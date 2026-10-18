import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from publish_feed import build_manifest


class PublishFeedTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.apk = Path(self.directory.name) / "app.apk"
        self.apk.write_bytes(b"test APK payload")
        self.asset = {"browser_download_url": "https://github.com/repsreps/repsreps/releases/download/v2.1/repsreps-release.apk"}

    def build(self, package="com.repsreps.app", channel="release"):
        with patch("publish_feed.subprocess.run") as verify, patch(
            "publish_feed.subprocess.check_output",
            return_value=f"package: name='{package}' versionCode='2' versionName='2.1'\n",
        ):
            result = build_manifest({"body": "Fixed bugs"}, self.asset, self.apk, channel, Path("tools"))
            verify.assert_called_once()
            return result

    def test_derives_metadata_and_digest_from_apk(self):
        import hashlib
        result = self.build()
        self.assertEqual(2, result["release"]["versionCode"])
        self.assertEqual(self.apk.stat().st_size, result["release"]["size"])
        self.assertEqual(hashlib.sha256(self.apk.read_bytes()).hexdigest(), result["release"]["sha256"])

    def test_rejects_wrong_package(self):
        with self.assertRaises(ValueError):
            self.build(package="com.repsreps.app.debug")

    def test_supports_separate_debug_channel(self):
        self.assertEqual("com.repsreps.app.debug", self.build(package="com.repsreps.app.debug", channel="debug")["packageName"])

    def test_rejects_other_release_repository(self):
        self.asset["browser_download_url"] = "https://github.com/other/repo/releases/download/v2/app.apk"
        with self.assertRaises(ValueError):
            self.build()

    def test_rejects_unsigned_apk(self):
        import subprocess
        with patch("publish_feed.subprocess.run", side_effect=subprocess.CalledProcessError(1, "apksigner")):
            with self.assertRaises(subprocess.CalledProcessError):
                build_manifest({}, self.asset, self.apk, "release", Path("tools"))


if __name__ == "__main__":
    unittest.main()
