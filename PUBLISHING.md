# RepsReps downloads

This is the public APK distribution site for RepsReps. Application source and Firebase configuration do not belong in this repository.

## Initial setup

Copy the contents of the app repository's `distribution/` directory into the root of `repsreps/repsreps`, including `.github` and `.nojekyll`. In repository Settings → Pages, change Source to **GitHub Actions**. The supplied workflow explicitly deploys Pages; it does not rely on a bot commit triggering a branch-based Pages build.

Run **Actions → Publish RepsReps updates → Run workflow** with an empty tag to deploy the initial site. The empty feeds correctly mean no signed update has been published yet.

## Publish an update

1. Increase `versionCode` and set `versionName` in the Android app's Gradle configuration.
2. Build a signed APK using the same signing key as the previously distributed app. Keep signing material and passwords out of GitHub. An unsigned release APK is not distributable.
3. Create a **draft** GitHub release with a new tag and release notes.
4. Attach the signed APK as **repsreps-release.apk**. Optionally attach **repsreps-debug.apk** for the separate debug channel. Keep debug APKs signed with the same debug certificate across versions; regenerating a debug keystore prevents updates to existing debug installations.
5. Publish the release as a regular release, not a prerelease. All desired assets must be attached before publishing.
6. The workflow checks APK signatures, reads actual package/version fields, computes SHA-256 and size, commits update feeds, and deploys Pages. A mismatched package, unsigned APK or non-increasing version fails the workflow.
7. Verify the Actions run succeeds. RepsReps checks on resume at most once an hour; Settings → Check for updates bypasses this interval. A new version gets one automatic prompt; Later leaves the banner available. If you need to rerun publishing, use Run workflow with the release tag.

Never replace an existing APK asset with different bytes under the same version code. Publish a new version instead. The app verifies package, exact version, size, SHA-256 and matching signer before opening Android's installer.

Feeds:
- https://repsreps.github.io/repsreps/updates/release.json
- https://repsreps.github.io/repsreps/updates/debug.json

APKs are public and require no GitHub account to download. The update banner is inside the app; this setup does not send push notifications while it is closed.
