// fläsh Campus – Folien blättern, Kapitel in der Leiste, Sprechertext, Großansicht der Layouts.
(() => {
  const data = JSON.parse(document.getElementById("deck-data").textContent);
  const slides = data.slides;
  const $ = (id) => document.getElementById(id);
  const img = $("slide"), current = $("current"), where = $("where");
  const prev = $("prev"), next = $("next");
  const notesToggle = $("notes-toggle"), notes = $("notes"), notesText = $("notes-text");
  const thumbs = [...document.querySelectorAll(".thumb")];
  const chapters = [...document.querySelectorAll(".rail-chapter")];
  const calm = matchMedia("(prefers-reduced-motion: reduce)");
  let index = 0;

  const fromHash = () => {
    const m = location.hash.match(/^#folie-(\d+)$/);
    return m ? Math.min(Math.max(Number(m[1]), 1), slides.length) - 1 : null;
  };

  function show(i, { scrollThumb = true, updateHash = true } = {}) {
    index = Math.min(Math.max(i, 0), slides.length - 1);
    const s = slides[index];
    if (!img.src.endsWith(s.src)) {
      img.classList.add("is-loading");
      const pre = new Image();
      pre.onload = pre.onerror = () => { img.src = s.src; img.classList.remove("is-loading"); };
      pre.src = s.src;
    }
    img.alt = `Folie ${s.n}: ${s.title}`;
    current.textContent = s.n;
    where.textContent = s.chapter ? `Kapitel ${s.chapter}: ${data.chapters[s.chapter - 1]}` : s.kicker;
    notesText.textContent = s.notes || "Zu dieser Folie gibt es keinen Sprechertext.";
    prev.disabled = index === 0;
    next.disabled = index === slides.length - 1;
    thumbs.forEach((t, k) => t.setAttribute("aria-current", String(k === index)));
    chapters.forEach((c) => {
      const n = Number(c.dataset.chapter);
      c.classList.toggle("is-active", n === s.chapter);
      c.classList.toggle("is-done", Boolean(s.chapter) && n < s.chapter);
      if (n === s.chapter) c.setAttribute("aria-current", "step"); else c.removeAttribute("aria-current");
    });
    if (scrollThumb) {
      const strip = thumbs[index].closest(".thumbs");
      const t = thumbs[index];
      strip.scrollTo({ left: t.offsetLeft - strip.clientWidth / 2 + t.clientWidth / 2, behavior: calm.matches ? "auto" : "smooth" });
    }
    if (updateHash) history.replaceState(null, "", `#folie-${s.n}`);
    if (slides[index + 1]) new Image().src = slides[index + 1].src;
  }

  prev.addEventListener("click", () => show(index - 1));
  next.addEventListener("click", () => show(index + 1));
  thumbs.forEach((t) => t.addEventListener("click", () => show(Number(t.dataset.index))));
  chapters.forEach((c) => c.addEventListener("click", () => {
    const k = slides.findIndex((s) => s.chapter === Number(c.dataset.chapter));
    if (k < 0) return;
    show(k);
    $("viewer").scrollIntoView({ behavior: calm.matches ? "auto" : "smooth", block: "center" });
  }));

  document.addEventListener("keydown", (e) => {
    if (e.altKey || e.ctrlKey || e.metaKey || e.target.closest("input, textarea, select") || $("lightbox").open) return;
    if (e.key === "ArrowRight" || e.key === "PageDown") { show(index + 1); e.preventDefault(); }
    if (e.key === "ArrowLeft" || e.key === "PageUp") { show(index - 1); e.preventDefault(); }
  });

  let touchX = null;
  const screen = img.closest(".screen");
  screen.addEventListener("touchstart", (e) => { touchX = e.touches[0].clientX; }, { passive: true });
  screen.addEventListener("touchend", (e) => {
    if (touchX === null) return;
    const dx = e.changedTouches[0].clientX - touchX;
    if (Math.abs(dx) > 40) show(index + (dx < 0 ? 1 : -1));
    touchX = null;
  });

  notesToggle.addEventListener("click", () => {
    const open = notesToggle.getAttribute("aria-expanded") !== "true";
    notesToggle.setAttribute("aria-expanded", String(open));
    notes.hidden = !open;
    notesToggle.textContent = open ? "Sprechertext ausblenden" : "Sprechertext anzeigen";
  });

  const box = $("lightbox"), boxImg = $("lightbox-img"), boxLabel = $("lightbox-label");
  document.querySelectorAll(".layout").forEach((b) => b.addEventListener("click", () => {
    boxImg.src = b.dataset.src;
    boxImg.alt = `Layout ${b.dataset.label}`;
    boxLabel.textContent = b.dataset.label;
    box.showModal();
  }));
  box.addEventListener("click", (e) => { if (e.target === box) box.close(); });

  window.addEventListener("hashchange", () => {
    const k = fromHash();
    if (k !== null && k !== index) show(k, { updateHash: false });
  });
  show(fromHash() ?? 0, { scrollThumb: false, updateHash: false });
})();
