document.addEventListener("DOMContentLoaded", function () {
  const video = document.getElementById("courseVideo");
  const captionSelect = document.getElementById("captionSelect");

  // Check if video and caption elements exist on this page
  if (video && captionSelect) {
    captionSelect.addEventListener("change", () => {
      const tracks = video.textTracks;

      for (let i = 0; i < tracks.length; i++) {
        tracks[i].mode = "disabled";
      }

      if (captionSelect.value !== "none") {
        const index = parseInt(captionSelect.value);
        if (tracks[index]) {
          tracks[index].mode = "showing";
        }
      }
    });

    // Set default (first caption track)
    const tracks = video.textTracks;
    if (tracks[0]) tracks[0].mode = "showing";
  }
});
