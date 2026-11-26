# design.md: Next-Day PM2.5 Forecast (weather-app theme)

The site should feel like a weather app, but for air: open it, see one big number, one condition word, and an hourly strip for the next 24 hours. Build from this file; change it first if the design changes.

---

## 1. Purpose

Two parts, one visual language:

1. **Dashboard (the product):** a weather-style screen for tomorrow's PM2.5.
2. **Landing page (the showcase):** explains the problem, approach, data and plan, with the dashboard shown in a phone frame.

**Honesty rule:** until the models are trained, every value is sample data and the screen says **"Proposed design | Sample data"**. Targets (RMSE < 20, MAE < 14, R² > 0.75) are always called targets, never results.

## 2. Weather-app mapping

| Weather app idea | Our version |
|---|---|
| Location | Monitoring station (12 Beijing stations, picker at top) |
| Big temperature | Big PM2.5 number in µg/m³ |
| Condition ("Partly cloudy") | Category ("Moderate") with a haze icon |
| H / L | Peak / lowest PM2.5 in the next 24 h |
| Hourly forecast strip | 24-hour PM2.5 strip, scrolls sideways |
| Sky changes with weather | Background gradient changes with category |
| Detail tiles (wind, humidity) | Best window, peak risk, wind, temperature, dew point, pressure |
| AQI bar with marker | PM2.5 scale bar with a marker on the current value |
| "Feels like" sentence | One-line advisory, e.g. "Best time outside is 1 to 5 PM." |

## 3. Principles

1. **One glance, one answer.** Hero number, condition, advisory sentence.
2. **Mobile-first.** Designed as a phone screen; desktop centers it or widens into a grid.
3. **Sky as mood.** The background tells you the air quality before you read anything.
4. **Calm and honest.** Never alarmist; always label sample data, Beijing data and targets.

## 4. Color tokens

```css
:root {
  /* Sky gradients (top to bottom), one per category, day */
  --sky-good:         linear-gradient(#4E9FD1, #A4D9D2);
  --sky-satisfactory: linear-gradient(#5FA3CF, #CBE0B0);
  --sky-moderate:     linear-gradient(#C8955A, #F0D6A0);   /* golden haze */
  --sky-poor:         linear-gradient(#BE7650, #E9B58D);
  --sky-very-poor:    linear-gradient(#96566A, #D99C9C);
  --sky-severe:       linear-gradient(#5A3850, #A0647A);
  --sky-night:        linear-gradient(#1B2540, #3E4573);   /* used when forecast hour is 7 PM to 5 AM */

  /* Glass */
  --glass: rgba(255,255,255,0.18);
  --glass-strong: rgba(255,255,255,0.28);
  --glass-border: rgba(255,255,255,0.30);
  --scrim: rgba(15,23,32,0.14);       /* overlay on sky to protect text contrast */

  /* Text on sky */
  --text: #FFFFFF;
  --text-soft: rgba(255,255,255,0.82);
  --text-faint: rgba(255,255,255,0.64);   /* labels only, 12px+ uppercase */

  /* Category colors (bars, dots, scale) */
  --aq-good: #3FA796;
  --aq-satisfactory: #A8C66C;
  --aq-moderate: #E8A317;
  --aq-poor: #E57A44;
  --aq-very-poor: #D1495B;
  --aq-severe: #8E2C48;

  /* Accent / notice pill */
  --sun: #E8A317;
  --sun-ink: #1F2A33;
}
```

Always place `--scrim` over the sky so white text stays readable on the lighter gradients (Satisfactory, Moderate, Good). Check contrast on each sky; darken the scrim if any fails 4.5:1 for body text.

### Categories (24-hour PM2.5, µg/m³)

| Category | Range | Sky | Icon (Lucide) | Tone |
|---|---|---|---|---|
| Good | 0–30 | `--sky-good` | `sun` | Enjoy outdoor activity |
| Satisfactory | 31–60 | `--sky-satisfactory` | `cloud-sun` | Fine for most people |
| Moderate | 61–90 | `--sky-moderate` | `cloud-fog` | Sensitive groups take care |
| Poor | 91–120 | `--sky-poor` | `cloud-fog` | Limit long outdoor exertion |
| Very Poor | 121–250 | `--sky-very-poor` | `wind` | Avoid outdoor activity |
| Severe | 250+ | `--sky-severe` | `triangle-alert` | Stay indoors if possible |

> Based on India's CPCB PM2.5 breakpoints. **Verify against the current CPCB guideline before submission.** Keep the table in one file (`aqi.js`) so it is a one-place fix.

Color is never the only signal: pair with the category word and icon.

## 5. Typography

- **Font:** Inter only (fallback `system-ui, sans-serif`). Use `font-variant-numeric: tabular-nums`.
- Weather-app feel comes from **light, large numbers**.

| Role | Size (phone / desktop) | Weight |
|---|---|---|
| Hero number | 96 / 128 px | 200–300 |
| Condition word | 24 / 28 px | 500 |
| Station name | 28 / 32 px | 500 |
| H / L line | 18 px | 500 |
| Advisory sentence | 17 px | 400 |
| Tile value | 28 px | 600 |
| Tile label | 12 px uppercase, 0.08em tracking | 600 |
| Hourly strip time / value | 13 / 18 px | 500 / 600 |
| Landing hero title | 40 / 64 px | 600 |
| Landing section title | 30 / 40 px | 600 |
| Landing body | 16 / 17 px, line-height 1.6 | 400 |

## 6. Shape and depth

- **Cards (tiles):** glass: `--glass` fill, `backdrop-filter: blur(20px)`, 1 px `--glass-border`, radius 22 px, no heavy shadows.
- **Pills and buttons:** fully rounded.
- **Spacing scale:** 4, 8, 12, 16, 24, 32, 48, 72. Tiles gap 12 px (phone), 16 px (desktop).
- **Container:** phone layout max-width 430 px, centered; desktop dashboard grid max-width 1000 px.

## 7. Dashboard layout (top to bottom)

1. **Top bar:** station picker (name with chevron), date, notice pill **"Proposed design | Sample data"**.
2. **Hero:** category icon, huge PM2.5 number (µg/m³ small beside it), condition word, **H: 142  L: 40**.
3. **Advisory line:** one sentence, e.g. "Best time outside is 1 to 5 PM. Peak around 10 PM."
4. **24-hour strip** (glass card): horizontal scroll, snap per hour. Each cell: time (6 AM, 7 AM, then "Now"/next hour first), category icon, value, thin vertical bar colored by category. Highlight the best-window hours with a soft ring.
5. **Scale bar** (glass card): the six categories as a gradient track, marker dot at the current value, label "Moderate".
6. **Tile grid (2 columns phone, 3 desktop):**
   - Best window
   - Peak risk
   - Wind speed
   - Temperature
   - Dew point
   - Pressure
7. **Pollutants card:** PM10, NO₂, SO₂, CO, O₃ as small rows with value and mini bar.
8. **Forecast vs baseline card:** simple line chart, model line vs persistence baseline line, with legend. Caption: "Persistence = tomorrow equals today."
9. **Footnote:** "Forecasts are predictions, not guarantees. Not medical advice. Weather tiles show dataset conditions, not a weather forecast."

**Desktop:** hero + strip + scale in the left 7 columns, tiles + pollutants + baseline chart in the right 5 columns.

**States:** loading (shimmering glass skeletons), error ("Forecast unavailable. Showing last sample."), station switch (sky crossfades 600 ms, number counts up).

## 8. Landing page

Same sky background (default `--sky-moderate`), same glass cards, so it feels like the same app.

1. **Nav** (sticky glass): "PM2.5 Forecast", links *Problem · Approach · Data · Plan*, pill button **Open dashboard**.
2. **Hero:** title *"Know tomorrow's air before you breathe it."*, subtitle, two buttons. Right side: a **phone frame** showing the live demo dashboard (sample data, labelled).
3. **Problem:** big stat **4M+** (premature deaths a year linked to PM2.5, WHO estimate) and three short points.
4. **How it works:** 5 glass steps: Ingest → Clean → Features → Model → Advise, plus "benchmarked against persistence".
5. **Data:** four stat tiles (420,768 records · 12 stations · 18 columns · 2013–17) and source line (UCI Beijing Multi-Site Air Quality, CC BY 4.0).
6. **Targets:** three tiles for RMSE, MAE, R², baseline vs target. Caption: "Goals, not results."
7. **Team and plan:** four member tiles with roles; Oct–Dec timeline; guide name.
8. **Limitations and future scope:** two glass cards. Limits: Beijing data, needs adaptation for India, Colab free-tier compute. Future: Indian CPCB data, live forecasts, mobile alerts.
9. **Footer:** DSCE, Dept. of AI & ML, SDG 11.6.2 note, dataset credit.

## 9. Components

| Component | Notes |
|---|---|
| Primary button | `--sun` fill, `--sun-ink` text, pill, hover lifts 2 px |
| Secondary button | glass fill, white text, 1 px glass border |
| Notice pill | `--sun` fill, `--sun-ink` 12 px bold text |
| Glass tile | label (uppercase 12 px), value (28 px), optional sub-caption |
| Hour cell | 64 px wide, stacked time, icon, value, bar (height maps to value) |
| Scale bar | 10 px track, 20 px marker with white ring |
| Tooltip | glass-strong, 12 px radius |

## 10. Motion

- Slow drifting haze/cloud layers behind content (two large blurred shapes, 40 to 70 s loop).
- Hero number counts up once (600 ms). Strip scrolls with snap; bars grow on first view.
- Sky gradient crossfades when category or station changes.
- Respect `prefers-reduced-motion`: no drifting, no count-up.

## 11. Iconography

Lucide, 1.75 px stroke, white. Weather-style icons per category (table above), plus `map-pin` (station), `wind`, `thermometer`, `droplets` (dew point), `gauge` (pressure), `clock` (best window).

## 12. Accessibility

- 4.5:1 contrast for body text on every sky (use the scrim).
- Category always shown as text plus icon, never color alone.
- Visible focus ring: 3 px white outline, 2 px offset.
- Hourly strip is keyboard scrollable; a visually hidden table lists all 24 values.
- Touch targets at least 44 px. Semantic landmarks, one `h1` per page.

## 13. Responsive

- `<640 px`: single column, full-bleed sky, tiles 2-up.
- `640–1023 px`: centered 430 px phone column on the dashboard.
- `≥1024 px`: two-column dashboard grid as in section 7; landing hero shows the phone frame on the right.

## 14. Tech recommendation

Free and simple (project budget is ₹0):

- **Plain HTML + CSS + vanilla JS**, Chart.js (or SVG) for the baseline chart, Lucide icons.
- Forecasts come from a static `forecast.json` exported from the Colab notebook.
- Host on GitHub Pages or Vercel.
- Later: a small FastAPI endpoint if live forecasts are added.

```
/
├─ index.html          # landing page
├─ dashboard.html      # weather-style dashboard
├─ css/tokens.css      # tokens from this file
├─ css/styles.css
├─ js/aqi.js           # categories, ranges, icons, skies
├─ js/dashboard.js
├─ data/forecast.json
└─ design.md
```
