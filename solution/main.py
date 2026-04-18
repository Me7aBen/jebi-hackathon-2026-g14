"""
solution/main.py - Agrega outputs de los pipelines y genera los 3 entregables finales.

Lee:   outputs/cycles.json, outputs/truck_events.json, outputs/fill_factor.json
Escribe: outputs/metrics.json, outputs/report.html, outputs/summary.md
"""
import json
import os
import numpy as np

OUTPUT_DIR       = './outputs'
BUCKET_CAP_T     = 68   # EX-5600 capacidad nominal del balde (toneladas)


# ─── HELPERS ──────────────────────────────────────────────────────────────────

def load(filename, default=None):
    path = os.path.join(OUTPUT_DIR, filename)
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    print(f"[warning] {filename} no encontrado, usando default")
    return default


def build_metrics(cycles_data, exchanges, fill_factors):
    summary = cycles_data.get('summary', {})
    cycles  = cycles_data.get('cycles', [])

    valid_cycles   = [c['duration_s'] for c in cycles if 5 < c['duration_s'] < 120]
    mean_cycle_s   = float(np.mean(valid_cycles))   if valid_cycles else 0.0
    cycles_per_h   = 3600 / mean_cycle_s             if mean_cycle_s > 0 else 0.0

    dead_times     = [e['exchange_duration_s'] for e in exchanges]
    mean_dead_s    = float(np.mean(dead_times))      if dead_times else 0.0

    ff_list        = [f['fill_factor'] for f in fill_factors] if fill_factors else []
    mean_fill      = float(np.mean(ff_list))         if ff_list else 0.70

    productivity   = cycles_per_h * mean_fill * BUCKET_CAP_T
    n_trucks       = max(len(exchanges) + 1, 1)

    return {
        "productivity_t_per_h":      round(productivity, 1),
        "mean_cycle_time_s":         round(mean_cycle_s, 1),
        "cycles_per_hour":           round(cycles_per_h, 2),
        "mean_fill_factor":          round(mean_fill, 3),
        "bucket_capacity_t":         BUCKET_CAP_T,
        "mean_exchange_dead_time_s": round(mean_dead_s, 1),
        "n_exchanges_detected":      len(exchanges),
        "smoothness_rms_jerk":       round(summary.get('smoothness_rms_jerk', 0), 4),
        "pct_productive_time":       round(summary.get('pct_productive_time', 0), 1),
        "n_cycles_detected":         summary.get('n_cycles_detected', len(cycles)),
        "n_cycles_per_truck":        round(len(cycles) / n_trucks, 1),
    }


# ─── REPORT HTML ──────────────────────────────────────────────────────────────

def generate_report(metrics, cycles_data, exchanges, fill_factors):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import base64, io

    cycles  = cycles_data.get('cycles', [])
    summary = cycles_data.get('summary', {})

    fig, axes = plt.subplots(1, 3, figsize=(15, 4))
    fig.suptitle('Hitachi EX-5600 — Productivity Dashboard', fontsize=13, fontweight='bold')

    # 1. Tiempos de ciclo
    if cycles:
        durs = [c['duration_s'] for c in cycles]
        axes[0].bar(range(1, len(durs)+1), durs, color='steelblue', alpha=0.8)
        axes[0].axhline(metrics['mean_cycle_time_s'], color='red', linestyle='--',
                        label=f"media={metrics['mean_cycle_time_s']:.1f}s")
        axes[0].set_title('Tiempo de ciclo (s)')
        axes[0].set_xlabel('Ciclo #')
        axes[0].legend(fontsize=8)

    # 2. Fill factor por camión
    if fill_factors:
        ffs    = [f['fill_factor'] for f in fill_factors]
        colors = ['seagreen' if ff >= 0.70 else 'tomato' for ff in ffs]
        axes[1].bar([f"T{i+1}" for i in range(len(ffs))], ffs, color=colors, alpha=0.85)
        axes[1].axhline(0.70, color='black', linestyle='--', label='objetivo 0.70')
        axes[1].set_ylim(0, 1.1)
        axes[1].set_title('Fill factor por camión')
        axes[1].legend(fontsize=8)
    else:
        axes[1].text(0.5, 0.5, 'Sin datos\nde fill factor', ha='center', va='center',
                     transform=axes[1].transAxes, color='gray')
        axes[1].set_title('Fill factor por camión')

    # 3. Distribución del tiempo
    labels_pie = ['Swing activo', 'Paradas op.', 'Espera', 'Tiempo muerto']
    sizes = [
        max(0, summary.get('time_active_swing_s', 0)),
        max(0, summary.get('time_operational_stops_s', 0)),
        max(0, summary.get('time_wait_s', 0)),
        max(0, summary.get('time_dead_s', 0)),
    ]
    if sum(sizes) > 0:
        axes[2].pie(sizes, labels=labels_pie, autopct='%1.0f%%',
                    colors=['steelblue', 'lightgreen', 'orange', 'tomato'],
                    startangle=90)
        axes[2].set_title('Distribución del tiempo')

    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
    plt.close()
    chart_b64 = base64.b64encode(buf.getvalue()).decode()

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <title>Mining Productivity Report</title>
  <style>
    body  {{ font-family: Arial, sans-serif; max-width: 960px; margin: 40px auto; padding: 0 20px; background: #f5f5f5; }}
    h1   {{ color: #1a237e; }}
    h2   {{ color: #283593; border-bottom: 2px solid #3f51b5; padding-bottom: 6px; }}
    .grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; margin: 20px 0; }}
    .kpi  {{ background: white; border-radius: 8px; padding: 18px; text-align: center; box-shadow: 0 2px 6px rgba(0,0,0,.1); }}
    .kpi .val {{ font-size: 2em; font-weight: bold; color: #1a237e; }}
    .kpi .lbl {{ color: #555; font-size: .85em; margin-top: 4px; }}
    .card {{ background: white; border-radius: 8px; padding: 16px; margin: 20px 0; box-shadow: 0 2px 6px rgba(0,0,0,.1); }}
    img   {{ max-width: 100%; }}
    pre   {{ overflow: auto; font-size: .85em; }}
  </style>
</head>
<body>
<h1>Mining Shovel Productivity Report</h1>
<p>Hitachi EX-5600 — Generado automáticamente · Hackathon JEBI 2026</p>

<h2>KPIs Principales</h2>
<div class="grid">
  <div class="kpi"><div class="val">{metrics['productivity_t_per_h']:.0f}</div><div class="lbl">t / hora</div></div>
  <div class="kpi"><div class="val">{metrics['mean_cycle_time_s']:.1f}s</div><div class="lbl">Tiempo ciclo promedio</div></div>
  <div class="kpi"><div class="val">{metrics['mean_fill_factor']:.0%}</div><div class="lbl">Fill factor promedio</div></div>
  <div class="kpi"><div class="val">{metrics['cycles_per_hour']:.1f}</div><div class="lbl">Ciclos / hora</div></div>
  <div class="kpi"><div class="val">{metrics['mean_exchange_dead_time_s']:.1f}s</div><div class="lbl">Tiempo muerto / intercambio</div></div>
  <div class="kpi"><div class="val">{metrics['smoothness_rms_jerk']:.3f}</div><div class="lbl">RMS Jerk (suavidad)</div></div>
</div>

<h2>Gráficos</h2>
<div class="card"><img src="data:image/png;base64,{chart_b64}" alt="dashboard"/></div>

<h2>metrics.json</h2>
<div class="card"><pre>{json.dumps(metrics, indent=2)}</pre></div>
</body>
</html>"""

    with open(os.path.join(OUTPUT_DIR, 'report.html'), 'w') as f:
        f.write(html)
    print("✓ report.html generado")


# ─── SUMMARY.MD con Claude ────────────────────────────────────────────────────

def generate_summary(metrics, cycles_data, exchanges):
    try:
        import anthropic
        client = anthropic.Anthropic()   # lee ANTHROPIC_API_KEY del entorno

        prompt = f"""Eres un experto en productividad de minería a tajo abierto.
Analiza estos KPIs de una pala Hitachi EX-5600 y escribe un summary.md con:
1. Una frase de diagnóstico (productividad real vs potencial estimado)
2. El insight principal (si ciclos rápidos correlacionan con menor fill factor, menciónalo)
3. Exactamente 3 recomendaciones accionables con los números concretos

KPIs:
{json.dumps(metrics, indent=2)}

Ciclos detectados: {len(cycles_data.get('cycles', []))}
Intercambios de camión: {len(exchanges)} (tiempo muerto promedio {metrics['mean_exchange_dead_time_s']}s)

Responde en español, formato Markdown, máximo 300 palabras."""

        msg = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=800,
            messages=[{"role": "user", "content": prompt}]
        )
        text = msg.content[0].text

    except Exception as e:
        print(f"[warning] Claude API: {e} — usando summary básico")
        text = f"""# Resumen de Productividad — Hitachi EX-5600

## Diagnóstico
Productividad estimada: **{metrics['productivity_t_per_h']:.0f} t/hora**
({metrics['cycles_per_hour']:.1f} ciclos/h × {metrics['mean_fill_factor']:.0%} fill × 68 t/balde)

## Insight principal
- Tiempo de ciclo promedio: **{metrics['mean_cycle_time_s']:.1f}s**
- Fill factor promedio: **{metrics['mean_fill_factor']:.0%}**
- Tiempo muerto por intercambio: **{metrics['mean_exchange_dead_time_s']:.1f}s** en {metrics['n_exchanges_detected']} intercambios

## Recomendaciones
1. **Reducir tiempo de intercambio** de {metrics['mean_exchange_dead_time_s']:.1f}s → objetivo <15s (coordinación con operadores de camión).
2. **Monitorear correlación ciclo–fill**: ciclos muy rápidos (<{metrics['mean_cycle_time_s']*0.8:.0f}s) pueden reducir el fill factor y disminuir tonelaje real.
3. **Suavidad del operador** (RMS jerk={metrics['smoothness_rms_jerk']:.4f}): reducir movimientos bruscos extiende vida útil y puede mejorar fill.
"""

    with open(os.path.join(OUTPUT_DIR, 'summary.md'), 'w') as f:
        f.write(text)
    print("✓ summary.md generado")


# ─── MAIN ─────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    print("=== main.py: agregando métricas ===\n")

    cycles_data  = load('cycles.json',       default={'summary': {}, 'cycles': []})
    exchanges    = load('truck_events.json', default=[])
    fill_factors = load('fill_factor.json',  default=[])

    metrics = build_metrics(cycles_data, exchanges, fill_factors)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(os.path.join(OUTPUT_DIR, 'metrics.json'), 'w') as f:
        json.dump(metrics, f, indent=2)
    print("✓ metrics.json generado")
    print(json.dumps(metrics, indent=2))
    print()

    generate_report(metrics, cycles_data, exchanges, fill_factors)
    generate_summary(metrics, cycles_data, exchanges)
