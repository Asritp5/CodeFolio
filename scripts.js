// Theme Toggle Button
const themeToggleBtn = document.getElementById("themeToggle");
const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;

// Load stored theme preference or system preference
const savedTheme = localStorage.getItem("theme");
if (savedTheme === "dark" || (!savedTheme && prefersDark)) {
  document.body.classList.add("dark-theme");
  themeToggleBtn.textContent = "☀️";
} else {
  themeToggleBtn.textContent = "🌙";
}

// Toggle Theme on Click
themeToggleBtn.addEventListener("click", () => {
  document.body.classList.toggle("dark-theme");
  const isDark = document.body.classList.contains("dark-theme");

  themeToggleBtn.textContent = isDark ? "☀️" : "🌙";
  localStorage.setItem("theme", isDark ? "dark" : "light");
});
