/* Runs in the head to restore the theme before the first paint. */
(function () {
  "use strict";
  var root = document.documentElement;
  var storageKey = "panda-lab-theme";
  var preference = window.matchMedia("(prefers-color-scheme: dark)");
  root.classList.add("js");

  try {
    var saved = localStorage.getItem(storageKey);
    if (saved === "light" || saved === "dark") {
      root.setAttribute("data-theme", saved);
    }
  } catch (error) {
    // Browsing with storage disabled still supports switching themes.
  }

  document.addEventListener("DOMContentLoaded", function () {
    var themeButton = document.querySelector(".theme-toggle");
    var menuButton = document.querySelector(".menu-toggle");
    var navigation = document.querySelector(".site-nav");

    function currentTheme() {
      return root.getAttribute("data-theme") || (preference.matches ? "dark" : "light");
    }

    function syncTheme() {
      if (!themeButton) return;
      var mode = currentTheme();
      var label = mode === "dark" ? "Switch to light mode" : "Switch to dark mode";
      themeButton.setAttribute("data-mode", mode);
      themeButton.setAttribute("aria-label", label);
      themeButton.setAttribute("title", label);
    }

    if (themeButton) {
      themeButton.addEventListener("click", function () {
        var mode = currentTheme() === "dark" ? "light" : "dark";
        root.setAttribute("data-theme", mode);
        try { localStorage.setItem(storageKey, mode); } catch (error) {}
        syncTheme();
      });
      preference.addEventListener("change", syncTheme);
      syncTheme();
    }

    if (menuButton && navigation) {
      function setMenu(open) {
        navigation.classList.toggle("is-open", open);
        menuButton.setAttribute("aria-expanded", String(open));
        menuButton.setAttribute("aria-label", open ? "Close navigation" : "Open navigation");
      }

      menuButton.addEventListener("click", function () {
        setMenu(menuButton.getAttribute("aria-expanded") !== "true");
      });
      document.addEventListener("keydown", function (event) {
        if (event.key === "Escape" && menuButton.getAttribute("aria-expanded") === "true") {
          setMenu(false);
          menuButton.focus();
        }
      });
      navigation.addEventListener("click", function (event) {
        if (event.target.closest("a")) setMenu(false);
      });
      window.matchMedia("(max-width: 900px)").addEventListener("change", function () {
        setMenu(false);
      });
    }
  });
})();
