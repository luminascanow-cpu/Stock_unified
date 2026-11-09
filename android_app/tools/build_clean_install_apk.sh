#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
APP_DIR="$ROOT_DIR/android_app/app"
SDK_DIR="${ANDROID_HOME:-$HOME/Library/Android/sdk}"
BUILD_TOOLS="$SDK_DIR/build-tools/36.0.0"
ANDROID_JAR="$SDK_DIR/platforms/android-35/android.jar"
OUT_DIR="$APP_DIR/build/outputs/apk/debug"
OUT_APK="$OUT_DIR/nse-matrix.apk"
WORK_DIR="$(mktemp -d /private/tmp/stock-unified-clean.XXXXXX)"

if [[ ! -x "$BUILD_TOOLS/aapt2" ]]; then
  echo "aapt2 not found at $BUILD_TOOLS/aapt2" >&2
  exit 1
fi

if [[ ! -f "$ANDROID_JAR" ]]; then
  echo "android.jar not found at $ANDROID_JAR" >&2
  exit 1
fi

mkdir -p "$WORK_DIR/src/com/stockunified/app" "$WORK_DIR/classes" "$WORK_DIR/dex" "$WORK_DIR/package/assets" "$OUT_DIR"

cat > "$WORK_DIR/AndroidManifest.xml" <<'MANIFEST'
<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="com.nsematrix.mobile">

    <uses-permission android:name="android.permission.INTERNET" />

    <application
        android:allowBackup="false"
        android:hardwareAccelerated="true"
        android:label="@string/app_name"
        android:supportsRtl="true"
        android:theme="@style/Theme.StockUnified">
        <activity
            android:name="com.stockunified.app.MainActivity"
            android:exported="true"
            android:screenOrientation="portrait">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
    </application>

</manifest>
MANIFEST

cat > "$WORK_DIR/src/com/stockunified/app/BuildConfig.java" <<'BUILDCONFIG'
package com.stockunified.app;

public final class BuildConfig {
  public static final boolean DEBUG = false;
  public static final String APPLICATION_ID = "com.nsematrix.mobile";
  public static final String BUILD_TYPE = "release";
  public static final int VERSION_CODE = 2026080203;
  public static final String VERSION_NAME = "0.1.3";
  public static final String START_URL = "file:///android_asset/index.html";
}
BUILDCONFIG

"$BUILD_TOOLS/aapt2" compile --dir "$APP_DIR/src/main/res" -o "$WORK_DIR/res.zip"
"$BUILD_TOOLS/aapt2" link \
  -I "$ANDROID_JAR" \
  --manifest "$WORK_DIR/AndroidManifest.xml" \
  --java "$WORK_DIR/gen" \
  --min-sdk-version 23 \
  --target-sdk-version 35 \
  --version-code 2026080203 \
  --version-name "0.1.3" \
  -o "$WORK_DIR/base.apk" \
  "$WORK_DIR/res.zip"

javac -source 17 -target 17 \
  -cp "$ANDROID_JAR" \
  -d "$WORK_DIR/classes" \
  "$APP_DIR/src/main/java/com/stockunified/app/MainActivity.java" \
  "$WORK_DIR/src/com/stockunified/app/BuildConfig.java"

"$BUILD_TOOLS/d8" \
  --min-api 23 \
  --lib "$ANDROID_JAR" \
  --output "$WORK_DIR/dex" \
  $(find "$WORK_DIR/classes" -name '*.class')

cp "$WORK_DIR/base.apk" "$WORK_DIR/app-unsigned.apk"
cp "$WORK_DIR/dex/classes.dex" "$WORK_DIR/package/classes.dex"
cp "$APP_DIR/src/main/assets/index.html" "$WORK_DIR/package/assets/index.html"
(cd "$WORK_DIR/package" && zip -q -X "$WORK_DIR/app-unsigned.apk" classes.dex assets/index.html)

"$BUILD_TOOLS/zipalign" -f -p 4 "$WORK_DIR/app-unsigned.apk" "$WORK_DIR/app-aligned.apk"
"$BUILD_TOOLS/apksigner" sign \
  --ks "$HOME/.android/debug.keystore" \
  --ks-pass pass:android \
  --key-pass pass:android \
  --out "$OUT_APK" \
  "$WORK_DIR/app-aligned.apk"

"$BUILD_TOOLS/apksigner" verify --verbose "$OUT_APK"
"$BUILD_TOOLS/aapt" dump badging "$OUT_APK" | head -n 8
ls -lh "$OUT_APK"
