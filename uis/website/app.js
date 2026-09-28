// TrackFlow Website — Corporate site

window.addEventListener("DOMContentLoaded", () => {
  lucide.createIcons();

  // Mobile menu toggle
  const toggle = document.getElementById("menu-toggle");
  const nav = document.getElementById("main-nav");
  toggle.addEventListener("click", () => {
    nav.classList.toggle("open");
    const isOpen = nav.classList.contains("open");
    toggle.setAttribute("aria-label", isOpen ? "Cerrar menú" : "Abrir menú");
    toggle.innerHTML = isOpen
      ? '<i data-lucide="x"></i>'
      : '<i data-lucide="menu"></i>';
    lucide.createIcons();
  });

  // Close menu on nav click (mobile)
  nav.querySelectorAll("a").forEach((link) => {
    link.addEventListener("click", () => {
      nav.classList.remove("open");
      toggle.innerHTML = '<i data-lucide="menu"></i>';
      toggle.setAttribute("aria-label", "Abrir menú");
      lucide.createIcons();
    });
  });

  // Contact form handling
  const form = document.getElementById("contact-form");
  form.addEventListener("submit", (e) => {
    e.preventDefault();
    const toast = document.getElementById("toast");
    toast.textContent = "Gracias por tu mensaje. Te contactaremos pronto.";
    toast.className = "show";
    setTimeout(() => { toast.className = ""; }, 3000);
    form.reset();
  });
});