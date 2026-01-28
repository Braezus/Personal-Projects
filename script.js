// console.log("Portfolio site loaded successfully.");

// Remove loading screen after window loads
window.addEventListener("load", () => {
  document.body.classList.remove("loading");
  const loader = document.getElementById("loader");
  if (loader) loader.style.display = "none";

  // Apply dark mode preference
  if (localStorage.getItem("darkMode") === "true") {
    document.body.classList.add("dark-mode");
  }
});

// Dark mode toggle button logic
const toggle = document.getElementById("darkModeToggle");
if (toggle) {
  toggle.addEventListener("click", () => {
    document.body.classList.toggle("dark-mode");
    localStorage.setItem("darkMode", document.body.classList.contains("dark-mode"));
  });
}

// Back-to-top button logic (visibility + click)
const backToTopBtn = document.getElementById("backToTopBtn");
if (backToTopBtn) {
  const updateBackToTopVisibility = () => {
    backToTopBtn.style.display = window.scrollY > 300 ? "block" : "none";
  };

  window.addEventListener("scroll", updateBackToTopVisibility, { passive: true });
  updateBackToTopVisibility();

  backToTopBtn.addEventListener("click", () => {
    window.scrollTo({ top: 0, behavior: "smooth" });
  });
}

// Contact button scroll logic
const contactButton = document.getElementById("contactButton");
if (contactButton) {
  contactButton.addEventListener("click", () => {
    // This targets your Contact section (2nd from last section in <main>)
    const contactSection = document.querySelector("main section:nth-last-child(2)");
    if (contactSection) {
      contactSection.scrollIntoView({ behavior: "smooth" });
    }
  });
}

