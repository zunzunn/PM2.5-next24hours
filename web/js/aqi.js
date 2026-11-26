/**
 * Centralized CPCB AQI Breakpoints, Sky Gradients & Lucide SVG Icons
 * Defined per design.md specifications.
 */

const CPCB_PM25_CATEGORIES = [
  {
    name: "Good",
    min: 0,
    max: 30,
    color: "#3FA796",
    skyGradient: "linear-gradient(180deg, #4E9FD1 0%, #A4D9D2 100%)",
    icon: "sun",
    tone: "Enjoy outdoor activity",
    advice: "Air quality is ideal. Minimal health risk for all citizens."
  },
  {
    name: "Satisfactory",
    min: 31,
    max: 60,
    color: "#A8C66C",
    skyGradient: "linear-gradient(180deg, #5FA3CF 0%, #CBE0B0 100%)",
    icon: "cloud-sun",
    tone: "Fine for most people",
    advice: "Minor breathing discomfort to sensitive individuals."
  },
  {
    name: "Moderate",
    min: 61,
    max: 90,
    color: "#E8A317",
    skyGradient: "linear-gradient(180deg, #C8955A 0%, #F0D6A0 100%)",
    icon: "cloud-fog",
    tone: "Sensitive groups take care",
    advice: "Breathing discomfort to people with lung disease, asthma, and heart conditions."
  },
  {
    name: "Poor",
    min: 91,
    max: 120,
    color: "#E57A44",
    skyGradient: "linear-gradient(180deg, #BE7650 0%, #E9B58D 100%)",
    icon: "cloud-fog",
    tone: "Limit long outdoor exertion",
    advice: "Breathing discomfort to most people on prolonged exposure."
  },
  {
    name: "Very Poor",
    min: 121,
    max: 250,
    color: "#D1495B",
    skyGradient: "linear-gradient(180deg, #96566A 0%, #D99C9C 100%)",
    icon: "wind",
    tone: "Avoid outdoor activity",
    advice: "Respiratory illness on prolonged exposure. Avoid morning/evening outdoor workouts."
  },
  {
    name: "Severe",
    min: 251,
    max: 9999,
    color: "#8E2C48",
    skyGradient: "linear-gradient(180deg, #5A3850 0%, #A0647A 100%)",
    icon: "triangle-alert",
    tone: "Stay indoors if possible",
    advice: "Serious health impacts on healthy people and severe impacts on vulnerable groups."
  }
];

const SKY_NIGHT = "linear-gradient(180deg, #1B2540 0%, #3E4573 100%)";

/**
 * Returns category metadata given a PM2.5 value.
 */
function getAqiCategory(pm25) {
  const val = Math.max(0, Number(pm25) || 0);
  for (const cat of CPCB_PM25_CATEGORIES) {
    if (val <= cat.max) {
      return cat;
    }
  }
  return CPCB_PM25_CATEGORIES[CPCB_PM25_CATEGORIES.length - 1];
}

/**
 * Determines whether the given hour (0-23) falls during night hours (7 PM to 5 AM)
 */
function isNightHour(hour) {
  return hour >= 19 || hour < 5;
}

/**
 * Returns Lucide SVG markup for standard icons with customizable size and stroke
 */
function getLucideIcon(name, size = 20, strokeWidth = 1.75) {
  const icons = {
    "sun": `<svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="${strokeWidth}" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2"/><path d="M12 20v2"/><path d="m4.93 4.93 1.41 1.41"/><path d="m17.66 17.66 1.41 1.41"/><path d="M2 12h2"/><path d="M20 12h2"/><path d="m6.34 17.66-1.41 1.41"/><path d="m19.07 4.93-1.41 1.41"/></svg>`,
    "cloud-sun": `<svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="${strokeWidth}" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2v2"/><path d="m4.93 4.93 1.41 1.41"/><path d="M20 12h2"/><path d="m19.07 4.93-1.41 1.41"/><path d="M15.947 12.65a4 4 0 0 0-5.925-4.128"/><path d="M13 22H7a5 5 0 1 1 4.9-6H13a3 3 0 0 1 0 6Z"/></svg>`,
    "cloud-fog": `<svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="${strokeWidth}" stroke-linecap="round" stroke-linejoin="round"><path d="M4 14.899A7 7 0 1 1 15.71 8h1.79a4.5 4.5 0 0 1 2.5 8.242"/><path d="M16 17H7"/><path d="M17 21H9"/></svg>`,
    "wind": `<svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="${strokeWidth}" stroke-linecap="round" stroke-linejoin="round"><path d="M17.7 7.7a2.5 2.5 0 1 1 1.8 4.3H2"/><path d="M9.6 4.6A2 2 0 1 1 11 8H2"/><path d="M12.6 19.4A2 2 0 1 0 14 16H2"/></svg>`,
    "triangle-alert": `<svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="${strokeWidth}" stroke-linecap="round" stroke-linejoin="round"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>`,
    "clock": `<svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="${strokeWidth}" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>`,
    "thermometer": `<svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="${strokeWidth}" stroke-linecap="round" stroke-linejoin="round"><path d="M14 4v10.54a4 4 0 1 1-4 0V4a2 2 0 0 1 4 0Z"/></svg>`,
    "droplets": `<svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="${strokeWidth}" stroke-linecap="round" stroke-linejoin="round"><path d="M7 16.3c2.2 0 4-1.83 4-4.05 0-1.16-.57-2.26-1.71-3.19S7.29 6.75 7 5.3c-.29 1.45-1.14 2.84-2.29 3.76S3 11.1 3 12.25c0 2.22 1.8 4.05 4 4.05z"/><path d="M12.56 6.6A10.97 10.97 0 0 0 14 3.02c.5 2.5 2 4.9 4 6.5s3 3.5 3 5.5a6.98 6.98 0 0 1-11.91 4.97"/></svg>`,
    "gauge": `<svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="${strokeWidth}" stroke-linecap="round" stroke-linejoin="round"><path d="m12 14 4-4"/><path d="M3.34 19a10 10 0 1 1 17.32 0"/></svg>`,
    "map-pin": `<svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="${strokeWidth}" stroke-linecap="round" stroke-linejoin="round"><path d="M20 10c0 4.993-5.539 10.193-7.399 11.799a1 1 0 0 1-1.202 0C9.539 20.193 4 14.993 4 10a8 8 0 0 1 16 0"/><circle cx="12" cy="10" r="3"/></svg>`,
    "chevron-down": `<svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="${strokeWidth}" stroke-linecap="round" stroke-linejoin="round"><path d="m6 9 6 6 6-6"/></svg>`,
    "chevron-right": `<svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="${strokeWidth}" stroke-linecap="round" stroke-linejoin="round"><path d="m9 18 6-6-6-6"/></svg>`,
    "arrow-right": `<svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="${strokeWidth}" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg>`,
    "check": `<svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="${strokeWidth}" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>`,
    "info": `<svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="${strokeWidth}" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/></svg>`,
    "sparkles": `<svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="${strokeWidth}" stroke-linecap="round" stroke-linejoin="round"><path d="m12 3-1.9 5.8a2 2 0 0 1-1.287 1.288L3 12l5.8 1.9a2 2 0 0 1 1.288 1.287L12 21l1.9-5.8a2 2 0 0 1 1.287-1.288L21 12l-5.8-1.9a2 2 0 0 1-1.288-1.287Z"/></svg>`
  };

  return icons[name] || icons["cloud-sun"];
}

/**
 * Formats a 24h hour number (0-23) into user friendly "1 AM", "Now", "12 PM", etc.
 */
function formatHourDisplay(hour, isFirst = false) {
  if (isFirst) return "Now";
  const h = hour % 24;
  if (h === 0) return "12 AM";
  if (h < 12) return `${h} AM`;
  if (h === 12) return "12 PM";
  return `${h - 12} PM`;
}

/**
 * Automatically computes peak risk window, best outdoor window, and a friendly one-line advisory
 */
function computeHourlyAdvisory(hourlyList) {
  if (!hourlyList || hourlyList.length === 0) {
    return {
      bestWindow: "1 PM – 5 PM",
      peakRisk: "9 PM – 11 PM",
      advisorySentence: "Air quality levels are stable across the diurnal cycle.",
      high: 0,
      low: 0,
      bestIndices: new Set(),
      peakIndices: new Set()
    };
  }

  let minVal = Infinity, maxVal = -Infinity;
  let minIdx = 0, maxIdx = 0;

  hourlyList.forEach((item, idx) => {
    const val = item.pm25;
    if (val < minVal) {
      minVal = val;
      minIdx = idx;
    }
    if (val > maxVal) {
      maxVal = val;
      maxIdx = idx;
    }
  });

  // Calculate contiguous lowest 3-4 hour window
  let bestWindowStart = 0;
  let bestWindowScore = Infinity;
  const windowSize = 4;

  for (let i = 0; i <= hourlyList.length - windowSize; i++) {
    const sum = hourlyList.slice(i, i + windowSize).reduce((acc, cur) => acc + cur.pm25, 0);
    if (sum < bestWindowScore) {
      bestWindowScore = sum;
      bestWindowStart = i;
    }
  }

  const bestIndices = new Set();
  for (let i = bestWindowStart; i < bestWindowStart + windowSize; i++) {
    bestIndices.add(i);
  }

  const peakIndices = new Set([maxIdx]);
  if (maxIdx > 0) peakIndices.add(maxIdx - 1);
  if (maxIdx < hourlyList.length - 1) peakIndices.add(maxIdx + 1);

  // Time formatting
  const startHour = (new Date().getHours() + bestWindowStart) % 24;
  const endHour = (startHour + windowSize) % 24;
  const peakHour = (new Date().getHours() + maxIdx) % 24;

  const bestWindowStr = `${formatHourDisplay(startHour)} – ${formatHourDisplay(endHour)}`;
  const peakRiskStr = `${formatHourDisplay(peakHour)} (${Math.round(maxVal)} µg/m³)`;

  const advisorySentence = `Best time outside is ${bestWindowStr}. Diurnal peak expected around ${formatHourDisplay(peakHour)}.`;

  return {
    bestWindow: bestWindowStr,
    peakRisk: peakRiskStr,
    advisorySentence,
    high: Math.round(maxVal),
    low: Math.round(minVal),
    bestIndices,
    peakIndices
  };
}
