// Add strikethrough styling to ToC links for deprecated endpoints
document.addEventListener("DOMContentLoaded", function () {
  document.querySelectorAll(".deprecated-marker").forEach(function (marker) {
    var heading = marker.parentElement;
    if (!heading || !heading.id) return;
    document.querySelectorAll('a.md-nav__link[href="#' + heading.id + '"]').forEach(function (link) {
      link.style.textDecoration = "line-through";
    });
  });
});
