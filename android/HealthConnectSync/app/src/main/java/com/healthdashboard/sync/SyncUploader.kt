package com.healthdashboard.sync

import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject
import java.io.IOException
import java.util.concurrent.TimeUnit

object SyncUploader {

    private val JSON = "application/json; charset=utf-8".toMediaType()

    private val client = OkHttpClient.Builder()
        .connectTimeout(15, TimeUnit.SECONDS)
        .readTimeout(60, TimeUnit.SECONDS)
        .build()

    /** POSTs [payload] to {serverUrl}/ingest/health_connect, returns the response body. */
    fun upload(serverUrl: String, syncToken: String, payload: JSONObject): String {
        val body = payload.toString().toRequestBody(JSON)
        val requestBuilder = Request.Builder()
            .url("$serverUrl/ingest/health_connect")
            .post(body)
        if (syncToken.isNotBlank()) {
            requestBuilder.addHeader("X-Sync-Token", syncToken)
        }

        client.newCall(requestBuilder.build()).execute().use { response ->
            val responseBody = response.body?.string().orEmpty()
            if (!response.isSuccessful) {
                throw IOException("HTTP ${response.code}: $responseBody")
            }
            return responseBody
        }
    }
}
