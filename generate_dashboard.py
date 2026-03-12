"""
Samsung Health Dashboard Generator
Læser rå Samsung Health CSV-data og genererer en standalone HTML-fil.
"""

import os, glob, json
import pandas as pd
import numpy as np
from datetime import datetime

SAMSUNG_DIR = r'C:/Users/Bruger/Desktop/Sasung health data'
SUNDHED_DIR = os.path.join(os.path.dirname(__file__), 'data', 'sundhed')
SCRAPER_DIR = os.path.join(os.path.dirname(__file__), '..', 'health-scraper', 'output', 'parsed')
OUTPUT      = os.path.join(os.path.dirname(__file__), f'dashboard_{datetime.now().strftime("%Y%m%d")}.html')

# ── Hjælpefunktioner ──────────────────────────────────────────────────────

def load_shealth(pattern):
    files = glob.glob(os.path.join(SAMSUNG_DIR, pattern))
    if not files:
        return pd.DataFrame()
    dfs = []
    for f in files:
        try:
            df = pd.read_csv(f, skiprows=1, index_col=False, low_memory=False)
            dfs.append(df)
        except:
            pass
    return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()

def to_json(df, date_col, val_col, label=None):
    """Konverter til [{x: dato, y: værdi}] JSON — kun fra faktiske datapunkter."""
    if df.empty or val_col not in df.columns:
        return []
    sub = df[[date_col, val_col]].dropna()
    sub[date_col] = pd.to_datetime(sub[date_col], errors='coerce')
    sub = sub.dropna().sort_values(date_col)
    return [{'x': row[date_col].strftime('%Y-%m-%d'), 'y': round(float(row[val_col]), 1)}
            for _, row in sub.iterrows()]

def rolling_avg(data, window=7):
    """Beregn glidende gennemsnit på [{x,y}] liste."""
    if len(data) < 2:
        return []
    vals = [d['y'] for d in data]
    result = []
    for i, d in enumerate(data):
        start = max(0, i - window + 1)
        avg = round(sum(vals[start:i+1]) / (i - start + 1), 1)
        result.append({'x': d['x'], 'y': avg})
    return result

# ── Indlæs data ───────────────────────────────────────────────────────────
print('Indlæser Samsung Health data...')

# Skridt
raw_steps = load_shealth('com.samsung.shealth.tracker.pedometer_step_count*.csv')
steps_daily = pd.DataFrame()
if not raw_steps.empty:
    raw_steps['_dt'] = pd.to_datetime(raw_steps['com.samsung.health.step_count.start_time'], errors='coerce')
    raw_steps['date'] = raw_steps['_dt'].dt.date
    raw_steps['count'] = pd.to_numeric(raw_steps['com.samsung.health.step_count.count'], errors='coerce')
    steps_daily = raw_steps.dropna(subset=['date','count']).groupby('date')['count'].sum().reset_index()
    steps_daily['date'] = pd.to_datetime(steps_daily['date'])
    print(f'  Skridt: {len(steps_daily)} dage, gns {steps_daily["count"].mean():,.0f}')

# Puls
raw_hr = load_shealth('com.samsung.shealth.tracker.heart_rate*.csv')
hr_daily = pd.DataFrame()
if not raw_hr.empty:
    raw_hr['_dt'] = pd.to_datetime(raw_hr['com.samsung.health.heart_rate.start_time'], errors='coerce')
    raw_hr['date'] = raw_hr['_dt'].dt.date
    raw_hr['hr'] = pd.to_numeric(raw_hr['com.samsung.health.heart_rate.heart_rate'], errors='coerce')
    hr_daily = raw_hr.dropna(subset=['date','hr']).groupby('date')['hr'].mean().reset_index()
    hr_daily['date'] = pd.to_datetime(hr_daily['date'])
    hr_daily['hr'] = hr_daily['hr'].round(1)
    print(f'  Puls: {len(hr_daily)} dage, gns {hr_daily["hr"].mean():.0f} bpm')

# Søvn
raw_sleep = load_shealth('com.samsung.shealth.sleep*.csv')
sleep_daily = pd.DataFrame()
if not raw_sleep.empty:
    raw_sleep['_dt'] = pd.to_datetime(raw_sleep['com.samsung.health.sleep.start_time'], errors='coerce')
    raw_sleep['date'] = raw_sleep['_dt'].dt.date
    raw_sleep['duration_h'] = pd.to_numeric(raw_sleep.get('sleep_duration', pd.Series(dtype=float)), errors='coerce') / 60
    raw_sleep['rem_h']   = pd.to_numeric(raw_sleep.get('total_rem_duration',   pd.Series(dtype=float)), errors='coerce') / 60
    raw_sleep['light_h'] = pd.to_numeric(raw_sleep.get('total_light_duration', pd.Series(dtype=float)), errors='coerce') / 60
    sleep_daily = raw_sleep[raw_sleep['duration_h'] > 1].dropna(subset=['date','duration_h'])
    sleep_daily['deep_h'] = (sleep_daily['duration_h'] - sleep_daily['rem_h'].fillna(0) - sleep_daily['light_h'].fillna(0)).clip(lower=0)
    sleep_daily['date'] = pd.to_datetime(sleep_daily['date'])
    print(f'  Søvn: {len(sleep_daily)} nætter, gns {sleep_daily["duration_h"].mean():.1f} t')

# SpO2
raw_spo2 = load_shealth('com.samsung.shealth.tracker.oxygen_saturation*.csv')
spo2_daily = pd.DataFrame()
if not raw_spo2.empty:
    raw_spo2['_dt'] = pd.to_datetime(raw_spo2['com.samsung.health.oxygen_saturation.start_time'], errors='coerce')
    raw_spo2['date'] = raw_spo2['_dt'].dt.date
    raw_spo2['spo2'] = pd.to_numeric(raw_spo2['com.samsung.health.oxygen_saturation.spo2'], errors='coerce')
    spo2_daily = raw_spo2.dropna(subset=['date','spo2']).groupby('date')['spo2'].mean().reset_index()
    spo2_daily['date'] = pd.to_datetime(spo2_daily['date'])
    spo2_daily['spo2'] = spo2_daily['spo2'].round(1)
    print(f'  SpO2: {len(spo2_daily)} dage, gns {spo2_daily["spo2"].mean():.1f}%')

# Vitalitet
raw_vit = load_shealth('com.samsung.shealth.vitality_score*.csv')
stress_daily = pd.DataFrame()
if not raw_vit.empty:
    raw_vit['date'] = pd.to_datetime(raw_vit['day_time'], errors='coerce').dt.date
    raw_vit['score'] = pd.to_numeric(raw_vit.get('total_score', pd.Series(dtype=float)), errors='coerce')
    stress_daily = raw_vit.dropna(subset=['date','score']).groupby('date')['score'].mean().reset_index()
    stress_daily['date'] = pd.to_datetime(stress_daily['date'])
    stress_daily['score'] = stress_daily['score'].round(1)
    print(f'  Vitalitet: {len(stress_daily)} dage, gns {stress_daily["score"].mean():.0f}/100')

# MinSundhedsplatform data
diagnoses = []
lab_results = []
visits = []

dx_path = os.path.join(SCRAPER_DIR, 'diagnoser.csv')
if os.path.exists(dx_path):
    df = pd.read_csv(dx_path, encoding='utf-8-sig')
    diagnoses = df.to_dict('records')
    print(f'  Diagnoser: {len(diagnoses)}')

pv_path = os.path.join(SCRAPER_DIR, 'proevesvar.csv')
if os.path.exists(pv_path):
    df = pd.read_csv(pv_path, encoding='utf-8-sig')
    df = df.dropna(subset=['dato_iso'])
    lab_results = df.to_dict('records')
    print(f'  Proevesvar: {len(lab_results)}')

bv_path = os.path.join(SCRAPER_DIR, 'besoeg.csv')
if os.path.exists(bv_path):
    df = pd.read_csv(bv_path, encoding='utf-8-sig')
    visits = df.to_dict('records')
    print(f'  Besoeg: {len(visits)}')

# ── Byg datasæt til HTML ──────────────────────────────────────────────────
steps_data   = to_json(steps_daily, 'date', 'count')
steps_roll7  = rolling_avg(steps_data, 7)
hr_data      = to_json(hr_daily, 'date', 'hr')
hr_roll30    = rolling_avg(hr_data, 30)
spo2_data    = to_json(spo2_daily, 'date', 'spo2')
vit_data     = to_json(stress_daily, 'date', 'score')

sleep_data = []
if not sleep_daily.empty:
    sleep_daily_s = sleep_daily.sort_values('date')
    for _, r in sleep_daily_s.iterrows():
        sleep_data.append({
            'x':     r['date'].strftime('%Y-%m-%d'),
            'total': round(float(r['duration_h']), 2),
            'rem':   round(float(r['rem_h']) if pd.notna(r['rem_h']) else 0, 2),
            'light': round(float(r['light_h']) if pd.notna(r['light_h']) else 0, 2),
            'deep':  round(float(r['deep_h']) if pd.notna(r['deep_h']) else 0, 2),
        })

# Statistik
def stat(df, col):
    if df.empty or col not in df.columns:
        return {'mean': 0, 'min': 0, 'max': 0, 'last': 0}
    s = df[col].dropna()
    return {
        'mean': round(float(s.mean()), 1),
        'min':  round(float(s.min()), 1),
        'max':  round(float(s.max()), 1),
        'last': round(float(s.iloc[-1]), 1) if len(s) else 0,
    }

stats = {
    'steps':  stat(steps_daily, 'count'),
    'hr':     stat(hr_daily, 'hr'),
    'sleep':  stat(sleep_daily, 'duration_h') if not sleep_daily.empty else {'mean':0,'min':0,'max':0,'last':0},
    'spo2':   stat(spo2_daily, 'spo2'),
    'vit':    stat(stress_daily, 'score'),
}

date_range = {
    'start': min(
        [d['x'] for d in steps_data[:1]] +
        [d['x'] for d in hr_data[:1]] +
        [d['x'] for d in sleep_data[:1]] +
        ['N/A']
    ),
    'end': max(
        [d['x'] for d in steps_data[-1:]] +
        [d['x'] for d in hr_data[-1:]] +
        [d['x'] for d in sleep_data[-1:]] +
        ['N/A']
    ),
}

payload = json.dumps({
    'steps':      steps_data,
    'steps_avg':  steps_roll7,
    'hr':         hr_data,
    'hr_avg':     hr_roll30,
    'sleep':      sleep_data,
    'spo2':       spo2_data,
    'vitality':   vit_data,
    'stats':      stats,
    'date_range': date_range,
    'diagnoses':  diagnoses,
    'lab':        lab_results,
    'visits':     visits,
}, ensure_ascii=False, default=str)

# ── HTML ──────────────────────────────────────────────────────────────────
html = f"""<!DOCTYPE html>
<html lang="da">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Health Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
<style>
  :root {{
    --bg:       #0d0d0f;
    --card:     #1c1c1e;
    --card2:    #2c2c2e;
    --border:   #3a3a3c;
    --text:     #f2f2f7;
    --muted:    #8e8e93;
    --green:    #30d158;
    --red:      #ff375f;
    --blue:     #0a84ff;
    --purple:   #bf5af2;
    --orange:   #ff9f0a;
    --teal:     #5ac8fa;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    background: var(--bg);
    color: var(--text);
    font-family: -apple-system, 'SF Pro Display', BlinkMacSystemFont, sans-serif;
    min-height: 100vh;
  }}
  header {{
    padding: 32px 32px 0;
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    border-bottom: 1px solid var(--border);
    padding-bottom: 20px;
    margin-bottom: 28px;
  }}
  header h1 {{
    font-size: 28px;
    font-weight: 700;
    letter-spacing: -0.5px;
  }}
  header span {{
    color: var(--muted);
    font-size: 13px;
  }}
  .grid {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
    padding: 0 32px 24px;
  }}
  .kpi {{
    background: var(--card);
    border-radius: 16px;
    padding: 20px;
    border: 1px solid var(--border);
  }}
  .kpi-label {{
    font-size: 12px;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 8px;
  }}
  .kpi-value {{
    font-size: 34px;
    font-weight: 700;
    letter-spacing: -1px;
    line-height: 1;
  }}
  .kpi-sub {{
    font-size: 12px;
    color: var(--muted);
    margin-top: 6px;
  }}
  .charts {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
    padding: 0 32px 24px;
  }}
  .chart-card {{
    background: var(--card);
    border-radius: 16px;
    border: 1px solid var(--border);
    padding: 20px;
  }}
  .chart-card.wide {{
    grid-column: span 2;
  }}
  .chart-title {{
    font-size: 14px;
    font-weight: 600;
    margin-bottom: 4px;
  }}
  .chart-sub {{
    font-size: 12px;
    color: var(--muted);
    margin-bottom: 16px;
  }}
  .chart-area {{
    width: 100%;
    height: 220px;
  }}
  .chart-area.tall {{
    height: 300px;
  }}
  .section-title {{
    font-size: 18px;
    font-weight: 700;
    padding: 8px 32px 16px;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 1px;
    font-size: 11px;
  }}
  .data-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
    padding: 0 32px 40px;
  }}
  .data-card {{
    background: var(--card);
    border-radius: 16px;
    border: 1px solid var(--border);
    overflow: hidden;
  }}
  .data-card-header {{
    padding: 16px 20px 12px;
    border-bottom: 1px solid var(--border);
    font-size: 14px;
    font-weight: 600;
  }}
  .data-row {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 20px;
    border-bottom: 1px solid var(--border);
    font-size: 13px;
  }}
  .data-row:last-child {{ border-bottom: none; }}
  .data-row-label {{ color: var(--text); }}
  .data-row-meta {{ color: var(--muted); font-size: 12px; }}
  .badge {{
    font-size: 11px;
    padding: 3px 8px;
    border-radius: 6px;
    font-weight: 600;
  }}
  .badge-red    {{ background: rgba(255,55,95,.15);  color: var(--red);    }}
  .badge-green  {{ background: rgba(48,209,88,.15);  color: var(--green);  }}
  .badge-blue   {{ background: rgba(10,132,255,.15); color: var(--blue);   }}
  .badge-purple {{ background: rgba(191,90,242,.15); color: var(--purple); }}
  .badge-orange {{ background: rgba(255,159,10,.15); color: var(--orange); }}
</style>
</head>
<body>

<header>
  <div>
    <div style="font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:1px;margin-bottom:4px">Samsung Health</div>
    <h1>Health Dashboard</h1>
  </div>
  <span id="dateRange">Indlæser...</span>
</header>

<!-- KPI-kort -->
<div class="grid">
  <div class="kpi">
    <div class="kpi-label" style="color:var(--green)">● Skridt</div>
    <div class="kpi-value" style="color:var(--green)" id="kpi-steps">—</div>
    <div class="kpi-sub">dagligt gennemsnit</div>
  </div>
  <div class="kpi">
    <div class="kpi-label" style="color:var(--red)">● Hvilepuls</div>
    <div class="kpi-value" style="color:var(--red)" id="kpi-hr">—</div>
    <div class="kpi-sub">bpm gennemsnit</div>
  </div>
  <div class="kpi">
    <div class="kpi-label" style="color:var(--purple)">● Søvn</div>
    <div class="kpi-value" style="color:var(--purple)" id="kpi-sleep">—</div>
    <div class="kpi-sub">timer pr. nat</div>
  </div>
  <div class="kpi">
    <div class="kpi-label" style="color:var(--blue)">● SpO2</div>
    <div class="kpi-value" style="color:var(--blue)" id="kpi-spo2">—</div>
    <div class="kpi-sub">iltmætning gns.</div>
  </div>
</div>

<!-- Grafer -->
<div class="section-title">Samsung Health Data</div>
<div class="charts">

  <div class="chart-card wide">
    <div class="chart-title">Daglige skridt</div>
    <div class="chart-sub">Faktiske dage + 7-dages glidende gennemsnit</div>
    <div class="chart-area tall" id="chart-steps"></div>
  </div>

  <div class="chart-card">
    <div class="chart-title">Hvilepuls</div>
    <div class="chart-sub">Dagligt gennemsnit + 30-dages trend</div>
    <div class="chart-area" id="chart-hr"></div>
  </div>

  <div class="chart-card">
    <div class="chart-title">Iltmætning — SpO2</div>
    <div class="chart-sub">Nattarget ≥ 95%</div>
    <div class="chart-area" id="chart-spo2"></div>
  </div>

  <div class="chart-card">
    <div class="chart-title">Søvnvarighed</div>
    <div class="chart-sub">Timer pr. nat — kun nætter med registreret søvn</div>
    <div class="chart-area" id="chart-sleep"></div>
  </div>

  <div class="chart-card">
    <div class="chart-title">Søvnstadier</div>
    <div class="chart-sub">Fordeling dyb / REM / let søvn</div>
    <div class="chart-area" id="chart-sleep-stages"></div>
  </div>

  <div class="chart-card">
    <div class="chart-title">Vitalitetsscore</div>
    <div class="chart-sub">Samsung Energy Score 0–100</div>
    <div class="chart-area" id="chart-vitality"></div>
  </div>

</div>

<!-- MinSundhedsplatform -->
<div class="section-title">MinSundhedsplatform</div>
<div class="data-grid">

  <div class="data-card">
    <div class="data-card-header">Diagnoser</div>
    <div id="dx-list"></div>
  </div>

  <div class="data-card">
    <div class="data-card-header">Seneste prøvesvar</div>
    <div id="lab-list"></div>
  </div>

  <div class="data-card">
    <div class="data-card-header">Sygehusbesøg</div>
    <div id="visit-list"></div>
  </div>

</div>

<script>
const DATA = {payload};

// KPI-kort
const s = DATA.stats;
document.getElementById('kpi-steps').textContent  = s.steps.mean.toLocaleString('da-DK', {{maximumFractionDigits:0}});
document.getElementById('kpi-hr').textContent    = s.hr.mean + ' bpm';
document.getElementById('kpi-sleep').textContent = s.sleep.mean + ' t';
document.getElementById('kpi-spo2').textContent  = s.spo2.mean + '%';

const dr = DATA.date_range;
document.getElementById('dateRange').textContent =
  dr.start !== 'N/A' ? dr.start + ' → ' + dr.end : '';

const DARK = '#1c1c1e';
const MUTED = '#8e8e93';
const GRID = 'rgba(255,255,255,0.06)';

function baseOpts(color) {{
  return {{
    backgroundColor: 'transparent',
    animation: true,
    animationDuration: 800,
    grid: {{ top: 10, right: 16, bottom: 40, left: 50 }},
    xAxis: {{
      type: 'time',
      axisLabel: {{ color: MUTED, fontSize: 11 }},
      axisLine: {{ lineStyle: {{ color: GRID }} }},
      splitLine: {{ show: false }},
    }},
    yAxis: {{
      axisLabel: {{ color: MUTED, fontSize: 11 }},
      axisLine: {{ show: false }},
      splitLine: {{ lineStyle: {{ color: GRID }} }},
    }},
    tooltip: {{
      trigger: 'axis',
      backgroundColor: '#2c2c2e',
      borderColor: '#3a3a3c',
      textStyle: {{ color: '#f2f2f7', fontSize: 12 }},
    }},
  }};
}}

// ── Skridt ──────────────────────────────────────────────────────────────
if (DATA.steps.length) {{
  const c = echarts.init(document.getElementById('chart-steps'));
  const opts = baseOpts('#30d158');
  opts.grid = {{ top: 10, right: 16, bottom: 40, left: 60 }};
  opts.series = [
    {{
      name: 'Skridt',
      type: 'bar',
      data: DATA.steps.map(d => [d.x, d.y]),
      itemStyle: {{ color: 'rgba(48,209,88,0.35)', borderRadius: [2,2,0,0] }},
      barMaxWidth: 8,
    }},
    {{
      name: '7-dages gns',
      type: 'line',
      data: DATA.steps_avg.map(d => [d.x, d.y]),
      smooth: true,
      symbol: 'none',
      lineStyle: {{ color: '#30d158', width: 2 }},
      areaStyle: {{ color: new echarts.graphic.LinearGradient(0,0,0,1, [
        {{offset:0, color:'rgba(48,209,88,0.15)'}},
        {{offset:1, color:'rgba(48,209,88,0)'}}
      ])}},
    }},
    {{
      type: 'line',
      markLine: {{
        silent: true,
        symbol: 'none',
        data: [{{yAxis: 10000}}],
        lineStyle: {{ color: 'rgba(48,209,88,0.4)', type: 'dashed', width: 1 }},
        label: {{ formatter: 'WHO 10.000', color: 'rgba(48,209,88,0.6)', fontSize: 11 }},
      }},
    }},
  ];
  c.setOption(opts);
}}

// ── Puls ────────────────────────────────────────────────────────────────
if (DATA.hr.length) {{
  const c = echarts.init(document.getElementById('chart-hr'));
  const opts = baseOpts('#ff375f');
  opts.yAxis.min = d => Math.floor(d.min * 0.95);
  opts.series = [
    {{
      name: 'Puls',
      type: 'scatter',
      data: DATA.hr.map(d => [d.x, d.y]),
      symbolSize: 3,
      itemStyle: {{ color: 'rgba(255,55,95,0.3)' }},
    }},
    {{
      name: '30-dages gns',
      type: 'line',
      data: DATA.hr_avg.map(d => [d.x, d.y]),
      smooth: true,
      symbol: 'none',
      lineStyle: {{ color: '#ff375f', width: 2.5 }},
    }},
  ];
  opts.visualMap = {{
    show: false,
    pieces: [
      {{ min: 100, color: 'rgba(255,55,95,0.9)' }},
      {{ min: 85, max: 100, color: 'rgba(255,159,10,0.9)' }},
      {{ max: 85, color: '#ff375f' }},
    ],
    dimension: 1,
    seriesIndex: 1,
  }};
  c.setOption(opts);
}}

// ── SpO2 ────────────────────────────────────────────────────────────────
if (DATA.spo2.length) {{
  const c = echarts.init(document.getElementById('chart-spo2'));
  const opts = baseOpts('#0a84ff');
  opts.yAxis.min = d => Math.max(85, Math.floor(d.min - 1));
  opts.yAxis.max = 101;
  opts.series = [
    {{
      name: 'SpO2',
      type: 'line',
      data: DATA.spo2.map(d => [d.x, d.y]),
      smooth: true,
      symbol: 'none',
      lineStyle: {{ color: '#0a84ff', width: 1.5 }},
      areaStyle: {{ color: new echarts.graphic.LinearGradient(0,0,0,1, [
        {{offset:0, color:'rgba(10,132,255,0.3)'}},
        {{offset:1, color:'rgba(10,132,255,0)'}}
      ])}},
    }},
    {{
      type: 'line',
      markLine: {{
        silent: true, symbol: 'none',
        data: [{{yAxis: 95}}],
        lineStyle: {{ color: 'rgba(255,159,10,0.5)', type: 'dashed', width: 1 }},
        label: {{ formatter: '95%', color: 'rgba(255,159,10,0.7)', fontSize: 11 }},
      }},
    }},
  ];
  opts.visualMap = {{
    show: false,
    pieces: [
      {{ max: 94, color: '#ff375f' }},
      {{ min: 94, max: 96, color: '#ff9f0a' }},
      {{ min: 96, color: '#0a84ff' }},
    ],
    dimension: 1,
    seriesIndex: 0,
  }};
  c.setOption(opts);
}}

// ── Søvn varighed ────────────────────────────────────────────────────────
if (DATA.sleep.length) {{
  const c = echarts.init(document.getElementById('chart-sleep'));
  const opts = baseOpts('#bf5af2');
  opts.series = [
    {{
      name: 'Søvn',
      type: 'bar',
      data: DATA.sleep.map(d => [d.x, d.total]),
      itemStyle: {{ color: new echarts.graphic.LinearGradient(0,0,0,1,[
        {{offset:0,color:'rgba(191,90,242,0.9)'}},
        {{offset:1,color:'rgba(191,90,242,0.3)'}}
      ]), borderRadius: [3,3,0,0] }},
      barMaxWidth: 10,
    }},
    {{
      type: 'line',
      markLine: {{
        silent: true, symbol: 'none',
        data: [{{yAxis: 7}}],
        lineStyle: {{ color: 'rgba(48,209,88,0.4)', type: 'dashed', width: 1 }},
        label: {{ formatter: '7t', color: 'rgba(48,209,88,0.6)', fontSize: 11 }},
      }},
    }},
  ];
  c.setOption(opts);
}}

// ── Søvnstadier stacked bar ──────────────────────────────────────────────
if (DATA.sleep.length) {{
  const c = echarts.init(document.getElementById('chart-sleep-stages'));
  const opts = baseOpts('#bf5af2');
  opts.legend = {{
    bottom: 0,
    textStyle: {{ color: MUTED, fontSize: 11 }},
    itemWidth: 10, itemHeight: 10,
  }};
  opts.grid.bottom = 60;
  opts.series = [
    {{
      name: 'Dyb', type: 'bar',
      stack: 'sleep',
      data: DATA.sleep.map(d => [d.x, d.deep]),
      itemStyle: {{ color: '#1a237e', borderRadius: [0,0,0,0] }},
      barMaxWidth: 10,
    }},
    {{
      name: 'REM', type: 'bar',
      stack: 'sleep',
      data: DATA.sleep.map(d => [d.x, d.rem]),
      itemStyle: {{ color: '#7c4dff' }},
      barMaxWidth: 10,
    }},
    {{
      name: 'Let', type: 'bar',
      stack: 'sleep',
      data: DATA.sleep.map(d => [d.x, d.light]),
      itemStyle: {{ color: 'rgba(191,90,242,0.4)', borderRadius: [3,3,0,0] }},
      barMaxWidth: 10,
    }},
  ];
  c.setOption(opts);
}}

// ── Vitalitet ────────────────────────────────────────────────────────────
if (DATA.vitality.length) {{
  const c = echarts.init(document.getElementById('chart-vitality'));
  const opts = baseOpts('#ff9f0a');
  opts.yAxis.min = 0; opts.yAxis.max = 100;
  opts.series = [
    {{
      name: 'Vitalitet',
      type: 'line',
      data: DATA.vitality.map(d => [d.x, d.y]),
      smooth: true,
      symbol: 'none',
      lineStyle: {{ color: '#ff9f0a', width: 1.5 }},
      areaStyle: {{ color: new echarts.graphic.LinearGradient(0,0,0,1,[
        {{offset:0,color:'rgba(255,159,10,0.35)'}},
        {{offset:1,color:'rgba(255,159,10,0)'}}
      ])}},
    }},
  ];
  opts.visualMap = {{
    show: false,
    pieces: [
      {{ max: 40, color: '#ff375f' }},
      {{ min: 40, max: 70, color: '#ff9f0a' }},
      {{ min: 70, color: '#30d158' }},
    ],
    dimension: 1, seriesIndex: 0,
  }};
  c.setOption(opts);
}}

// ── Diagnoser ────────────────────────────────────────────────────────────
const dxList = document.getElementById('dx-list');
if (DATA.diagnoses.length) {{
  DATA.diagnoses.forEach(d => {{
    dxList.innerHTML += `
      <div class="data-row">
        <div>
          <div class="data-row-label">${{d.diagnose || d.name || '—'}}</div>
          <div class="data-row-meta">${{d.dato || ''}} · ${{d.icd_kode || ''}}</div>
        </div>
        <span class="badge badge-blue">${{d.icd_kode || ''}}</span>
      </div>`;
  }});
}} else {{
  dxList.innerHTML = '<div class="data-row"><div class="data-row-meta">Ingen data</div></div>';
}}

// ── Prøvesvar ────────────────────────────────────────────────────────────
const labList = document.getElementById('lab-list');
const uniqueLab = [];
const seen = new Set();
DATA.lab.forEach(l => {{
  const key = l.navn || l.test || l.name;
  if (!seen.has(key)) {{ seen.add(key); uniqueLab.push(l); }}
}});
uniqueLab.slice(0, 12).forEach(l => {{
  const flag = (l.abnormal === 'True' || l.abnormal === true);
  labList.innerHTML += `
    <div class="data-row">
      <div>
        <div class="data-row-label">${{l.navn || l.test || '—'}}</div>
        <div class="data-row-meta">${{l.dato_iso || l.dato || ''}} · ${{l.laege || ''}}</div>
      </div>
      ${{flag ? '<span class="badge badge-red">Abnormal</span>' : '<span class="badge badge-green">OK</span>'}}
    </div>`;
}});
if (!uniqueLab.length) {{
  labList.innerHTML = '<div class="data-row"><div class="data-row-meta">Ingen data</div></div>';
}}

// ── Besøg ─────────────────────────────────────────────────────────────────
const visitList = document.getElementById('visit-list');
if (DATA.visits.length) {{
  DATA.visits.slice(0, 10).forEach(v => {{
    const d = new Date(v.dato);
    const dateStr = isNaN(d) ? v.dato : d.toLocaleDateString('da-DK', {{day:'numeric',month:'short',year:'numeric'}});
    visitList.innerHTML += `
      <div class="data-row">
        <div>
          <div class="data-row-label">${{v.hospital || 'Sygehus'}}</div>
          <div class="data-row-meta">${{dateStr}}</div>
        </div>
        <span class="badge badge-purple">Journal</span>
      </div>`;
  }});
}} else {{
  visitList.innerHTML = '<div class="data-row"><div class="data-row-meta">Ingen data</div></div>';
}}

window.addEventListener('resize', () => {{
  echarts.getInstanceByDom(document.getElementById('chart-steps'))?.resize();
  echarts.getInstanceByDom(document.getElementById('chart-hr'))?.resize();
  echarts.getInstanceByDom(document.getElementById('chart-spo2'))?.resize();
  echarts.getInstanceByDom(document.getElementById('chart-sleep'))?.resize();
  echarts.getInstanceByDom(document.getElementById('chart-sleep-stages'))?.resize();
  echarts.getInstanceByDom(document.getElementById('chart-vitality'))?.resize();
}});
</script>
</body>
</html>"""

with open(OUTPUT, 'w', encoding='utf-8') as f:
    f.write(html.replace('{payload}', payload))

print(f'\nDashboard gemt: {OUTPUT}')
print('Åbn filen direkte i din browser.')
