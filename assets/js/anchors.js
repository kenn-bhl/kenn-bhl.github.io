// Same-page links (href="#id"): scroll to the section without adding #id to the URL.
// Arriving from another page with a hash (e.g. ../#education): jump there, then drop the hash.
(() => {
  const reduceMotion = matchMedia('(prefers-reduced-motion: reduce)');

  const targetOf = (hash) => {
    if (!hash || hash.length < 2) return null;
    try { return document.getElementById(decodeURIComponent(hash.slice(1))); } catch { return null; }
  };

  const clearHash = () => {
    if (location.hash) history.replaceState(history.state, '', location.pathname + location.search);
  };

  document.addEventListener('click', (event) => {
    const link = event.target.closest('a[href^="#"]');
    if (!link || event.defaultPrevented || event.button !== 0) return;
    if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    const target = targetOf(link.hash);
    if (!target) return;
    event.preventDefault();
    const behavior = reduceMotion.matches ? 'instant' : 'smooth';
    // #top is the sticky header, which is always "in view": scroll the page itself.
    if (target.id === 'top') window.scrollTo({ top: 0, behavior });
    else target.scrollIntoView({ behavior, block: 'start' });
    // Move keyboard focus to the section too, as a normal anchor jump would.
    if (!target.hasAttribute('tabindex')) target.setAttribute('tabindex', '-1');
    target.focus({ preventScroll: true });
    clearHash();
  });

  // After load (images sized), make sure we sit on the hash target, then tidy the URL.
  window.addEventListener('load', () => {
    const target = targetOf(location.hash);
    if (!target) return;
    target.scrollIntoView({ behavior: 'instant', block: 'start' });
    clearHash();
  });
})();
