// Header language dropdown (<details class="lang-menu">, written by _tools/build_vi.py).
// Opening and closing work without JS; this only closes it on an outside click or Escape.
(function () {
  function openMenus() {
    return document.querySelectorAll('details.lang-menu[open]');
  }
  document.addEventListener('click', function (e) {
    openMenus().forEach(function (menu) {
      if (!menu.contains(e.target)) menu.open = false;
    });
  });
  document.addEventListener('keydown', function (e) {
    if (e.key !== 'Escape') return;
    openMenus().forEach(function (menu) {
      menu.open = false;
      menu.querySelector('summary').focus();
    });
  });
})();
