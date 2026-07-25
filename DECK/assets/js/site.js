const toggle = document.querySelector(".nav-toggle");
const nav = document.querySelector(".site-nav");

if (toggle && nav) {
  toggle.addEventListener("click", () => {
    const open = nav.classList.toggle("open");
    toggle.setAttribute("aria-expanded", String(open));
  });
}

const currentFile = window.location.pathname.split("/").filter(Boolean).at(-1) || "index.html";
document.querySelectorAll(".site-nav a[data-page]").forEach((link) => {
  const target = link.dataset.page;
  const isHome = target === "index.html" && (currentFile === "DECK" || currentFile === "index.html");
  if (currentFile === target || isHome) {
    link.setAttribute("aria-current", "page");
  }
});

document.querySelectorAll("model-viewer").forEach((viewer) => {
  viewer.addEventListener(
    "camera-change",
    () => {
      const hint = viewer.closest(".model-stage, .model-card")?.querySelector(".drag-hint");
      if (hint) hint.style.opacity = "0";
    },
    { once: true }
  );
});
