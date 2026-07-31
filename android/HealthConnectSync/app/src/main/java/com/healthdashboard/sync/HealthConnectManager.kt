package com.healthdashboard.sync

import android.content.Context
import android.util.Log
import androidx.health.connect.client.HealthConnectClient
import androidx.health.connect.client.permission.HealthPermission
import androidx.health.connect.client.records.ActiveCaloriesBurnedRecord
import androidx.health.connect.client.records.DistanceRecord
import androidx.health.connect.client.records.HeartRateRecord
import androidx.health.connect.client.records.OxygenSaturationRecord
import androidx.health.connect.client.records.Record
import androidx.health.connect.client.records.SleepSessionRecord
import androidx.health.connect.client.records.StepsRecord
import androidx.health.connect.client.request.ReadRecordsRequest
import androidx.health.connect.client.time.TimeRangeFilter
import org.json.JSONArray
import org.json.JSONObject
import java.time.Duration
import java.time.Instant
import java.time.ZoneId
import java.time.format.DateTimeFormatter
import kotlin.reflect.KClass

/**
 * Reads Samsung Health data back out of Health Connect (the only way to pull
 * it programmatically — Samsung has no public cloud API for personal
 * accounts) and shapes it into the same column names the backend's Samsung
 * CSV bronze tables use, so etl.py can merge both sources unchanged.
 *
 * Note: Health Connect has no "stress" record type, so Samsung Health's
 * stress metric cannot be synced this way — it still requires the manual
 * CSV export path.
 */
class HealthConnectManager(private val context: Context) {

    val client: HealthConnectClient? by lazy {
        if (HealthConnectClient.getSdkStatus(context) == HealthConnectClient.SDK_AVAILABLE) {
            HealthConnectClient.getOrCreate(context)
        } else {
            null
        }
    }

    companion object {
        private const val TAG = "HealthConnectManager"

        val PERMISSIONS: Set<String> = setOf(
            HealthPermission.getReadPermission(StepsRecord::class),
            HealthPermission.getReadPermission(HeartRateRecord::class),
            HealthPermission.getReadPermission(SleepSessionRecord::class),
            HealthPermission.getReadPermission(OxygenSaturationRecord::class),
            HealthPermission.getReadPermission(ActiveCaloriesBurnedRecord::class),
            HealthPermission.getReadPermission(DistanceRecord::class),
        )
    }

    private val isoUtc = DateTimeFormatter.ISO_INSTANT

    suspend fun hasAllPermissions(): Boolean {
        val hc = client ?: return false
        val granted = hc.permissionController.getGrantedPermissions()
        return granted.containsAll(PERMISSIONS)
    }

    private suspend fun <T : Record> safeRead(
        hc: HealthConnectClient,
        type: KClass<T>,
        range: TimeRangeFilter,
    ): List<T> {
        return try {
            hc.readRecords(ReadRecordsRequest(type, range)).records
        } catch (e: Exception) {
            Log.w(TAG, "Could not read ${type.simpleName} (missing permission?): ${e.message}")
            emptyList()
        }
    }

    /** Builds the JSON body for POST /ingest/health_connect covering [since, now). */
    suspend fun buildSyncPayload(since: Instant): JSONObject {
        val hc = client ?: throw IllegalStateException("Health Connect is not available")
        val now = Instant.now()
        val range = TimeRangeFilter.between(since, now)
        val zone = ZoneId.systemDefault()

        val payload = JSONObject()
        payload.put("steps", buildStepsArray(hc, range, zone))
        payload.put("heart_rate", buildHeartRateArray(hc, range))
        payload.put("sleep", buildSleepArray(hc, range))
        payload.put("blood_oxygen", buildBloodOxygenArray(hc, range, zone))
        payload.put("calories", buildCaloriesArray(hc, range, zone))
        return payload
    }

    private suspend fun buildStepsArray(
        hc: HealthConnectClient,
        range: TimeRangeFilter,
        zone: ZoneId,
    ): JSONArray {
        val steps = safeRead(hc, StepsRecord::class, range)
        val distances = safeRead(hc, DistanceRecord::class, range)

        val stepsByDay = steps.groupBy { it.startTime.atZone(zone).toLocalDate() }
        val distanceByDay = distances
            .groupBy { it.startTime.atZone(zone).toLocalDate() }
            .mapValues { (_, records) -> records.sumOf { it.distance.inMeters } }

        val array = JSONArray()
        for ((day, records) in stepsByDay) {
            val row = JSONObject()
            row.put("start_time", isoUtc.format(day.atStartOfDay(zone).toInstant()))
            row.put("count", records.sumOf { it.count })
            distanceByDay[day]?.let { meters -> row.put("distance", meters / 1000.0) }
            array.put(row)
        }
        return array
    }

    private suspend fun buildHeartRateArray(hc: HealthConnectClient, range: TimeRangeFilter): JSONArray {
        val records = safeRead(hc, HeartRateRecord::class, range)
        val array = JSONArray()
        for (record in records) {
            for (sample in record.samples) {
                val row = JSONObject()
                row.put("start_time", isoUtc.format(sample.time))
                row.put("end_time", isoUtc.format(sample.time))
                row.put("heart_rate", sample.beatsPerMinute)
                array.put(row)
            }
        }
        return array
    }

    private suspend fun buildSleepArray(hc: HealthConnectClient, range: TimeRangeFilter): JSONArray {
        val sessions = safeRead(hc, SleepSessionRecord::class, range)
        val array = JSONArray()
        for (session in sessions) {
            val totalMin = Duration.between(session.startTime, session.endTime).toMinutes()
            var remMin = 0L
            var deepMin = 0L
            var lightMin = 0L
            var asleepMin = 0L

            for (stage in session.stages) {
                val stageMin = Duration.between(stage.startTime, stage.endTime).toMinutes()
                when (stage.stage) {
                    SleepSessionRecord.STAGE_TYPE_REM -> {
                        remMin += stageMin
                        asleepMin += stageMin
                    }
                    SleepSessionRecord.STAGE_TYPE_DEEP -> {
                        deepMin += stageMin
                        asleepMin += stageMin
                    }
                    SleepSessionRecord.STAGE_TYPE_LIGHT -> {
                        lightMin += stageMin
                        asleepMin += stageMin
                    }
                    SleepSessionRecord.STAGE_TYPE_SLEEPING -> asleepMin += stageMin
                    // AWAKE / OUT_OF_BED / UNKNOWN are not counted as sleep.
                }
            }

            val sleepMin = if (asleepMin > 0) asleepMin else totalMin
            val row = JSONObject()
            row.put("start_time", isoUtc.format(session.startTime))
            row.put("end_time", isoUtc.format(session.endTime))
            row.put("sleep_duration", sleepMin)
            row.put("rem_duration", remMin)
            row.put("deep_sleep_duration", deepMin)
            row.put("light_duration", lightMin)
            if (totalMin > 0) {
                row.put("efficiency", (sleepMin.toDouble() / totalMin.toDouble() * 100.0).toInt())
            }
            array.put(row)
        }
        return array
    }

    private suspend fun buildBloodOxygenArray(
        hc: HealthConnectClient,
        range: TimeRangeFilter,
        zone: ZoneId,
    ): JSONArray {
        val records = safeRead(hc, OxygenSaturationRecord::class, range)
        val byDay = records.groupBy { it.time.atZone(zone).toLocalDate() }
        val array = JSONArray()
        for ((day, dayRecords) in byDay) {
            val values = dayRecords.map { it.percentage.value }
            val row = JSONObject()
            row.put("start_time", isoUtc.format(day.atStartOfDay(zone).toInstant()))
            row.put("spo2", values.average())
            row.put("min_spo2", values.min())
            array.put(row)
        }
        return array
    }

    private suspend fun buildCaloriesArray(
        hc: HealthConnectClient,
        range: TimeRangeFilter,
        zone: ZoneId,
    ): JSONArray {
        val records = safeRead(hc, ActiveCaloriesBurnedRecord::class, range)
        val byDay = records.groupBy { it.startTime.atZone(zone).toLocalDate() }
        val array = JSONArray()
        for ((day, dayRecords) in byDay) {
            val row = JSONObject()
            row.put("start_time", isoUtc.format(day.atStartOfDay(zone).toInstant()))
            row.put("calorie", dayRecords.sumOf { it.energy.inKilocalories })
            array.put(row)
        }
        return array
    }
}
