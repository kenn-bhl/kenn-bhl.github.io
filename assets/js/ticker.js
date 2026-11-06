// Auto-scrolling ticker that loops only when its items don't fit the screen.
// Markup: <div data-ticker [data-speed="50"]><track>…items…</track></div>
// When looping, the items are cloned once (class "is-dup", aria-hidden) so the
// track can slide by half its width and restart seamlessly.
(() => {
  const reduceMotion = matchMedia('(prefers-reduced-motion: reduce)');
  const gutter = () =>
    parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--gutter')) || 0;

  function update(box) {
    const track = box.firstElementChild;
    track.querySelectorAll(':scope > .is-dup').forEach((el) => el.remove());

    const width = track.scrollWidth;
    const fits = width <= box.clientWidth - 2 * gutter();
    const loop = !fits && !reduceMotion.matches;
    box.classList.toggle('is-fit', fits);
    box.classList.toggle('is-looping', loop);
    if (!loop) return;

    for (const item of [...track.children]) {
      const copy = item.cloneNode(true);
      copy.classList.add('is-dup');
      copy.setAttribute('aria-hidden', 'true');
      copy.querySelectorAll('a, button, [tabindex]').forEach((el) => (el.tabIndex = -1));
      track.appendChild(copy);
    }
    const speed = Number(box.dataset.speed) || 50; // px per second
    box.style.setProperty('--ticker-duration', `${width / speed}s`);
  }

  const boxes = document.querySelectorAll('[data-ticker]');
  const lastWidth = new WeakMap();
  const observer = new ResizeObserver((entries) => {
    for (const { target } of entries) {
      if (lastWidth.get(target) === target.clientWidth) continue;
      lastWidth.set(target, target.clientWidth);
      update(target);
    }
  });
  boxes.forEach((box) => observer.observe(box));
  reduceMotion.addEventListener('change', () => boxes.forEach(update));
})();
