"""
generate_mock_data.py
Generates realistic mock health data for the Personal Health AI Dashboard.
Run this script once before opening health_dashboard.ipynb.
"""

import os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

np.random.seed(42)

# Output directories
SAMSUNG_DIR = "data/samsung"
SUNDHED_DIR = "data/sundhed"
os.makedirs(SAMSUNG_DIR, exist_ok=True)
os.makedirs(SUNDHED_DIR, exist_ok=True)

# Date range: 5 years, 2020-01-01 to 2024-12-31
START = datetime(2020, 1, 1)
END = datetime(2024, 12, 31)
days = pd.date_range(start=START, end=END, freq="D")
n = len(days)

print(f"Generating {n} days of data ({START.date()} → {END.date()})...")


# ── Helpers ────────────────────────────────────────────────────────────────

def season_factor(dates, amplitude=0.15):
    """Sinusoidal seasonal variation peaking in summer."""
    day_of_year = np.array(dates.dayofyear, dtype=float)
    return 1 + amplitude * np.sin(2 * np.pi * (day_of_year - 80) / 365)


def trend(n, start=0, end=0):
    """Linear trend from start to end over n points."""
    return np.linspace(start, end, n)


# ── 1. Steps ───────────────────────────────────────────────────────────────

steps_base = 8000 + trend(n, -1500, 1500)  # gradual improvement
steps_season = season_factor(days) * steps_base
steps_noise = np.random.normal(0, 1200, n)
weekend_boost = np.where(np.array(days.dayofweek) >= 5, 500, 0)  # more on weekends

steps = np.clip(steps_season + steps_noise + weekend_boost, 500, 22000).astype(int)

df_steps = pd.DataFrame({
    "start_time": days.strftime("%Y-%m-%dT06:00:00.000+0100"),
    "end_time": days.strftime("%Y-%m-%dT23:59:00.000+0100"),
    "count": steps,
    "distance": (steps * 0.00075).round(2),  # km
    "calorie": (steps * 0.04).round(1),
    "speed": np.random.uniform(3.5, 5.5, n).round(2),
})
df_steps.to_csv(f"{SAMSUNG_DIR}/com.samsung.health.step_daily_trend.csv", index=False)
print(f"  ✓ Steps: {df_steps['count'].mean():.0f} avg steps/day")


# ── 2. Heart Rate ──────────────────────────────────────────────────────────

# Multiple readings per day (approx 6/day)
hr_dates = pd.date_range(start=START, end=END, freq="4H")
n_hr = len(hr_dates)

# Resting HR trend: slightly decreasing (fitness improvement)
resting_trend = 62 + trend(n_hr, 5, -5)
# Time-of-day variation (higher during day)
hour_factor = 1 + 0.08 * np.sin(2 * np.pi * (np.array(hr_dates.hour) - 6) / 24)
hr_values = resting_trend * hour_factor + np.random.normal(0, 4, n_hr)
hr_values = np.clip(hr_values, 45, 115).astype(int)

df_hr = pd.DataFrame({
    "start_time": hr_dates.strftime("%Y-%m-%dT%H:%M:%S.000+0100"),
    "end_time": (hr_dates + timedelta(minutes=5)).strftime("%Y-%m-%dT%H:%M:%S.000+0100"),
    "heart_rate": hr_values,
    "heart_beat_count": (hr_values * 5).astype(int),
})
df_hr.to_csv(f"{SAMSUNG_DIR}/com.samsung.health.heart_rate.csv", index=False)
print(f"  ✓ Heart rate: {df_hr['heart_rate'].mean():.0f} avg bpm")


# ── 3. Sleep ───────────────────────────────────────────────────────────────

# Sleep duration: 5.5–8.5 hours with some short nights
sleep_base = 7.0 + trend(n, -0.3, 0.3)
sleep_noise = np.random.normal(0, 0.7, n)
# Occasional very short nights (10% of days)
short_night = np.random.choice([0, -2], size=n, p=[0.9, 0.1])
sleep_hours = np.clip(sleep_base + sleep_noise + short_night, 3.5, 10.0)

# Sleep stages as fractions of total sleep
rem_frac = np.random.uniform(0.18, 0.25, n)
deep_frac = np.random.uniform(0.12, 0.22, n)
light_frac = 1 - rem_frac - deep_frac

# Bedtime around 23:00 ± 45 min
bedtime_offset = np.random.normal(0, 45, n).astype(int)  # minutes
bedtimes = days + pd.to_timedelta(23 * 60 + bedtime_offset, unit="m")
waketimes = bedtimes + pd.to_timedelta((sleep_hours * 60).astype(int), unit="m")

df_sleep = pd.DataFrame({
    "start_time": bedtimes.strftime("%Y-%m-%dT%H:%M:%S.000+0100"),
    "end_time": waketimes.strftime("%Y-%m-%dT%H:%M:%S.000+0100"),
    "duration": (sleep_hours * 60).astype(int),  # minutes
    "sleep_duration": (sleep_hours * 60).astype(int),
    "rem_duration": (sleep_hours * 60 * rem_frac).astype(int),
    "deep_sleep_duration": (sleep_hours * 60 * deep_frac).astype(int),
    "light_duration": (sleep_hours * 60 * light_frac).astype(int),
    "efficiency": np.clip(85 + np.random.normal(0, 5, n), 65, 98).astype(int),
})
df_sleep.to_csv(f"{SAMSUNG_DIR}/com.samsung.health.sleep.csv", index=False)
print(f"  ✓ Sleep: {sleep_hours.mean():.1f} avg hours/night")


# ── 4. Blood Oxygen (SpO2) ─────────────────────────────────────────────────

# Nightly readings
spo2_base = 97.5 + trend(n, -0.5, 0.5)
spo2_noise = np.random.normal(0, 0.8, n)
# Occasional dips (5% of nights)
dip = np.random.choice([0, -3.5], size=n, p=[0.95, 0.05])
spo2 = np.clip(spo2_base + spo2_noise + dip, 88, 100).round(1)

df_spo2 = pd.DataFrame({
    "start_time": days.strftime("%Y-%m-%dT02:00:00.000+0100"),
    "end_time": days.strftime("%Y-%m-%dT06:00:00.000+0100"),
    "spo2": spo2,
    "min_spo2": np.clip(spo2 - np.random.uniform(0.5, 3, n), 85, 100).round(1),
})
df_spo2.to_csv(f"{SAMSUNG_DIR}/com.samsung.health.blood_oxygen.csv", index=False)
print(f"  ✓ SpO2: {spo2.mean():.1f}% avg")


# ── 5. Stress ──────────────────────────────────────────────────────────────

# Stress readings 4x per day
stress_dates = pd.date_range(start=START, end=END, freq="6H")
n_st = len(stress_dates)

stress_base = 35 + trend(n_st, 10, -5)  # improving over time
stress_season = 1 + 0.1 * np.sin(2 * np.pi * (np.array(stress_dates.dayofyear, dtype=float) - 30) / 365)
# Workday effect (Mon–Fri higher)
workday = np.where(np.array(stress_dates.dayofweek) < 5, 8, -8)
stress = np.clip(stress_base * stress_season + workday + np.random.normal(0, 10, n_st), 0, 100).astype(int)

df_stress = pd.DataFrame({
    "start_time": stress_dates.strftime("%Y-%m-%dT%H:%M:%S.000+0100"),
    "end_time": (stress_dates + timedelta(minutes=30)).strftime("%Y-%m-%dT%H:%M:%S.000+0100"),
    "stress_level": stress,
    "score": stress,
})
df_stress.to_csv(f"{SAMSUNG_DIR}/com.samsung.health.stress.csv", index=False)
print(f"  ✓ Stress: {stress.mean():.0f} avg level")


# ── 6. Calories Burned ─────────────────────────────────────────────────────

cal_base = 2400 + trend(n, -200, 200)
cal_season = season_factor(days, 0.1) * cal_base
calories = np.clip(cal_season + np.random.normal(0, 200, n), 1600, 4200).astype(int)

df_cal = pd.DataFrame({
    "start_time": days.strftime("%Y-%m-%dT00:00:00.000+0100"),
    "end_time": days.strftime("%Y-%m-%dT23:59:00.000+0100"),
    "calorie": calories,
    "active_time": np.random.randint(30, 120, n),
})
df_cal.to_csv(f"{SAMSUNG_DIR}/com.samsung.health.calories_burned.csv", index=False)
print(f"  ✓ Calories: {calories.mean():.0f} avg kcal/day")


# ── 7. Lab Results (sundhed.dk) ────────────────────────────────────────────

lab_dates = pd.date_range(start="2020-03-01", end="2024-11-01", freq="6M")

# Reference ranges (Danish standard)
lab_data = []
for d in lab_dates:
    t = (d - pd.Timestamp("2020-01-01")).days / 365  # years elapsed
    lab_data.append({
        "date": d.strftime("%Y-%m-%d"),
        "test": "Kolesterol total (mmol/L)",
        "value": round(np.clip(5.8 - 0.15 * t + np.random.normal(0, 0.3), 3.5, 7.5), 1),
        "reference_low": 0,
        "reference_high": 5.0,
        "unit": "mmol/L",
    })
    lab_data.append({
        "date": d.strftime("%Y-%m-%d"),
        "test": "LDL-kolesterol (mmol/L)",
        "value": round(np.clip(3.8 - 0.12 * t + np.random.normal(0, 0.25), 1.5, 5.5), 1),
        "reference_low": 0,
        "reference_high": 3.0,
        "unit": "mmol/L",
    })
    lab_data.append({
        "date": d.strftime("%Y-%m-%d"),
        "test": "HDL-kolesterol (mmol/L)",
        "value": round(np.clip(1.2 + 0.05 * t + np.random.normal(0, 0.1), 0.9, 2.5), 2),
        "reference_low": 1.0,
        "reference_high": 99,
        "unit": "mmol/L",
    })
    lab_data.append({
        "date": d.strftime("%Y-%m-%d"),
        "test": "Fastende glukose (mmol/L)",
        "value": round(np.clip(5.6 + np.random.normal(0, 0.4), 3.5, 7.0), 1),
        "reference_low": 3.9,
        "reference_high": 6.1,
        "unit": "mmol/L",
    })
    lab_data.append({
        "date": d.strftime("%Y-%m-%d"),
        "test": "Hæmoglobin (mmol/L)",
        "value": round(np.clip(8.9 + np.random.normal(0, 0.3), 7.5, 10.5), 1),
        "reference_low": 8.3,
        "reference_high": 10.5,
        "unit": "mmol/L",
    })
    lab_data.append({
        "date": d.strftime("%Y-%m-%d"),
        "test": "HbA1c (%)",
        "value": round(np.clip(5.4 + np.random.normal(0, 0.2), 4.5, 6.5), 1),
        "reference_low": 0,
        "reference_high": 5.7,
        "unit": "%",
    })
    lab_data.append({
        "date": d.strftime("%Y-%m-%d"),
        "test": "TSH (mIU/L)",
        "value": round(np.clip(2.1 + np.random.normal(0, 0.5), 0.4, 4.0), 2),
        "reference_low": 0.4,
        "reference_high": 4.0,
        "unit": "mIU/L",
    })
    lab_data.append({
        "date": d.strftime("%Y-%m-%d"),
        "test": "Triglycerid (mmol/L)",
        "value": round(np.clip(1.6 - 0.05 * t + np.random.normal(0, 0.3), 0.5, 3.5), 1),
        "reference_low": 0,
        "reference_high": 1.7,
        "unit": "mmol/L",
    })
    lab_data.append({
        "date": d.strftime("%Y-%m-%d"),
        "test": "Kreatinin (µmol/L)",
        "value": round(np.clip(82 + np.random.normal(0, 6), 60, 110), 0),
        "reference_low": 60,
        "reference_high": 105,
        "unit": "µmol/L",
    })
    lab_data.append({
        "date": d.strftime("%Y-%m-%d"),
        "test": "Vitamin D (nmol/L)",
        "value": round(np.clip(55 + 8 * t + np.random.normal(0, 10), 20, 120), 0),
        "reference_low": 50,
        "reference_high": 125,
        "unit": "nmol/L",
    })

df_lab = pd.DataFrame(lab_data)
df_lab.to_csv(f"{SUNDHED_DIR}/lab_results.csv", index=False)
print(f"  ✓ Lab results: {len(df_lab)} entries ({len(lab_dates)} dates × 10 tests)")


# ── 8. Diagnoses ───────────────────────────────────────────────────────────

diagnoses = """# Diagnoser og journalnotater (mock)

## Aktive diagnoser
- **J30.1** Allergisk rhinitis (høfeber) — diagnosticeret 2018-04-12
- **M54.5** Lænderygsmerter — diagnosticeret 2021-06-03, periodevis
- **E78.0** Hyperkolesterolæmi — diagnosticeret 2020-09-15, under observation

## Tidligere diagnoser (afsluttede)
- **J06.9** Akut øvre luftvejsinfektion — 2022-01-18, behandlet og afsluttet
- **S93.4** Forstuvning af ankel — 2023-07-22, rehabiliteret

## Journalnoter
### 2024-11-05 — Almen praksis
Patient møder til kontrol. Generelt velbefindende. BT: 128/82 mmHg.
Kolesterol fortsat let forhøjet, diætvejledning gentaget. Anbefalet
motion ≥150 min/uge. Opfølgning om 6 måneder.

### 2023-09-12 — Almen praksis
Symptomer på sæsonallergi. Cetirizin 10mg ordineret.
Ryg OK siden fysioterapi i foråret. Blodprøver taget — se lab.

### 2022-03-08 — Almen praksis
Rutinemæssig kontrol. Blodtryk normalt. Vægt stabil.
Anbefalet fortsat regelmæssig motion. Vitamintilskud D-vitamin
anbefalet i vintermånederne.

### 2021-06-03 — Almen praksis
Smerter i lænde, sandsynligvis muskulære. Henvist til fysioterapi.
NSAID ved behov. Opfølgning om 4 uger.
"""

with open(f"{SUNDHED_DIR}/diagnoses.txt", "w", encoding="utf-8") as f:
    f.write(diagnoses)
print("  ✓ Diagnoses: written")


# ── 9. Vaccinations ────────────────────────────────────────────────────────

vaccinations = [
    {"date": "2020-10-05", "vaccine": "Influenza", "product": "Vaxigrip Tetra", "lot": "A2B3C4", "location": "Almen praksis"},
    {"date": "2021-04-08", "vaccine": "COVID-19 (1. dosis)", "product": "Comirnaty (Pfizer)", "lot": "EL3248", "location": "Vaccinationscenter"},
    {"date": "2021-04-29", "vaccine": "COVID-19 (2. dosis)", "product": "Comirnaty (Pfizer)", "lot": "EL9261", "location": "Vaccinationscenter"},
    {"date": "2021-10-04", "vaccine": "Influenza", "product": "Vaxigrip Tetra", "lot": "B3C4D5", "location": "Apotek"},
    {"date": "2021-11-15", "vaccine": "COVID-19 (booster)", "product": "Comirnaty (Pfizer)", "lot": "FK1234", "location": "Vaccinationscenter"},
    {"date": "2022-10-10", "vaccine": "Influenza + COVID-19 (combo)", "product": "Vaxigrip / Comirnaty Bivalent", "lot": "GH5678", "location": "Almen praksis"},
    {"date": "2023-09-25", "vaccine": "Influenza", "product": "Influvac Tetra", "lot": "IJ9012", "location": "Apotek"},
    {"date": "2024-09-30", "vaccine": "Influenza", "product": "Vaxigrip Tetra", "lot": "KL3456", "location": "Apotek"},
]

df_vac = pd.DataFrame(vaccinations)
df_vac.to_csv(f"{SUNDHED_DIR}/vaccinations.csv", index=False)
print(f"  ✓ Vaccinations: {len(df_vac)} records")


print("\nAll mock data generated successfully!")
print(f"  Samsung Health → {SAMSUNG_DIR}/")
print(f"  Sundhed.dk     → {SUNDHED_DIR}/")
print("\nNext step: open health_dashboard.ipynb in Jupyter")
