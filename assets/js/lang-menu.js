// Header language picker (<details class="lang-menu">, written by _tools/build_i18n.py).
// The summary opens a popup with a grid of languages. This script closes it on a
// backdrop click, the close button or Escape, locks page scroll while it is open
// and moves focus into it.
(function () {
  var root = document.documentElement;

  function close(menu, refocus) {
    menu.open = false;
    if (refocus) menu.querySelector('summary').focus();
  }

  document.querySelectorAll('details.lang-menu').forEach(function (menu) {
    menu.addEventListener('toggle', function () {
      root.classList.toggle('lang-open', menu.open);
      if (menu.open) {
        var current = menu.querySelector('.lang-grid a[aria-current]') || menu.querySelector('.lang-grid a');
        if (current) {
          current.focus({ preventScroll: true });
          current.scrollIntoView({ block: 'nearest' });
        }
      }
    });
    var sheet = menu.querySelector('.lang-sheet');
    if (sheet) {
      sheet.addEventListener('click', function (e) {
        if (e.target === sheet) close(menu, true);
      });
    }
    var btn = menu.querySelector('.lang-close');
    if (btn) btn.addEventListener('click', function () { close(menu, true); });
  });

  document.addEventListener('keydown', function (e) {
    if (e.key !== 'Escape') return;
    document.querySelectorAll('details.lang-menu[open]').forEach(function (menu) { close(menu, true); });
  });
})();
