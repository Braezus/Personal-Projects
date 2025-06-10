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

