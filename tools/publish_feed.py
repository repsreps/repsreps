"""Generate update manifests from signed GitHub release assets, never guessed version fields."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
from urllib.parse import urlparse


def build_manifest(release, asset, apk, channel, build_tools):
    expected = "com.repsreps.app" + (".debug" if channel == "debug" else "")
    url = asset["browser_download_url"]
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.netloc != "github.com" or not parsed.path.startswith(
        "/repsreps/repsreps/releases/download/"
    ) or not parsed.path.endswith(".apk"):
        raise ValueError("Unexpected APK URL")
    size = apk.stat().st_size
    if not 0 < size <= 200 * 1024 * 1024:
        raise ValueError("APK must be between 1 byte and 200 MB")
    suffix = ".exe" if os.name == "nt" else ""
    signer = "apksigner.bat" if os.name == "nt" else "apksigner"
    subprocess.run([str(build_tools / signer), "verify", str(apk)], check=True, capture_output=True)
    badging = subprocess.check_output([str(build_tools / ("aapt" + suffix)), "dump", "badging", str(apk)], text=True)
    match = re.search(r"^package: name='([^']+)' versionCode='(\d+)' versionName='([^']*)'", badging, re.MULTILINE)
    if not match or match[1] != expected:
        raise ValueError("APK package does not match channel")
    if not 0 < int(match[2]) <= 2147483647 or not 0 < len(match[3]) <= 80:
        raise ValueError("Invalid APK version")
    with apk.open("rb") as stream:
        checksum = hashlib.file_digest(stream, "sha256").hexdigest()
    return {
        "schemaVersion": 1, "packageName": expected, "channel": channel,
        "release": {
            "versionCode": int(match[2]), "versionName": match[3], "url": url,
            "size": size, "sha256": checksum,
            "notes": (release.get("body") or "")[:2000],
        },
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--release", type=Path, required=True)
    parser.add_argument("--downloads", type=Path, required=True)
    parser.add_argument("--build-tools", type=Path, required=True)
    args = parser.parse_args()
    release = json.loads(args.release.read_text(encoding="utf-8"))
    if release.get("draft") or release.get("prerelease"):
        raise ValueError("Publish a regular release; draft and prerelease assets are not advertised")
    staged = []
    for channel in ("release", "debug"):
        name = f"repsreps-{channel}.apk"
        assets = [asset for asset in release.get("assets", []) if asset["name"] == name]
        if not assets:
            continue
        manifest = build_manifest(release, assets[0], args.downloads / name, channel, args.build_tools)
        destination = Path("updates") / f"{channel}.json"
        previous = json.loads(destination.read_text(encoding="utf-8")).get("release") if destination.exists() else None
        current = manifest["release"]
        if previous and current["versionCode"] <= previous["versionCode"]:
            if current == previous:
                continue
            raise ValueError(f"{channel}: increase versionCode for every new APK")
        staged.append((destination, manifest))
    if not any(asset["name"] in ("repsreps-release.apk", "repsreps-debug.apk") for asset in release.get("assets", [])):
        raise ValueError("Attach repsreps-release.apk (and optionally repsreps-debug.apk) before publishing")
    for destination, manifest in staged:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
