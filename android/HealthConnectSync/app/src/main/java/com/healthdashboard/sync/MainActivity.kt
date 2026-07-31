package com.healthdashboard.sync

import android.content.Intent
import android.content.SharedPreferences
import android.net.Uri
import android.os.Bundle
import android.widget.Button
import android.widget.EditText
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import androidx.health.connect.client.PermissionController
import androidx.lifecycle.lifecycleScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.time.Instant
import java.time.temporal.ChronoUnit

class MainActivity : AppCompatActivity() {

    private lateinit var prefs: SharedPreferences
    private lateinit var healthConnectManager: HealthConnectManager

    private lateinit var serverUrlInput: EditText
    private lateinit var syncTokenInput: EditText
    private lateinit var statusText: TextView

    private val requestPermissions = registerForActivityResult(
        PermissionController.createRequestPermissionResultContract()
    ) { granted ->
        statusText.text = if (granted.containsAll(HealthConnectManager.PERMISSIONS)) {
            "Permissions granted. Ready to sync."
        } else {
            "Missing permissions: ${HealthConnectManager.PERMISSIONS - granted}"
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        prefs = getSharedPreferences("health_connect_sync", MODE_PRIVATE)
        healthConnectManager = HealthConnectManager(this)

        serverUrlInput = findViewById(R.id.serverUrlInput)
        syncTokenInput = findViewById(R.id.syncTokenInput)
        statusText = findViewById(R.id.statusText)

        serverUrlInput.setText(prefs.getString("server_url", ""))
        syncTokenInput.setText(prefs.getString("sync_token", ""))

        findViewById<Button>(R.id.grantPermissionsButton).setOnClickListener {
            requestPermissions.launch(HealthConnectManager.PERMISSIONS)
        }

        findViewById<Button>(R.id.syncButton).setOnClickListener {
            syncNow()
        }
    }

    private fun syncNow() {
        val serverUrl = serverUrlInput.text.toString().trimEnd('/')
        val syncToken = syncTokenInput.text.toString()
        prefs.edit().putString("server_url", serverUrl).putString("sync_token", syncToken).apply()

        if (serverUrl.isBlank()) {
            statusText.text = "Enter the dashboard's server URL first."
            return
        }

        if (healthConnectManager.client == null) {
            statusText.text = "Health Connect is not installed or unsupported on this device."
            startActivity(Intent(Intent.ACTION_VIEW, Uri.parse("market://details?id=com.google.android.apps.healthdata")))
            return
        }

        statusText.text = "Syncing..."
        lifecycleScope.launch {
            try {
                if (!healthConnectManager.hasAllPermissions()) {
                    statusText.text = "Grant Health Connect permissions first."
                    return@launch
                }

                val defaultSince = Instant.now().minus(30, ChronoUnit.DAYS)
                val since = Instant.ofEpochMilli(
                    prefs.getLong("last_sync_epoch_ms", defaultSince.toEpochMilli())
                )
                val payload = healthConnectManager.buildSyncPayload(since)
                val syncStartedAt = Instant.now()

                val result = withContext(Dispatchers.IO) {
                    SyncUploader.upload(serverUrl, syncToken, payload)
                }

                prefs.edit().putLong("last_sync_epoch_ms", syncStartedAt.toEpochMilli()).apply()
                statusText.text = "Synced: $result"
            } catch (e: Exception) {
                statusText.text = "Sync failed: ${e.message}"
            }
        }
    }
}
