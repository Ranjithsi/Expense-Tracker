// script.js - global UI behaviors (sidebar toggle, dark mode)

document.addEventListener("DOMContentLoaded", function () {
  const sidebarToggle = document.getElementById("sidebarToggle");
  const sidebar = document.getElementById("sidebar");
  if (sidebarToggle && sidebar) {
    sidebarToggle.addEventListener("click", () => sidebar.classList.toggle("show"));
  }

  const darkModeToggle = document.getElementById("darkModeToggle");
  if (darkModeToggle) {
    darkModeToggle.addEventListener("click", async () => {
      try {
        const res = await fetch("/toggle-dark-mode", {
          method: "POST",
          headers: { "X-CSRFToken": CSRF_TOKEN },
        });
        const data = await res.json();
        document.documentElement.setAttribute("data-bs-theme", data.dark_mode ? "dark" : "light");
        const icon = darkModeToggle.querySelector("i");
        icon.className = data.dark_mode ? "bi bi-sun" : "bi bi-moon-stars";
      } catch (err) {
        console.error("Failed to toggle dark mode:", err);
      }
    });
  }

  // Auto-dismiss alerts after 5 seconds
  document.querySelectorAll(".alert").forEach((alert) => {
    setTimeout(() => {
      const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
      if (bsAlert) bsAlert.close();
    }, 5000);
  });
});
