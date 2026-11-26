/**
 * Landing Page Showcase Controller
 * Initializes Lucide icons, atmospheric gradients, and interactive phone frame behaviors.
 */

document.addEventListener("DOMContentLoaded", () => {
  setupLandingIcons();
  setupAtmosphere();
});

function setupLandingIcons() {
  const setIcon = (id, iconName, size = 18) => {
    const el = document.getElementById(id);
    if (el) el.innerHTML = getLucideIcon(iconName, size);
  };

  setIcon("navIcon", "wind", 20);
  setIcon("heroBadgeIcon", "sparkles", 14);
  setIcon("btnArrowIcon", "arrow-right", 16);
  setIcon("phonePinIcon", "map-pin", 12);
  setIcon("phoneConditionIcon", "sun", 32);
}

function setupAtmosphere() {
  const sky = document.getElementById("landingSkyViewport");
  if (!sky) return;

  const currentHour = new Date().getHours();
  if (isNightHour(currentHour)) {
    sky.style.background = SKY_NIGHT;
  } else {
    // Default to gentle Golden-Sky / Moderate atmospheric glow for daytime
    sky.style.background = "linear-gradient(180deg, #5FA3CF 0%, #CBE0B0 100%)";
  }
}
