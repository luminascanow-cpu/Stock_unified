plugins {
    id("com.android.application")
}

android {
    namespace = "com.stockunified.app"
    compileSdk = 36

    defaultConfig {
        applicationId = "com.stockunified.app"
        minSdk = 23
        targetSdk = 36
        versionCode = 4
        versionName = "0.3.1"

        buildConfigField("String", "START_URL", "\"file:///android_asset/index.html\"")
    }

    buildFeatures {
        buildConfig = true
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
}
