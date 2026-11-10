// The Austin Local: hero load-in, scroll reveals, category accordion.
(function () {
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // hero zoom-out + copy fade once the image is ready
  var hero = document.querySelector('.hero');
  if (hero) {
    var img = hero.querySelector('img');
    var go = function () { requestAnimationFrame(function () { hero.classList.add('is-loaded'); }); };
    if (img.complete) go(); else { img.addEventListener('load', go); img.addEventListener('error', go); }
  }

  // reveals replay as they re-enter, like the Storyhaus sites
  var items = document.querySelectorAll('.reveal');
  if (reduce || !('IntersectionObserver' in window)) {
    items.forEach(function (el) { el.classList.add('is-in'); });
  } else {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) e.target.classList.add('is-in');
        else if (e.boundingClientRect.top > 0) e.target.classList.remove('is-in');
      });
    }, { rootMargin: '0px 0px -8% 0px' });
    items.forEach(function (el) { io.observe(el); });
  }

  // category accordion: one open at a time; panels stay in the DOM so they can animate
  var cats = Array.prototype.slice.call(document.querySelectorAll('.cat'));
  cats.forEach(function (cat) {
    var panel = cat.querySelector('.cat-panel');
    panel.hidden = false;
    if (!cat.classList.contains('is-open')) panel.setAttribute('aria-hidden', 'true'), panel.inert = true;
    cat.querySelector('.cat-tab').addEventListener('click', function () {
      if (cat.classList.contains('is-open')) return;
      cats.forEach(function (c) {
        var open = c === cat;
        c.classList.toggle('is-open', open);
        c.querySelector('.cat-tab').setAttribute('aria-expanded', String(open));
        var p = c.querySelector('.cat-panel');
        p.inert = !open;
        if (open) p.removeAttribute('aria-hidden'); else p.setAttribute('aria-hidden', 'true');
      });
    });
  });
})();
