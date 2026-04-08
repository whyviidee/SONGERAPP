#!/bin/bash
# SONGER Release Script — one command to bump, build, sign, notarize & publish
# Usage: ./release.sh [patch|minor|major]    (default: patch)
set -e

cd "$(dirname "$0")"
BUMP="${1:-patch}"
REPO="whyviidee/SONGERAPP"
SIGN_ID="Developer ID Application: Yuri Dagot (4S8T6F279K)"
ENTITLEMENTS="$(pwd)/entitlements.plist"
KEYCHAIN_PROFILE="SONGER"
BUILD_DIR="/tmp/songer_build_$$"
PYTHON_ARM_VENV="$(pwd)/.venv-arm64/bin/python3.13"
PYTHON_X86_VENV="/Library/Frameworks/Python.framework/Versions/3.11/bin/python3.11"

# ── 1. Read current version ──
CURRENT=$(cat VERSION | tr -d '[:space:]')
IFS='.' read -r MAJOR MINOR PATCH <<< "$CURRENT"

case "$BUMP" in
  major) MAJOR=$((MAJOR + 1)); MINOR=0; PATCH=0 ;;
  minor) MINOR=$((MINOR + 1)); PATCH=0 ;;
  patch) PATCH=$((PATCH + 1)) ;;
  *) echo "Usage: ./release.sh [patch|minor|major]"; exit 1 ;;
esac

NEW_VERSION="$MAJOR.$MINOR.$PATCH"
echo ""
echo "=== SONGER Release ==="
echo "  $CURRENT -> $NEW_VERSION ($BUMP)"
echo ""
if [[ "${AUTO_YES:-}" == "1" ]]; then
  echo "Auto-confirming (AUTO_YES=1)"
else
  read -p "Continue? [y/N] " -n 1 -r
  echo ""
  [[ ! $REPLY =~ ^[Yy]$ ]] && echo "Cancelled." && exit 0
fi

# ── 2. Write new version everywhere ──
echo "$NEW_VERSION" > VERSION
if [ -f landing/index.html ]; then
  sed -i '' "s/SONGER v[0-9]*\.[0-9]*\.[0-9]*/SONGER v${NEW_VERSION}/g" landing/index.html
  sed -i '' "s/v[0-9]*\.[0-9]*\.[0-9]* out now/v${NEW_VERSION} out now/g" landing/index.html
fi
echo "-> VERSION updated to $NEW_VERSION"

# ── 3. Build frontend ──
echo "-> Building frontend..."
cd frontend && npm run build && cd ..

# ── helper: sign + notarize + staple a .app ──────────────────────────────────
_sign_and_notarize() {
  local APP_PATH="$1"
  local ZIP_PATH="$2"

  find "$APP_PATH" -name "._*" -delete 2>/dev/null || true
  find "$APP_PATH" -name ".DS_Store" -delete 2>/dev/null || true

  # Sign .so and .dylib explicitly first (some are missed by Mach-O grep)
  echo "   Signing .so and .dylib files..."
  find "$APP_PATH" \( -name "*.so" -o -name "*.dylib" \) -type f | while read -r lib; do
    codesign --force --options runtime --timestamp --sign "$SIGN_ID" "$lib" 2>/dev/null || \
    echo "   WARN: failed to sign $lib"
  done

  echo "   Signing all Mach-O binaries..."
  local SIGNED=0
  while IFS= read -r bin; do
    [[ "$bin" == "$APP_PATH/Contents/MacOS/SONGER" ]] && continue
    codesign --force --options runtime --timestamp \
      --sign "$SIGN_ID" "$bin" 2>/dev/null && SIGNED=$((SIGNED + 1)) || true
  done < <(find "$APP_PATH" -type f -exec sh -c 'file "$1" | grep -q "Mach-O"' _ {} \; -print 2>/dev/null)
  echo "   Signed $SIGNED inner binaries"

  codesign --force --options runtime --timestamp \
    --entitlements "$ENTITLEMENTS" \
    --sign "$SIGN_ID" "$APP_PATH/Contents/MacOS/SONGER"

  codesign --force --options runtime --timestamp \
    --entitlements "$ENTITLEMENTS" \
    --sign "$SIGN_ID" "$APP_PATH"

  codesign --verify --deep --strict "$APP_PATH"
  echo "   Signature OK"

  echo "   Notarizing..."
  ditto -c -k --keepParent "$APP_PATH" "$ZIP_PATH"
  xcrun notarytool submit "$ZIP_PATH" --keychain-profile "$KEYCHAIN_PROFILE" --wait

  echo "   Stapling..."
  xcrun stapler staple "$APP_PATH"
  echo "   Notarization complete!"
}

# ── 4. Build arm64 ────────────────────────────────────────────────────────────
echo ""
echo "-> [1/2] Building macOS app (arm64)..."
BUILD_ARM="$BUILD_DIR/arm64"
rm -rf "$BUILD_ARM"
"$PYTHON_ARM_VENV" -m PyInstaller songer_mac.spec --clean --noconfirm \
  --distpath "$BUILD_ARM/dist" --workpath "$BUILD_ARM/work" 2>&1 | tail -3

APP_ARM="$BUILD_ARM/dist/SONGER.app"
echo "-> Signing & notarizing arm64..."
_sign_and_notarize "$APP_ARM" "$BUILD_ARM/SONGER-notarize.zip"

DMG_ARM="dist/SONGER-${NEW_VERSION}-arm64.dmg"
mkdir -p dist
rm -f "$DMG_ARM"
hdiutil create -volname "SONGER" -srcfolder "$APP_ARM" -ov -format UDZO "$DMG_ARM"
codesign --force --timestamp --sign "$SIGN_ID" "$DMG_ARM"
echo "-> arm64 DMG: $DMG_ARM ($(du -h "$DMG_ARM" | cut -f1))"

spctl --assess --type execute -vv "$APP_ARM" 2>&1 || true

# ── 5. Build x86_64 ───────────────────────────────────────────────────────────
echo ""
echo "-> [2/2] Building macOS app (x86_64 / Intel)..."
BUILD_X86="$BUILD_DIR/x86_64"
rm -rf "$BUILD_X86"
arch -x86_64 "$PYTHON_X86_VENV" -m PyInstaller songer_mac_x86.spec --clean --noconfirm \
  --distpath "$BUILD_X86/dist" --workpath "$BUILD_X86/work" 2>&1 | tail -3

APP_X86="$BUILD_X86/dist/SONGER.app"
echo "-> Signing & notarizing x86_64..."
_sign_and_notarize "$APP_X86" "$BUILD_X86/SONGER-notarize.zip"

DMG_X86="dist/SONGER-${NEW_VERSION}-x86_64.dmg"
rm -f "$DMG_X86"
hdiutil create -volname "SONGER" -srcfolder "$APP_X86" -ov -format UDZO "$DMG_X86"
codesign --force --timestamp --sign "$SIGN_ID" "$DMG_X86"
echo "-> x86_64 DMG: $DMG_X86 ($(du -h "$DMG_X86" | cut -f1))"

spctl --assess --type execute -vv "$APP_X86" 2>&1 || true

# ── 6. Git commit & tag ───────────────────────────────────────────────────────
echo "-> Git commit & tag..."
cd "$(git rev-parse --show-toplevel 2>/dev/null || echo .)"
git add VERSION
git commit -m "release: SONGER v${NEW_VERSION}" 2>/dev/null || true
git tag -a "v${NEW_VERSION}" -m "SONGER v${NEW_VERSION}" 2>/dev/null || true
git push origin HEAD --tags 2>/dev/null || true
cd "$(dirname "$0")"

# ── 7. GitHub Release ─────────────────────────────────────────────────────────
echo "-> Publishing GitHub Release v${NEW_VERSION}..."
FIXED_ARM="dist/SONGER-arm64.dmg"
FIXED_X86="dist/SONGER-x86_64.dmg"
cp "$DMG_ARM" "$FIXED_ARM"
cp "$DMG_X86" "$FIXED_X86"

gh release create "v${NEW_VERSION}" \
  "$DMG_ARM" "$DMG_X86" "$FIXED_ARM" "$FIXED_X86" \
  --repo "$REPO" \
  --title "SONGER v${NEW_VERSION}" \
  --notes "SONGER v${NEW_VERSION}" \
  --latest

# ── 8. Update Vercel landing ──────────────────────────────────────────────────
echo "-> Updating DMGs on songerapp.me..."
cp "$DMG_ARM" landing/SONGER-arm64.dmg
cp "$DMG_X86" landing/SONGER-x86_64.dmg
cd landing && vercel --prod --yes 2>&1 | grep -E "Aliased|Error" && cd ..
rm landing/SONGER-arm64.dmg landing/SONGER-x86_64.dmg

# Cleanup
rm -rf "$BUILD_DIR"

echo ""
echo "=== Done! ==="
echo "  Version:     $NEW_VERSION"
echo "  arm64 DMG:   $DMG_ARM"
echo "  x86_64 DMG:  $DMG_X86"
echo "  Signed:      YES"
echo "  Notarized:   YES"
echo "  Release:     https://github.com/$REPO/releases/tag/v${NEW_VERSION}"
echo ""
