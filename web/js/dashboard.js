/**
 * Weather-Style Dashboard Controller
 * Manages reactive UI state, station switching, smooth count-up motion,
 * 24-hour forecast strip rendering, scale bar updates, SVG line chart,
 * Interactive India Leaflet Map (647 stations across 34 States/UTs),
 * and Explainable AI (XAI) diagnostics.
 */

let allStations = [];
let all647Stations = [];
let allStatesSummary = {};
let allForecasts = {};
let currentStationId = "site_162";
let currentModelKey = "lstm"; // "lstm" | "rf" | "xgb" | "baseline"
let activeForecast = null;
let currentPm25Displayed = 0;

// Leaflet map instances & drill-down state layers
let leafletMap = null;
let modalLeafletMap = null;
let stationMarkers = [];
let modalStationMarkers = [];
let activeMapFilter = "all";
let activeModalState = "all";

// Image 2 visual styling tokens (Clean vector boundary polygons)
let indiaStatesGeojson = null;
let mainGeoJsonLayer = null;
let modalGeoJsonLayer = null;
let mainStateLayers = {};
let modalStateLayers = {};
let selectedStateMain = null;
let selectedStateModal = null;

const STATE_STYLE_DEFAULT = {
  fillColor: "#1d4ed8",  // Clean deep royal blue (exact match to Image 2)
  weight: 1.5,
  opacity: 1,
  color: "#93c5fd",      // Crisp light blue border
  fillOpacity: 0.92
};

const STATE_STYLE_HOVER = {
  fillColor: "#3b82f6",  // Vibrant electric blue on hover
  weight: 2.5,
  color: "#ffffff",      // White boundary highlight
  fillOpacity: 0.98
};

const STATE_STYLE_SELECTED = {
  fillColor: "#1e3a8a",  // Saturated royal navy
  weight: 3.0,
  color: "#38bdf8",      // Cyan glowing outline
  fillOpacity: 0.95
};

const STATE_STYLE_DIMMED = {
  fillColor: "#0f172a",
  weight: 1.0,
  color: "#334155",
  fillOpacity: 0.4
};

document.addEventListener("DOMContentLoaded", async () => {
  setupIcons();
  setupEventListeners();
  await loadData();
  renderDashboard();
});

/**
 * Injects Lucide SVGs into designated markup containers
 */
function setupIcons() {
  const setIcon = (id, iconName, size = 18) => {
    const el = document.getElementById(id);
    if (el) el.innerHTML = getLucideIcon(iconName, size);
  };

  setIcon("navBrandIcon", "wind", 20);
  setIcon("pinIcon", "map-pin", 15);
  setIcon("chevronDownIcon", "chevron-down", 13);
  setIcon("pillSparkleIcon", "sparkles", 13);
  setIcon("modalMapPinIcon", "map-pin", 22);
  setIcon("tabSunIcon", "sun", 15);
  setIcon("tabMapIcon", "map-pin", 15);
  setIcon("tabBrainIcon", "sparkles", 15);
  setIcon("modalXaiIcon", "sparkles", 22);

  setIcon("clockIcon", "clock", 15);
  setIcon("tileClockIcon", "clock", 16);
  setIcon("tileRiskIcon", "triangle-alert", 16);
  setIcon("tileWindIcon", "wind", 16);
  setIcon("tileTempIcon", "thermometer", 16);
  setIcon("tileDropletIcon", "droplets", 16);
  setIcon("tileGaugeIcon", "gauge", 16);
}

/**
 * Event bindings for modal, model select, tabs, XAI drawer, search
 */
function setupEventListeners() {
  // Station Modal
  const modal = document.getElementById("stationModal");
  const openBtn = document.getElementById("openStationModalBtn");
  const closeBtn = document.getElementById("closeStationModalBtn");
  const modelSelect = document.getElementById("modelSelect");

  if (openBtn) {
    openBtn.addEventListener("click", () => {
      modal.classList.add("open");
      openBtn.setAttribute("aria-expanded", "true");
      initOrResizeModalMap();
    });
  }

  if (closeBtn) {
    closeBtn.addEventListener("click", () => {
      modal.classList.remove("open");
      openBtn.setAttribute("aria-expanded", "false");
    });
  }

  // XAI Modal
  const xaiModal = document.getElementById("xaiModal");
  const closeXaiBtn = document.getElementById("closeXaiModalBtn");

  if (closeXaiBtn) {
    closeXaiBtn.addEventListener("click", () => {
      xaiModal.classList.remove("open");
    });
  }

  // Close modals on background click or Esc
  window.addEventListener("click", (e) => {
    if (e.target === modal) {
      modal.classList.remove("open");
      openBtn.setAttribute("aria-expanded", "false");
    }
    if (e.target === xaiModal) {
      xaiModal.classList.remove("open");
    }
  });

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      modal.classList.remove("open");
      xaiModal.classList.remove("open");
      if (openBtn) openBtn.setAttribute("aria-expanded", "false");
    }
  });

  if (modelSelect) {
    modelSelect.addEventListener("change", (e) => {
      currentModelKey = e.target.value;
      renderDashboard();
    });
  }

  // View Switcher Tabs
  const tabWeather = document.getElementById("tabWeatherBtn");
  const tabMap = document.getElementById("tabMapBtn");
  const tabExplain = document.getElementById("tabExplainBtn");

  const weatherSection = document.getElementById("weatherViewSection");
  const mapSection = document.getElementById("mapViewSection");

  if (tabWeather && tabMap && tabExplain) {
    tabWeather.addEventListener("click", () => {
      tabWeather.classList.add("active");
      tabMap.classList.remove("active");
      tabExplain.classList.remove("active");
      weatherSection.style.display = "grid";
      mapSection.style.display = "none";
    });

    tabMap.addEventListener("click", () => {
      tabMap.classList.add("active");
      tabWeather.classList.remove("active");
      tabExplain.classList.remove("active");
      weatherSection.style.display = "none";
      mapSection.style.display = "block";
      initOrResizeLeafletMap();
    });

    tabExplain.addEventListener("click", () => {
      renderXaiModal();
      xaiModal.classList.add("open");
    });
  }

  // Map Filter Buttons (Filter by AQI Category)
  const filterPills = document.querySelectorAll("#mapFilterPills button");
  filterPills.forEach(pill => {
    pill.addEventListener("click", () => {
      activeMapFilter = pill.getAttribute("data-filter");
      filterPills.forEach(p => p.style.opacity = "0.7");
      pill.style.opacity = "1.0";
      applyMapFilters();
    });
  });

  // "← All India States" Navigation Buttons (Reset Map to Image 2 State Outline View)
  const mapResetBtn = document.getElementById("mapResetBtn");
  if (mapResetBtn) {
    mapResetBtn.addEventListener("click", () => {
      resetMapToAllIndia(leafletMap, stationMarkers, false);
    });
  }

  const modalMapResetBtn = document.getElementById("modalMapResetBtn");
  if (modalMapResetBtn) {
    modalMapResetBtn.addEventListener("click", () => {
      resetMapToAllIndia(modalLeafletMap, modalStationMarkers, true);
    });
  }

  // Main Standalone Map State & Search Inputs
  const mainStateSelect = document.getElementById("mainStateSelect");
  if (mainStateSelect) {
    mainStateSelect.addEventListener("change", (e) => {
      const state = e.target.value;
      if (state === "all") {
        resetMapToAllIndia(leafletMap, stationMarkers, false);
      } else {
        const layer = mainStateLayers[state];
        if (layer) {
          drillIntoState(state, layer, leafletMap, stationMarkers, false);
        } else {
          zoomMapToState(leafletMap, state);
          renderStationsForState(leafletMap, stationMarkers, state, false);
        }
      }
    });
  }

  const searchInput = document.getElementById("mapSearchInput");
  if (searchInput) {
    searchInput.addEventListener("input", (e) => {
      applyMapFilters(e.target.value.toLowerCase().trim());
    });
  }

  // Modal State Dropdown & Search Input
  const modalStateSelect = document.getElementById("modalStateSelect");
  if (modalStateSelect) {
    modalStateSelect.addEventListener("change", (e) => {
      const state = e.target.value;
      activeModalState = state;
      if (state === "all") {
        resetMapToAllIndia(modalLeafletMap, modalStationMarkers, true);
      } else {
        const layer = modalStateLayers[state];
        if (layer) {
          drillIntoState(state, layer, modalLeafletMap, modalStationMarkers, true);
        } else {
          zoomMapToState(modalLeafletMap, state);
          renderStationsForState(modalLeafletMap, modalStationMarkers, state, true);
        }
      }
      renderModalStationList();
    });
  }

  const modalSearchInput = document.getElementById("modalSearchInput");
  if (modalSearchInput) {
    modalSearchInput.addEventListener("input", (e) => {
      const query = e.target.value.toLowerCase().trim();
      renderModalStationList(query);
      applyModalMapFilters(query);
    });
  }

  // Set current date
  const dateEl = document.getElementById("currentDateDisplay");
  if (dateEl) {
    const now = new Date();
    dateEl.textContent = now.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
  }
}

/**
 * Ingests stations, all 647 geolocations, state centroids, and forecasts metadata
 */
async function loadData() {
  try {
    const [stRes, geoRes, statesRes, fcRes, indiaGeoRes] = await Promise.all([
      fetch("data/stations.json"),
      fetch("data/all_stations_geo.json"),
      fetch("data/states_summary.json"),
      fetch("data/forecasts.json"),
      fetch("data/india_states_simplified.geojson")
    ]);

    if (stRes.ok && fcRes.ok) {
      allStations = await stRes.json();
      allForecasts = await fcRes.json();
    }
    if (geoRes.ok) {
      all647Stations = await geoRes.json();
    }
    if (statesRes.ok) {
      allStatesSummary = await statesRes.json();
    }
    if (indiaGeoRes && indiaGeoRes.ok) {
      indiaStatesGeojson = await indiaGeoRes.json();
    }
  } catch (err) {
    console.warn("Using inline fallback data:", err);
    useFallbackData();
  }

  populateStateDropdowns();
  renderModalStationList();
}

/**
 * Populates State selection dropdowns for all 34 Indian States & UTs
 */
function populateStateDropdowns() {
  const modalSelect = document.getElementById("modalStateSelect");
  const mainSelect = document.getElementById("mainStateSelect");
  if (!modalSelect && !mainSelect) return;

  // Sort states by station count descending
  const sortedStates = Object.keys(allStatesSummary).sort((a, b) => {
    return allStatesSummary[b].count - allStatesSummary[a].count;
  });

  const generateOptionsHtml = () => {
    let html = `<option value="all">🇮🇳 All India (All 647 Stations)</option>`;
    sortedStates.forEach(st => {
      if (st && st !== 'None' && st !== 'Unknown' && st !== 'Other') {
        const cnt = allStatesSummary[st].count;
        html += `<option value="${st}">${st} (${cnt} station${cnt > 1 ? 's' : ''})</option>`;
      }
    });
    return html;
  };

  const options = generateOptionsHtml();
  if (modalSelect) modalSelect.innerHTML = options;
  if (mainSelect) mainSelect.innerHTML = options;
}

/**
 * Populates station list in the modal based on selected state and search query
 */
function renderModalStationList(searchQuery = "") {
  const container = document.getElementById("stationListContainer");
  const headerEl = document.getElementById("modalListHeader");
  const countEl = document.getElementById("modalMatchingCount");
  if (!container) return;

  container.innerHTML = "";

  let list = all647Stations;
  if (activeModalState !== "all") {
    list = list.filter(s => s.state === activeModalState);
  }

  if (searchQuery) {
    list = list.filter(s => 
      (s.name && s.name.toLowerCase().includes(searchQuery)) ||
      (s.city && s.city.toLowerCase().includes(searchQuery)) ||
      (s.state && s.state.toLowerCase().includes(searchQuery))
    );
  }

  if (headerEl) {
    headerEl.textContent = activeModalState === "all" ? "All Monitoring Stations" : `Stations in ${activeModalState}`;
  }
  if (countEl) {
    countEl.textContent = `${list.length} station${list.length !== 1 ? 's' : ''}`;
  }

  list.forEach(st => {
    const item = document.createElement("div");
    item.className = `station-item ${st.id === currentStationId ? "active" : ""}`;
    item.setAttribute("role", "button");
    item.setAttribute("tabindex", "0");

    const badgeHtml = st.has_trained_model 
      ? `<span class="notice-pill model-active" style="font-size: 10px; padding: 2px 8px;">Trained ML</span>`
      : `<span style="background: ${st.color || '#3FA796'}; color: #fff; font-size: 10px; font-weight: 700; padding: 2px 7px; border-radius: 999px;">${st.category || 'Good'}</span>`;

    item.innerHTML = `
      <div style="flex: 1; min-width: 0;">
        <div style="font-weight: 600; font-size: 13px; color: #fff; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${st.name}</div>
        <div style="font-size: 11px; color: var(--text-soft);">${st.city || ''} • ${st.state || ''}</div>
      </div>
      <div style="text-align: right; margin-left: 8px;">
        <div style="font-weight: 700; font-size: 14px; color: #fff;">${st.pm25 || 23} <span style="font-size: 10px; font-weight: 400; opacity: 0.8;">µg/m³</span></div>
        <div style="margin-top: 2px;">${badgeHtml}</div>
      </div>
    `;

    item.addEventListener("click", () => {
      selectStation(st.id);
      document.getElementById("stationModal").classList.remove("open");
      document.getElementById("openStationModalBtn").setAttribute("aria-expanded", "false");
    });

    item.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") {
        item.click();
      }
    });

    container.appendChild(item);
  });
}

function selectStation(stationId) {
  currentStationId = stationId;

  // If station is not in allForecasts, generate synthesized realistic forecast
  if (!allForecasts[stationId]) {
    const stMeta = all647Stations.find(s => s.id === stationId) || { name: stationId, city: "India", state: "India", pm25: 25 };
    const baseVal = stMeta.pm25 || 25;
    
    const syntheticHourly = [];
    for (let h = 1; h <= 24; h++) {
      const diurnalOscillation = Math.sin((h - 6) / 24 * 2 * Math.PI) * 8;
      const pm = Math.max(8, Math.round((baseVal + diurnalOscillation + (h % 4) * 2) * 10) / 10);
      syntheticHourly.push({
        hour: h,
        time: `${h < 10 ? '0' + h : h}:00`,
        pm25: pm,
        baseline: Math.max(8, Math.round((baseVal + diurnalOscillation * 0.7) * 10) / 10),
        rf: pm,
        xgb: pm,
        lstm: pm,
        xai_attributions: [
          { feature: "Regional Particulate Advection", delta: roundVal(diurnalOscillation * 0.5), type: "regional", desc: "Regional baseline concentration in " + stMeta.city },
          { feature: "Diurnal Boundary Layer Modulation", delta: roundVal(diurnalOscillation * 0.3), type: "meteorology", desc: "Nocturnal cooling compression vs daytime solar mixing" },
          { feature: "Advective Wind Dispersion", delta: roundVal(-2.1), type: "dispersion", desc: "Horizontal wind ventilation velocity" },
          { feature: "Chemical Precursor Reaction (NH3/NO2)", delta: roundVal(1.8), type: "chemistry", desc: "Secondary aerosol conversion rate" }
        ]
      });
    }

    allForecasts[stationId] = {
      station_id: stationId,
      station: stMeta.name,
      mode: "sample",
      hourly: syntheticHourly,
      conditions: {
        wind_speed: 2.1,
        wind_direction: 135,
        temp: 24,
        dew_point: 15,
        humidity: 60,
        pressure: 915,
        solar_radiation: 400,
        rainfall: 0.0
      },
      pollutants: {
        pm10: Math.round(baseVal * 1.8),
        nh3: Math.round(baseVal * 0.4),
        no2: Math.round(baseVal * 0.5),
        so2: Math.round(baseVal * 0.2),
        co: 0.8,
        o3: 28,
        nox: Math.round(baseVal * 0.7),
        benzene: 1.8
      }
    };
  }

  renderModalStationList();
  renderDashboard();

  // If in map mode, switch back to forecast
  const tabWeather = document.getElementById("tabWeatherBtn");
  const tabMap = document.getElementById("tabMapBtn");
  const weatherSection = document.getElementById("weatherViewSection");
  const mapSection = document.getElementById("mapViewSection");

  if (tabWeather && tabMap && mapSection.style.display === "block") {
    tabWeather.classList.add("active");
    tabMap.classList.remove("active");
    weatherSection.style.display = "grid";
    mapSection.style.display = "none";
  }
}

function roundVal(v) {
  return Math.round(v * 10) / 10;
}

/**
 * Main render function for all dashboard components
 */
function renderDashboard() {
  const forecast = allForecasts[currentStationId] || allForecasts["site_162"];
  activeForecast = forecast;

  const stationMeta = all647Stations.find(s => s.id === currentStationId) || 
                      allStations.find(s => s.id === currentStationId) || {
    name: forecast.station,
    state: "Karnataka",
    mode: forecast.mode
  };

  // 1. Update station label, state badge & notice pill
  document.getElementById("selectedStationName").textContent = stationMeta.name;
  
  const stateBadge = document.getElementById("selectedStationStateBadge");
  if (stateBadge) {
    stateBadge.textContent = stationMeta.state || "India";
  }
  
  const pillEl = document.getElementById("modeNoticePill");
  const pillText = document.getElementById("modeNoticeText");
  const modelSelectorGroup = document.getElementById("modelSelectorGroup");

  if (forecast.mode === "model") {
    pillEl.className = "notice-pill model-active";
    pillText.textContent = "Trained Model";
    modelSelectorGroup.style.display = "flex";
  } else {
    pillEl.className = "notice-pill";
    pillText.textContent = "Proposed Design | Sample Data";
    modelSelectorGroup.style.display = "none";
  }

  // 2. Compute effective 24h hourly values based on selected model
  const effectiveHourly = forecast.hourly.map((h, idx) => {
    let val = h.pm25;
    if (forecast.mode === "model") {
      if (currentModelKey === "rf" && h.rf !== undefined) val = h.rf;
      else if (currentModelKey === "xgb" && h.xgb !== undefined) val = h.xgb;
      else if (currentModelKey === "baseline" && h.baseline !== undefined) val = h.baseline;
      else if (currentModelKey === "lstm" && h.pm25 !== undefined) val = h.pm25;
    }
    return {
      hourIndex: idx,
      hourNum: h.hour,
      time: h.time,
      pm25: val,
      baseline: h.baseline,
      xai_attributions: h.xai_attributions
    };
  });

  // 3. Advisory calculations
  const advisoryInfo = computeHourlyAdvisory(effectiveHourly);

  // 4. Hero section & Current Value
  const currentVal = effectiveHourly[0].pm25;
  const currentCategory = getAqiCategory(currentVal);

  // Crossfade Sky
  const skyViewport = document.getElementById("skyViewport");
  const currentHour = new Date().getHours();
  skyViewport.style.background = isNightHour(currentHour) ? SKY_NIGHT : currentCategory.skyGradient;

  // Animate Hero Number Count-Up
  animateCount("heroPm25Number", currentPm25Displayed, currentVal, 600);
  currentPm25Displayed = currentVal;

  // Hero Condition & Icon
  document.getElementById("heroConditionIcon").innerHTML = getLucideIcon(currentCategory.icon, 44);
  document.getElementById("heroConditionWord").textContent = currentCategory.name;
  document.getElementById("heroConditionWord").style.color = "#FFFFFF";

  document.getElementById("heroHlValues").innerHTML = `H: ${advisoryInfo.high} &nbsp;•&nbsp; L: ${advisoryInfo.low}`;
  document.getElementById("heroAdvisoryLine").textContent = advisoryInfo.advisorySentence;

  // 5. Render 24-Hour Strip
  renderHourlyStrip(effectiveHourly, advisoryInfo);

  // 6. Render CPCB Scale Bar
  renderScaleBar(currentVal, currentCategory);

  // 7. Render 6 Detail Tiles (Enhanced with Meteorology)
  renderDetailTiles(forecast, advisoryInfo);

  // 8. Render Chemical Precursors & Pollutants
  renderPollutants(forecast.pollutants);

  // 9. Render Model vs Baseline SVG Line Chart
  renderSvgChart(effectiveHourly);
}

/**
 * Animated number count-up for hero
 */
function animateCount(elemId, startVal, endVal, durationMs = 600) {
  const el = document.getElementById(elemId);
  if (!el) return;

  const prefersReduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (prefersReduced) {
    el.textContent = Math.round(endVal);
    return;
  }

  const startTime = performance.now();
  const diff = endVal - startVal;

  function update(now) {
    const elapsed = now - startTime;
    const progress = Math.min(elapsed / durationMs, 1);
    const ease = 1 - Math.pow(1 - progress, 3);
    const current = Math.round(startVal + diff * ease);
    el.textContent = current;

    if (progress < 1) {
      requestAnimationFrame(update);
    } else {
      el.textContent = Math.round(endVal);
    }
  }

  requestAnimationFrame(update);
}

/**
 * 24-Hour horizontal forecast strip
 */
function renderHourlyStrip(hourlyList, advisoryInfo) {
  const container = document.getElementById("hourlyStripScroll");
  if (!container) return;

  container.innerHTML = "";
  const maxValInSeries = Math.max(...hourlyList.map(h => h.pm25), 50);

  hourlyList.forEach((item, idx) => {
    const cat = getAqiCategory(item.pm25);
    const cell = document.createElement("div");
    cell.className = "hour-cell";

    if (advisoryInfo.bestIndices.has(idx)) {
      cell.classList.add("best-window");
    }
    if (advisoryInfo.peakIndices.has(idx) && idx === advisoryInfo.peakIndices.values().next().value) {
      cell.classList.add("peak-risk");
    }

    const heightPct = Math.min(Math.max((item.pm25 / maxValInSeries) * 100, 12), 100);
    const timeLabel = formatHourDisplay(idx, idx === 0);

    cell.innerHTML = `
      <div class="hour-time">${timeLabel}</div>
      <div class="hour-icon" style="color: ${cat.color}">${getLucideIcon(cat.icon, 20)}</div>
      <div class="hour-bar-wrap">
        <div class="hour-bar-fill" style="height: ${heightPct}%; background-color: ${cat.color};"></div>
      </div>
      <div class="hour-val">${Math.round(item.pm25)}</div>
    `;

    cell.setAttribute("title", `${timeLabel}: ${item.pm25} µg/m³ (${cat.name}) — Click to view XAI attribution`);
    
    cell.addEventListener("click", () => {
      renderXaiModal(idx);
      document.getElementById("xaiModal").classList.add("open");
    });

    container.appendChild(cell);
  });
}

/**
 * CPCB AQI Scale Bar position update
 */
function renderScaleBar(currentVal, currentCat) {
  const marker = document.getElementById("scaleMarker");
  const label = document.getElementById("scaleCurrentLabel");
  if (!marker) return;

  const maxScale = 250;
  const pct = Math.min(Math.max((currentVal / maxScale) * 100, 2), 98);
  marker.style.left = `${pct}%`;

  if (label) {
    label.textContent = `${currentCat.name} (${Math.round(currentVal)} µg/m³)`;
    label.style.color = currentCat.color;
  }
}

/**
 * Updates the 6 Detail Tiles with Comprehensive Meteorology
 */
function renderDetailTiles(forecast, advisoryInfo) {
  const cond = forecast.conditions || {};
  
  document.getElementById("tileBestWindow").textContent = advisoryInfo.bestWindow;
  document.getElementById("tilePeakRisk").textContent = advisoryInfo.peakRisk;
  
  document.getElementById("tileWindSpeed").innerHTML = `${cond.wind_speed || 2.4} <span style="font-size: 14px; font-weight: 400;">m/s</span>`;
  const windDir = cond.wind_direction !== undefined ? `${cond.wind_direction}°` : '142° (SE)';
  const windSub = document.getElementById("tileWindDir");
  if (windSub) windSub.textContent = `Wind Dir: ${windDir}`;

  document.getElementById("tileTemperature").innerHTML = `${cond.temp || 24.2} <span style="font-size: 14px; font-weight: 400;">°C</span>`;
  const rainSub = document.getElementById("tileRainfall");
  if (rainSub) rainSub.textContent = `Rainfall: ${cond.rainfall || 0.0} mm (${cond.rainfall > 0 ? 'Washout' : 'Dry Day'})`;

  document.getElementById("tileHumidity").innerHTML = `${cond.humidity || 62} <span style="font-size: 14px; font-weight: 400;">%</span>`;
  document.getElementById("tileDewPoint").textContent = `Dew point ${cond.dew_point || 15.1}°C`;

  document.getElementById("tilePressure").innerHTML = `${cond.pressure || 915} <span style="font-size: 14px; font-weight: 400;">hPa</span>`;
  const solarSub = document.getElementById("tileSolar");
  if (solarSub) solarSub.textContent = `Solar: ${cond.solar_radiation || 420} W/m²`;
}

/**
 * High-Impact Chemical Precursor Progress Rows
 */
function renderPollutants(pollutants = {}) {
  const container = document.getElementById("pollutantsList");
  if (!container) return;

  const pollutantConfigs = [
    { key: "pm10", name: "PM10", unit: "µg/m³", maxRef: 150, desc: "Coarse particulate matter" },
    { key: "nh3", name: "NH₃ (Ammonia)", unit: "µg/m³", maxRef: 100, desc: "Key chemical precursor to secondary ammonium aerosol" },
    { key: "no2", name: "NO₂", unit: "µg/m³", maxRef: 80, desc: "Diesel combustion byproduct & nitrate precursor" },
    { key: "so2", name: "SO₂", unit: "µg/m³", maxRef: 80, desc: "Industrial sulfur aerosol precursor" },
    { key: "co", name: "CO", unit: "mg/m³", maxRef: 4.0, desc: "Incomplete vehicular carbon combustion" },
    { key: "o3", name: "Ozone", unit: "µg/m³", maxRef: 120, desc: "Secondary photochemical ground oxidant" },
    { key: "nox", name: "NOx", unit: "ppb", maxRef: 80, desc: "Total nitrogen oxides precursor volume" },
    { key: "benzene", name: "Benzene", unit: "µg/m³", maxRef: 5.0, desc: "Volatile aromatic hydrocarbon (VOC)" }
  ];

  container.innerHTML = "";

  pollutantConfigs.forEach(item => {
    const val = pollutants[item.key] !== undefined ? pollutants[item.key] : (item.key === 'nh3' ? 18.4 : 25.0);
    const pct = Math.min((val / item.maxRef) * 100, 100);
    const color = pct < 40 ? "#3FA796" : pct < 75 ? "#E8A317" : "#D1495B";

    const row = document.createElement("div");
    row.className = "pollutant-row";
    row.innerHTML = `
      <div style="flex: 0 0 160px; min-width: 0;">
        <span class="pollutant-name" style="width: auto; font-size: 13px;">${item.name}</span>
        <div style="font-size: 10px; color: var(--text-faint); white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${item.desc}</div>
      </div>
      <div class="pollutant-bar-track" style="margin: 0 12px;">
        <div class="pollutant-bar-fill" style="width: ${pct}%; background-color: ${color};"></div>
      </div>
      <span class="pollutant-val" style="width: 70px; text-align: right; font-size: 13px;">${val} <span style="font-size: 10px; font-weight: 400; color: var(--text-soft);">${item.unit}</span></span>
    `;
    container.appendChild(row);
  });
}

/**
 * Renders SVG line chart for Model vs Baseline
 */
function renderSvgChart(hourlyList) {
  const svg = document.getElementById("forecastSvgChart");
  if (!svg || hourlyList.length === 0) return;

  const width = 460;
  const height = 180;
  const padLeft = 32;
  const padRight = 16;
  const padTop = 16;
  const padBottom = 28;

  const plotWidth = width - padLeft - padRight;
  const plotHeight = height - padTop - padBottom;

  const allVals = [
    ...hourlyList.map(h => h.pm25),
    ...hourlyList.map(h => h.baseline)
  ];
  const minVal = Math.max(0, Math.min(...allVals) - 5);
  const maxVal = Math.max(...allVals) + 8;
  const valRange = maxVal - minVal || 1;

  const getX = (i) => padLeft + (i / (hourlyList.length - 1)) * plotWidth;
  const getY = (val) => padTop + plotHeight - ((val - minVal) / valRange) * plotHeight;

  let modelPath = "";
  let baselinePath = "";

  hourlyList.forEach((h, i) => {
    const x = getX(i);
    const yModel = getY(h.pm25);
    const yBase = getY(h.baseline);

    if (i === 0) {
      modelPath += `M ${x.toFixed(1)} ${yModel.toFixed(1)}`;
      baselinePath += `M ${x.toFixed(1)} ${yBase.toFixed(1)}`;
    } else {
      modelPath += ` L ${x.toFixed(1)} ${yModel.toFixed(1)}`;
      baselinePath += ` L ${x.toFixed(1)} ${yBase.toFixed(1)}`;
    }
  });

  const areaPath = `${modelPath} L ${getX(hourlyList.length - 1)} ${padTop + plotHeight} L ${getX(0)} ${padTop + plotHeight} Z`;

  let gridLines = "";
  const gridSteps = 3;
  for (let s = 0; s <= gridSteps; s++) {
    const val = minVal + (s / gridSteps) * valRange;
    const y = getY(val);
    gridLines += `
      <line x1="${padLeft}" y1="${y}" x2="${width - padRight}" y2="${y}" stroke="rgba(255,255,255,0.12)" stroke-width="1" />
      <text x="${padLeft - 6}" y="${y + 4}" fill="rgba(255,255,255,0.5)" font-size="9" text-anchor="end">${Math.round(val)}</text>
    `;
  }

  let xLabels = "";
  const xStep = 6;
  for (let i = 0; i < hourlyList.length; i += xStep) {
    const x = getX(i);
    const label = `+${i + 1}h`;
    xLabels += `<text x="${x}" y="${height - 8}" fill="rgba(255,255,255,0.6)" font-size="10" text-anchor="middle">${label}</text>`;
  }

  svg.innerHTML = `
    <defs>
      <linearGradient id="chartModelGradient" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="#38bdf8" stop-opacity="0.45"/>
        <stop offset="100%" stop-color="#38bdf8" stop-opacity="0.0"/>
      </linearGradient>
    </defs>
    
    ${gridLines}
    ${xLabels}

    <path d="${areaPath}" fill="url(#chartModelGradient)"/>
    <path d="${baselinePath}" fill="none" stroke="rgba(255,255,255,0.4)" stroke-width="2" stroke-dasharray="4 3" stroke-linecap="round"/>
    <path d="${modelPath}" fill="none" stroke="#38bdf8" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
  `;
}

/**
 * =========================================================================
 * TWO-TIER STATE DRILL-DOWN INDIA MAP ENGINE (IMAGE 2 VECTOR ARCHITECTURE)
 * =========================================================================
 * Level 1 (All India): Shaped in the form of Indian state boundaries (clean blue fill,
 *                      crisp borders, ZERO scattered points, NO tile watermarks).
 * Level 2 (State Drill-down): Clicking any state zooms in, reveals the station
 *                            monitoring pins strictly in that state, and allows
 *                            selecting a station to predict tomorrow's air.
 * =========================================================================
 */

function initOrResizeLeafletMap() {
  if (typeof L === "undefined") return;

  const mapContainer = document.getElementById("indiaMap");
  if (!mapContainer) return;

  if (!leafletMap) {
    leafletMap = L.map("indiaMap", {
      center: [22.5, 82.0],
      zoom: 4.8,
      minZoom: 4,
      maxZoom: 12,
      zoomSnap: 0.2,
      zoomControl: true,
      attributionControl: false
    });

    // Custom non-intrusive metadata attribution in corner
    L.control.attribution({ position: "bottomright" })
      .addAttribution("CPCB &bull; XKDR India Air Quality Monitoring Network (647 Stations)")
      .addTo(leafletMap);
  }

  setTimeout(() => {
    leafletMap.invalidateSize();
    if (indiaStatesGeojson && !mainGeoJsonLayer) {
      mainGeoJsonLayer = buildIndiaStateGeoJsonLayer(leafletMap, stationMarkers, false);
    }
  }, 200);
}

function initOrResizeModalMap() {
  if (typeof L === "undefined") return;

  const mapContainer = document.getElementById("modalMapContainer");
  if (!mapContainer) return;

  if (!modalLeafletMap) {
    modalLeafletMap = L.map("modalMapContainer", {
      center: [22.5, 82.0],
      zoom: 4.2,
      minZoom: 3.5,
      maxZoom: 12,
      zoomSnap: 0.2,
      zoomControl: true,
      attributionControl: false
    });
  }

  setTimeout(() => {
    modalLeafletMap.invalidateSize();
    if (indiaStatesGeojson && !modalGeoJsonLayer) {
      modalGeoJsonLayer = buildIndiaStateGeoJsonLayer(modalLeafletMap, modalStationMarkers, true);
    }
  }, 250);
}

/**
 * Builds the clean India State boundary GeoJSON polygon layer matching Image 2
 */
function buildIndiaStateGeoJsonLayer(mapInstance, markerArray, isModal) {
  if (!indiaStatesGeojson || !mapInstance) return null;

  const layersStorage = isModal ? modalStateLayers : mainStateLayers;
  // Clear any existing stored layers
  Object.keys(layersStorage).forEach(k => delete layersStorage[k]);

  const layerGroup = L.geoJSON(indiaStatesGeojson, {
    style: () => STATE_STYLE_DEFAULT,
    onEachFeature: (feature, layer) => {
      const stateName = feature.properties.name || feature.properties.NAME_1;
      const count = feature.properties.station_count || 0;
      const avg = feature.properties.avg_pm25 || 35;
      
      layersStorage[stateName] = layer;

      // Clean glass tooltip on hover
      layer.bindTooltip(`
        <div style="font-weight: 700; font-size: 13px; color: #fff;">${stateName}</div>
        <div style="font-size: 11px; color: #93c5fd; margin-top: 2px;">${count} Monitoring Station${count !== 1 ? 's' : ''}</div>
        <div style="font-size: 10px; color: #cbd5e1; margin-top: 2px;">Avg PM₂.₅: ${Math.round(avg)} µg/m³ &bull; Click to reveal stations &rarr;</div>
      `, {
        className: 'leaflet-tooltip-state',
        sticky: true
      });

      // Interactive hover & click
      layer.on({
        mouseover: (e) => {
          const activeState = isModal ? selectedStateModal : selectedStateMain;
          if (activeState !== stateName) {
            e.target.setStyle(STATE_STYLE_HOVER);
            if (!L.Browser.ie && !L.Browser.opera && !L.Browser.edge) {
              e.target.bringToFront();
            }
          }
        },
        mouseout: (e) => {
          const activeState = isModal ? selectedStateModal : selectedStateMain;
          if (activeState !== stateName) {
            if (activeState) {
              e.target.setStyle(STATE_STYLE_DIMMED);
            } else {
              e.target.setStyle(STATE_STYLE_DEFAULT);
            }
          }
        },
        click: () => {
          drillIntoState(stateName, layer, mapInstance, markerArray, isModal);
        }
      });
    }
  }).addTo(mapInstance);

  return layerGroup;
}

/**
 * Drills into a clicked state: zooms to boundaries, dims surrounding states,
 * and reveals the station pins belonging to this state.
 */
function drillIntoState(stateName, layer, mapInstance, markerArray, isModal) {
  if (!mapInstance) return;

  if (isModal) {
    selectedStateModal = stateName;
    activeModalState = stateName;
  } else {
    selectedStateMain = stateName;
  }

  // 1. Zoom smoothly to state polygon bounds
  if (layer && layer.getBounds) {
    mapInstance.fitBounds(layer.getBounds(), { padding: [35, 35], maxZoom: 9 });
  } else {
    zoomMapToState(mapInstance, stateName);
  }

  // 2. Highlight clicked state polygon; dim all others
  const layersMap = isModal ? modalStateLayers : mainStateLayers;
  Object.keys(layersMap).forEach(k => {
    const l = layersMap[k];
    if (k === stateName) {
      l.setStyle(STATE_STYLE_SELECTED);
      if (l.bringToFront) l.bringToFront();
    } else {
      l.setStyle(STATE_STYLE_DIMMED);
    }
  });

  // 3. Render station pins strictly inside this state
  renderStationsForState(mapInstance, markerArray, stateName, isModal);

  // 4. Update UI: show Reset Button & State Active Badge
  const resetBtn = document.getElementById(isModal ? "modalMapResetBtn" : "mapResetBtn");
  const stateBadge = document.getElementById(isModal ? "modalMapStateActiveBadge" : "mapStateActiveBadge");
  const stateBadgeText = document.getElementById(isModal ? "modalMapStateActiveBadgeText" : "mapStateActiveBadgeText");
  const instructionPill = document.getElementById(isModal ? "modalMapInstructionPill" : "mapInstructionPill");

  if (resetBtn) resetBtn.style.display = "inline-flex";
  if (stateBadge) stateBadge.style.display = "block";
  if (instructionPill) instructionPill.style.display = "none";

  const stateStations = getStationsForStateName(stateName);
  if (stateBadgeText) {
    stateBadgeText.textContent = `${stateName} (${stateStations.length} Stations)`;
  }

  // 5. Update dropdowns
  const selectEl = document.getElementById(isModal ? "modalStateSelect" : "mainStateSelect");
  if (selectEl) selectEl.value = stateName;

  // 6. Update counts & modal list
  if (!isModal) {
    const countEl = document.getElementById("mapStationCount");
    if (countEl) countEl.textContent = stateStations.length;
  } else {
    renderModalStationList();
  }
}

/**
 * Resets the map back to All India (Image 2 clean blue state outlines, 0 station pins)
 */
function resetMapToAllIndia(mapInstance, markerArray, isModal) {
  if (!mapInstance) return;

  if (isModal) {
    selectedStateModal = null;
    activeModalState = "all";
  } else {
    selectedStateMain = null;
  }

  // 1. Clear station markers (hide points)
  markerArray.forEach(m => mapInstance.removeLayer(m));
  markerArray.length = 0;

  // 2. Reset all state polygons back to Image 2 style
  const layersMap = isModal ? modalStateLayers : mainStateLayers;
  Object.values(layersMap).forEach(l => {
    l.setStyle(STATE_STYLE_DEFAULT);
  });

  // 3. Reset view to All India
  mapInstance.setView([22.5, 82.0], isModal ? 4.2 : 4.8);

  // 4. Update UI: hide Reset Button & Active Badge, show Instruction Pill
  const resetBtn = document.getElementById(isModal ? "modalMapResetBtn" : "mapResetBtn");
  const stateBadge = document.getElementById(isModal ? "modalMapStateActiveBadge" : "mapStateActiveBadge");
  const instructionPill = document.getElementById(isModal ? "modalMapInstructionPill" : "mapInstructionPill");

  if (resetBtn) resetBtn.style.display = "none";
  if (stateBadge) stateBadge.style.display = "none";
  if (instructionPill) instructionPill.style.display = "block";

  // 5. Reset dropdown
  const selectEl = document.getElementById(isModal ? "modalStateSelect" : "mainStateSelect");
  if (selectEl) selectEl.value = "all";

  // 6. Reset counts
  if (!isModal) {
    const countEl = document.getElementById("mapStationCount");
    if (countEl) countEl.textContent = all647Stations.length;
  } else {
    renderModalStationList();
  }
}

function getStationsForStateName(stateName) {
  if (stateName === "Jammu and Kashmir" || stateName === "Ladakh") {
    return all647Stations.filter(s => s.state === "Jammu and Kashmir" || s.state === "Ladakh");
  }
  return all647Stations.filter(s => s.state === stateName);
}

/**
 * Renders the station markers for a specific state once it has been clicked
 */
function renderStationsForState(mapInstance, markerArray, stateName, isModal) {
  if (!mapInstance) return;

  // Clear existing markers
  markerArray.forEach(m => mapInstance.removeLayer(m));
  markerArray.length = 0;

  let matching = getStationsForStateName(stateName);
  if (!isModal && activeMapFilter !== "all") {
    matching = matching.filter(s => s.category === activeMapFilter);
  }

  matching.forEach(st => {
    if (!st.lat || !st.lon) return;

    const isCurrent = st.id === currentStationId;
    const marker = L.circleMarker([st.lat, st.lon], {
      radius: isCurrent ? 10 : 7,
      fillColor: st.color || '#3FA796',
      color: '#FFFFFF',
      weight: isCurrent ? 2.5 : 1.8,
      opacity: 1,
      fillOpacity: 0.95
    });

    const popupContent = `
      <div style="min-width: 230px;">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 6px;">
          <div>
            <div style="font-weight: 700; font-size: 14px; color: #fff;">${st.name}</div>
            <div style="font-size: 11px; color: rgba(255,255,255,0.7);">${st.city || ''}, ${st.state || ''}</div>
          </div>
          <span style="background: ${st.color || '#3FA796'}; color: #fff; font-size: 10px; font-weight: 700; padding: 2px 7px; border-radius: 999px;">
            ${st.category || 'Good'}
          </span>
        </div>

        <div style="margin: 8px 0; font-size: 22px; font-weight: 300; color: #fff;">
          ${st.pm25} <span style="font-size: 12px; color: rgba(255,255,255,0.7);">µg/m³ PM₂.₅</span>
        </div>

        <div style="font-size: 11px; color: rgba(255,255,255,0.75); margin-bottom: 10px; line-height: 1.3;">
          Monitored: ${st.parameters ? st.parameters.slice(0, 5).join(', ') + '...' : 'PM2.5, PM10, NO2, SO2'}
        </div>

        <button onclick="window.selectStationFromMap('${st.id}')" style="width: 100%; background: #E8A317; color: #1F2A33; border: none; font-size: 12px; font-weight: 700; padding: 8px 14px; border-radius: 999px; cursor: pointer; transition: transform 0.15s ease;">
          Predict Tomorrow's Air (24h) &rarr;
        </button>
      </div>
    `;

    marker.bindPopup(popupContent);
    marker.stationData = st;

    marker.on("mouseover", () => {
      marker.setRadius(isCurrent ? 13 : 10);
    });
    marker.on("mouseout", () => {
      marker.setRadius(isCurrent ? 10 : 7);
    });

    marker.addTo(mapInstance);
    markerArray.push(marker);
  });

  if (!isModal) {
    const countEl = document.getElementById("mapStationCount");
    if (countEl) countEl.textContent = matching.length;
  }
}

function zoomMapToState(mapInstance, stateName) {
  if (!mapInstance) return;

  if (stateName === "all" || !stateName) {
    mapInstance.setView([22.5, 82.0], 4.8);
    return;
  }

  const stateInfo = allStatesSummary[stateName];
  if (stateInfo && stateInfo.center) {
    const zoomLevel = stateInfo.count > 40 ? 7 : 8;
    mapInstance.flyTo(stateInfo.center, zoomLevel, { duration: 1.2 });
  }
}

/**
 * When a user selects a station from the map popup or station list,
 * update the model predictions and switch back to the Weather Forecast tab
 */
window.selectStationFromMap = function(stationId) {
  selectStation(stationId);
  
  // Close modal if open
  const modal = document.getElementById("stationModal");
  if (modal) modal.classList.remove("open");
  const openBtn = document.getElementById("openStationModalBtn");
  if (openBtn) openBtn.setAttribute("aria-expanded", "false");

  // Automatically switch to Weather Forecast view
  const tabWeather = document.getElementById("tabWeatherBtn");
  const tabMap = document.getElementById("tabMapBtn");
  const weatherSection = document.getElementById("weatherViewSection");
  const mapSection = document.getElementById("mapViewSection");

  if (tabWeather && tabMap && weatherSection && mapSection) {
    tabWeather.classList.add("active");
    tabMap.classList.remove("active");
    weatherSection.style.display = "grid";
    mapSection.style.display = "none";
  }

  // Smooth scroll to top of forecast screen
  window.scrollTo({ top: 0, behavior: "smooth" });
};

function applyMapFilters(searchQuery = "") {
  if (!leafletMap) return;
  const stateVal = document.getElementById("mainStateSelect")?.value || "all";

  // If a state is selected, filter markers within that state
  if (stateVal !== "all" && selectedStateMain) {
    let count = 0;
    stationMarkers.forEach(m => {
      const st = m.stationData;
      const matchesCat = (activeMapFilter === "all" || st.category === activeMapFilter);
      const matchesSearch = !searchQuery || 
        st.name.toLowerCase().includes(searchQuery) || 
        (st.city && st.city.toLowerCase().includes(searchQuery)) || 
        (st.state && st.state.toLowerCase().includes(searchQuery));

      if (matchesCat && matchesSearch) {
        if (!leafletMap.hasLayer(m)) leafletMap.addLayer(m);
        count++;
      } else {
        if (leafletMap.hasLayer(m)) leafletMap.removeLayer(m);
      }
    });

    const countEl = document.getElementById("mapStationCount");
    if (countEl) countEl.textContent = count;
  } else if (searchQuery) {
    // If no state is selected but search query is typed, check if it matches a state or city
    const matchedState = Object.keys(mainStateLayers).find(st => 
      st.toLowerCase().includes(searchQuery)
    );
    if (matchedState) {
      const layer = mainStateLayers[matchedState];
      if (layer) drillIntoState(matchedState, layer, leafletMap, stationMarkers, false);
    }
  }
}

function applyModalMapFilters(searchQuery = "") {
  if (!modalLeafletMap) return;

  if (activeModalState !== "all" && selectedStateModal) {
    modalStationMarkers.forEach(m => {
      const st = m.stationData;
      const matchesSearch = !searchQuery || 
        st.name.toLowerCase().includes(searchQuery) || 
        (st.city && st.city.toLowerCase().includes(searchQuery)) || 
        (st.state && st.state.toLowerCase().includes(searchQuery));

      if (matchesSearch) {
        if (!modalLeafletMap.hasLayer(m)) modalLeafletMap.addLayer(m);
      } else {
        if (modalLeafletMap.hasLayer(m)) modalLeafletMap.removeLayer(m);
      }
    });
  } else if (searchQuery) {
    const matchedState = Object.keys(modalStateLayers).find(st => 
      st.toLowerCase().includes(searchQuery)
    );
    if (matchedState) {
      const layer = modalStateLayers[matchedState];
      if (layer) drillIntoState(matchedState, layer, modalLeafletMap, modalStationMarkers, true);
    }
  }
}

/**
 * =========================================================================
 * EXPLAINABLE AI (XAI) DIAGNOSTIC RENDERER
 * =========================================================================
 */
function renderXaiModal(targetHourIdx = 0) {
  const forecast = activeForecast || allForecasts["site_162"];
  const hourly = forecast.hourly || [];
  const selectedHour = hourly[targetHourIdx] || hourly[0] || {};
  const attributions = selectedHour.xai_attributions || [];

  const waterfallBox = document.getElementById("xaiWaterfallContainer");
  if (waterfallBox) {
    waterfallBox.innerHTML = "";

    const baseVal = 22.0;
    const finalVal = selectedHour.pm25 || 23.2;

    const baseHeader = document.createElement("div");
    baseHeader.className = "xai-waterfall-row";
    baseHeader.style.fontWeight = "600";
    baseHeader.innerHTML = `
      <span>Diurnal Baseline Expected PM₂.₅</span>
      <span>${baseVal.toFixed(1)} µg/m³</span>
    `;
    waterfallBox.appendChild(baseHeader);

    attributions.forEach(attr => {
      const isPos = attr.delta >= 0;
      const row = document.createElement("div");
      row.className = "xai-waterfall-row";
      row.innerHTML = `
        <div style="flex: 1;">
          <div style="color: #fff; font-weight: 500;">${attr.feature}</div>
          <div style="font-size: 11px; color: var(--text-faint);">${attr.desc}</div>
        </div>
        <div class="xai-bar-track">
          <div class="${isPos ? 'xai-bar-fill-pos' : 'xai-bar-fill-neg'}" style="width: ${Math.min(Math.abs(attr.delta) * 12, 100)}%;"></div>
        </div>
        <span style="font-weight: 600; color: ${isPos ? '#ff8a9a' : '#4ade80'}; width: 55px; text-align: right;">
          ${isPos ? '+' : ''}${attr.delta} µg/m³
        </span>
      `;
      waterfallBox.appendChild(row);
    });

    const finalFooter = document.createElement("div");
    finalFooter.className = "xai-waterfall-row";
    finalFooter.style.fontWeight = "700";
    finalFooter.style.marginTop = "6px";
    finalFooter.style.borderTop = "1px solid rgba(255,255,255,0.2)";
    finalFooter.innerHTML = `
      <span style="color: #fff;">Model Prediction at Horizon (+${targetHourIdx + 1}h)</span>
      <span style="color: #38bdf8; font-size: 15px;">${finalVal} µg/m³</span>
    `;
    waterfallBox.appendChild(finalFooter);
  }

  const globalBox = document.getElementById("xaiGlobalFeaturesContainer");
  if (globalBox) {
    globalBox.innerHTML = "";
    const topFeats = [
      { name: "PM₂.₅ Past 6h Moving Mean (Short-Term Inertia)", pct: 37.95 },
      { name: "PM₂.₅ Current Concentration (Immediate Baseline)", pct: 17.29 },
      { name: "PM₂.₅ Past 24h Moving Mean (Diurnal Background)", pct: 12.86 },
      { name: "PM₂.₅ Instantaneous Lag 0", pct: 9.83 },
      { name: "PM₂.₅ Lag 1 (1-Hour Momentum Velocity)", pct: 2.15 },
      { name: "PM₂.₅ Lag 6 (6-Hour Morning/Evening Cycle)", pct: 2.00 },
      { name: "PM₂.₅ Past 24h Min Floor Level", pct: 1.90 },
      { name: "Seasonal Cyclical Time Factors (Hour / Month Cos)", pct: 1.76 }
    ];

    topFeats.forEach(f => {
      const row = document.createElement("div");
      row.className = "pollutant-row";
      row.style.padding = "6px 0";
      row.innerHTML = `
        <span style="font-size: 12px; width: 220px; color: var(--text-soft);">${f.name}</span>
        <div class="pollutant-bar-track" style="margin: 0 10px;">
          <div class="pollutant-bar-fill" style="width: ${f.pct * 2.2}%; background-color: #38bdf8;"></div>
        </div>
        <span style="font-size: 12px; font-weight: 600; width: 45px; text-align: right; color: #fff;">${f.pct}%</span>
      `;
      globalBox.appendChild(row);
    });
  }
}

/**
 * Standalone Fallback Dataset
 */
function useFallbackData() {
  allStations = [
    { id: "site_162", name: "BTM Layout, Bengaluru", authority: "CPCB", city: "Bengaluru", state: "Karnataka", has_trained_model: true, mode: "model" }
  ];
  all647Stations = [
    { id: "site_162", name: "BTM Layout, Bengaluru", city: "Bengaluru", state: "Karnataka", lat: 12.9135, lon: 77.5951, pm25: 23.2, category: "Good", color: "#3FA796" }
  ];
  allStatesSummary = {
    Karnataka: { state: "Karnataka", count: 42, center: [14.5, 75.8], stations: all647Stations }
  };
}
