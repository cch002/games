plugins {
    id("com.android.application")
}

android {
    namespace = "com.cch002.watchface.classicdial"
    compileSdk = 35

    defaultConfig {
        // Must differ from any app with code; WFF faces are resource-only packages.
        applicationId = "com.cch002.watchface.classicdial"
        // Watch Face Format v2 needs Wear OS 5 (API 34). Pixel Watch 3 ships with it.
        minSdk = 34
        targetSdk = 35
        versionCode = 1
        versionName = "1.0"
    }

    buildTypes {
        release {
            isMinifyEnabled = false
            // Signed with the debug key so `assembleRelease` is installable for personal use.
            // Replace with your own signing config before publishing to Play.
            signingConfig = signingConfigs.getByName("debug")
        }
    }
}
