/* Keep native video controls; respect the visitor's reduced-motion preference. */
(function () {
  "use strict";
  var preference = window.matchMedia("(prefers-reduced-motion: reduce)");
  var videos = document.querySelectorAll(".showcase video");

  function syncPlayback() {
    videos.forEach(function (video) {
      video.autoplay = !preference.matches;
      if (preference.matches) {
        video.pause();
      } else {
        // Browser autoplay restrictions leave the native play button available.
        video.play().catch(function () {});
      }
    });
  }

  syncPlayback();
  preference.addEventListener("change", syncPlayback);
})();
