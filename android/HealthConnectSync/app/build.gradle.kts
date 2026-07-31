plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

android {
    namespace = "com.healthdashboard.sync"
    compileSdk = 34

    defaultConfig {
        applicationId = "com.healthdashboard.sync"
        // Health Connect's client library requires API 26+ (java.time is
        // available natively at that level, no desugaring needed).
        minSdk = 26
        targetSdk = 34
        versionCode = 1
        versionName = "1.0"
    }

    buildTypes {
        release {
            isMinifyEnabled = false
            proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"), "proguard-rules.pro")
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_1_8
        targetCompatibility = JavaVersion.VERSION_1_8
    }

    kotlinOptions {
        jvmTarget = "1.8"
    }
}

dependencies {
    implementation("androidx.core:core-ktx:1.13.1")
    implementation("androidx.appcompat:appcompat:1.7.0")
    implementation("androidx.activity:activity-ktx:1.9.0")
    implementation("androidx.lifecycle:lifecycle-runtime-ktx:2.8.0")
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.8.1")

    // Check https://developer.android.com/health-and-fitness/guides/health-connect/setup
    // for the latest version — this API is still pre-1.0 stable and moves fast.
    implementation("androidx.health.connect:connect-client:1.1.0-alpha07")

    implementation("com.squareup.okhttp3:okhttp:4.12.0")
}
