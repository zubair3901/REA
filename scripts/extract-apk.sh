#!/usr/bin/env bash
set -euo pipefail
# Caller supplies an APK; never download a similarly named, unverified package.
source /workspace/rea-env/activate.sh
apk="$(realpath "${1:?Usage: extract-apk.sh /path/to/app.apk}")"
out="${2:-/workspace/REA/docs/apk-evidence}"
mkdir -p "$out"
sha256sum "$apk" > "$out/artifact.sha256"
rea doctor --provider jadx --json > "$out/jadx-readiness.json"
rea inspect-android-package "$apk" --json > "$out/package.json"
# Focused code queries require separate analyst selection after inspecting package.json.
