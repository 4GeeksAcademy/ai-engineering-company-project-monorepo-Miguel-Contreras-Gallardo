/* TrackFlow — Lucide Icon Helper
 * Extracted to avoid manual lucide.createIcons() calls scattered across views.
 * Auto-initializes on DOMContentLoaded. Exposes window.refreshIcons() for
 * dynamic DOM updates (menu toggle, API status changes, etc.).
 */

window.refreshIcons = () => {
  if (typeof lucide !== "undefined" && lucide.createIcons) {
    lucide.createIcons();
  }
};

// Auto-initialize when DOM is ready
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", window.refreshIcons);
} else {
  window.refreshIcons();
}