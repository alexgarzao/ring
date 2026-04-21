'use strict';

// In-page tweaks layer. T key or toolbar Tweak button toggles tweak mode.
// Three tools: pin (point at coords), flag (attach to slide element), sticky
// (freeform note). All tweak UI lives on document.body — the <deck-stage>
// shadow-DOM .canvas has transform: scale(), which creates a containing
// block for position:fixed descendants and warps overlays.
//
// Markers are slide-scoped: a flag on slide 3 only renders when slide 3 is
// active. Pins/stickies rely on slide-space coords captured at drop time and
// reprojected to screen space on render. Flags rely on a descendant CSS
// selector re-resolved against the live DOM on each render, so content
// hot-reloads don't orphan them as long as structure is stable.
//
// Persistence: dev-server POST/PUT/DELETE/GET on /feedback. See the report
// in the PR description for the endpoint schema.

(function () {
  const SLIDE_W = 1920;
  const SLIDE_H = 1080;

  const state = {
    mounted: false,
    stage: null,
    on: false,
    activeTool: null,
    markers: [],
    currentSlideIndex: -1,
    pendingFlagEl: null,
  };

  const dom = {
    picker: null,
    hoverOutline: null,
    popover: null,
    markerLayer: null,
    styleEl: null,
  };

  function mount(stage) {
    if (state.mounted) return;
    state.stage = stage;
    buildDom();
    attachListeners();
    state.mounted = true;
  }

  function open() {
    if (!state.mounted || state.on) return;
    document.dispatchEvent(new CustomEvent('deck-feedback-opening'));
    state.on = true;
    document.body.classList.add('deck-tweaks-on');
    dom.picker.style.display = 'inline-flex';
    loadMarkers();
  }

  function close() {
    if (!state.on) return;
    state.on = false;
    document.body.classList.remove('deck-tweaks-on');
    dom.picker.style.display = 'none';
    setActiveTool(null);
    closePopover();
    hideHoverOutline();
  }

  function toggle() { state.on ? close() : open(); }

  function buildDom() {
    const style = document.createElement('style');
    style.setAttribute('data-deck-tweaks', '');
    style.textContent = [
      'body.deck-tweaks-on { cursor: default; }',
      'body.deck-tweaks-on.deck-tweak-cursor-crosshair, body.deck-tweaks-on.deck-tweak-cursor-crosshair * { cursor: crosshair !important; }',
      '.deck-tweak-hover-outline { position: fixed; pointer-events: none; border: 2px solid #FEED02; box-shadow: 0 0 0 1px rgba(25,26,27,0.6); z-index: 9988; display: none; }',
      '.deck-tweak-picker { position: fixed; bottom: 72px; left: 50%; transform: translateX(-50%); z-index: 9995; display: none; gap: 6px; padding: 6px; background: rgba(25,26,27,0.92); border-radius: 999px; box-shadow: 0 8px 32px rgba(0,0,0,0.25); backdrop-filter: blur(6px); }',
      '.deck-tweak-picker button { appearance: none; border: 0; background: transparent; color: #fff; font-family: "JetBrains Mono", ui-monospace, monospace; font-size: 11px; letter-spacing: 0.06em; text-transform: uppercase; padding: 8px 14px; border-radius: 999px; cursor: pointer; display: inline-flex; align-items: center; gap: 6px; }',
      '.deck-tweak-picker button:hover { background: rgba(255,255,255,0.1); }',
      '.deck-tweak-picker button.active { background: #FEED02; color: #191A1B; }',
      '.deck-tweak-marker-layer { position: fixed; inset: 0; pointer-events: none; z-index: 9990; }',
      '.deck-tweak-marker-layer > * { pointer-events: auto; }',
      '.deck-tweak-pin { position: fixed; width: 24px; height: 24px; background: #FEED02; border: 2px solid #191A1B; border-radius: 50% 50% 50% 0; transform: translate(-12px, -24px) rotate(-45deg); cursor: pointer; box-shadow: 0 4px 12px rgba(0,0,0,0.25); display: flex; align-items: center; justify-content: center; }',
      '.deck-tweak-pin > span { transform: rotate(45deg); font-family: "JetBrains Mono", ui-monospace, monospace; font-size: 10px; font-weight: 700; color: #191A1B; line-height: 1; }',
      '.deck-tweak-flag { position: fixed; background: #191A1B; color: #FEED02; padding: 3px 8px; border-radius: 4px; font-family: "JetBrains Mono", ui-monospace, monospace; font-size: 10px; letter-spacing: 0.05em; text-transform: uppercase; cursor: pointer; box-shadow: 0 4px 12px rgba(0,0,0,0.3); max-width: 180px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }',
      '.deck-tweak-sticky { position: fixed; width: 200px; min-height: 140px; background: #fef4a8; border: 1px solid rgba(0,0,0,0.08); border-radius: 2px; box-shadow: 0 6px 18px rgba(0,0,0,0.2); transform: rotate(-1.5deg); padding: 22px 10px 10px; box-sizing: border-box; }',
      '.deck-tweak-sticky textarea { width: 100%; height: 100px; resize: none; border: 0; outline: 0; background: transparent; font-family: "Comic Sans MS", "Marker Felt", "Segoe Print", cursive; font-size: 14px; color: #191A1B; line-height: 1.35; }',
      '.deck-tweak-sticky .chrome { position: absolute; top: 0; left: 0; right: 0; height: 22px; display: flex; align-items: center; justify-content: flex-end; padding: 0 6px; cursor: grab; }',
      '.deck-tweak-sticky .chrome:active { cursor: grabbing; }',
      '.deck-tweak-sticky .close { appearance: none; border: 0; background: transparent; font-size: 16px; line-height: 1; cursor: pointer; color: #191A1B; padding: 2px 4px; }',
      '.deck-tweak-popover { position: fixed; width: 220px; background: #fff; color: #191A1B; border-radius: 6px; box-shadow: 0 12px 32px rgba(0,0,0,0.28); padding: 10px; z-index: 9999; font-family: "IBM Plex Serif", Georgia, serif; }',
      '.deck-tweak-popover textarea { width: 100%; box-sizing: border-box; min-height: 80px; padding: 6px 8px; font: inherit; font-size: 13px; border: 1px solid #d4d4d8; border-radius: 4px; resize: vertical; outline: none; }',
      '.deck-tweak-popover .row { display: flex; justify-content: space-between; gap: 6px; margin-top: 8px; }',
      '.deck-tweak-popover button { appearance: none; border: 0; padding: 6px 12px; border-radius: 4px; font-family: "JetBrains Mono", ui-monospace, monospace; font-size: 10px; letter-spacing: 0.05em; text-transform: uppercase; cursor: pointer; }',
      '.deck-tweak-popover .primary { background: #191A1B; color: #fff; }',
      '.deck-tweak-popover .danger { background: transparent; color: #b02222; border: 1px solid #e4c7c7; }',
    ].join('\n');
    document.head.appendChild(style);
    dom.styleEl = style;

    const picker = document.createElement('div');
    picker.className = 'deck-tweak-picker';
    picker.setAttribute('aria-label', 'Tweak tools');
    picker.appendChild(toolButton('pin', 'Pin'));
    picker.appendChild(toolButton('flag', 'Flag'));
    picker.appendChild(toolButton('sticky', 'Sticky'));
    document.body.appendChild(picker);
    dom.picker = picker;

    const outline = document.createElement('div');
    outline.className = 'deck-tweak-hover-outline';
    document.body.appendChild(outline);
    dom.hoverOutline = outline;

    const layer = document.createElement('div');
    layer.className = 'deck-tweak-marker-layer';
    document.body.appendChild(layer);
    dom.markerLayer = layer;
  }

  function toolButton(tool, label) {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.dataset.tool = tool;
    btn.textContent = label;
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      setActiveTool(state.activeTool === tool ? null : tool);
    });
    return btn;
  }

  function setActiveTool(tool) {
    state.activeTool = tool;
    dom.picker.querySelectorAll('button').forEach(b => {
      b.classList.toggle('active', b.dataset.tool === tool);
    });
    // Crosshair for all three tools; the hover outline overlays on top for flag.
    document.body.classList.toggle('deck-tweak-cursor-crosshair', !!tool);
    if (!tool) hideHoverOutline();
  }

  function attachListeners() {
    state.stage.addEventListener('slidechange', onSlideChange);
    document.addEventListener('mousemove', onMouseMove);
    document.addEventListener('click', onClick, true);
    document.addEventListener('keydown', onKeydown);
    window.addEventListener('scroll', rerender, true);
    window.addEventListener('resize', rerender);
  }

  function onSlideChange(e) {
    state.currentSlideIndex = e.detail.index;
    if (state.on) loadMarkers();
  }

  function onMouseMove(e) {
    if (!state.on) return;
    if (state.activeTool !== 'flag') { hideHoverOutline(); return; }
    const el = pickTweakable(e.target);
    if (el) showHoverOutline(el);
    else hideHoverOutline();
  }

  // Click handler uses capture so we can intercept before the click reaches
  // marker elements (pin/flag open their own popovers via stopPropagation).
  function onClick(e) {
    if (!state.on) return;
    if (e.target.closest('.deck-tweak-popover')) return;
    if (e.target.closest('.deck-tweak-picker')) return;
    if (e.target.closest('.deck-tweak-sticky')) return;
    if (e.target.closest('.deck-tweak-pin') || e.target.closest('.deck-tweak-flag')) return;
    if (!state.activeTool) return;
    const slide = getActiveSlide();
    if (!slide) return;
    if (!insideSlide(e.target, slide)) return;

    if (state.activeTool === 'pin') { dropPin(e, slide); }
    else if (state.activeTool === 'sticky') { dropSticky(e, slide); }
    else if (state.activeTool === 'flag') {
      const el = pickTweakable(e.target);
      if (el) attachFlag(el, slide, e.clientX, e.clientY);
    }
  }

  function onKeydown(e) {
    if (!state.on) return;
    if (e.key !== 'Escape') return;
    if (dom.popover) { e.preventDefault(); closePopover(); return; }
    if (state.activeTool) { e.preventDefault(); setActiveTool(null); return; }
    e.preventDefault();
    close();
  }

  function pickTweakable(target) {
    if (!target || !target.closest) return null;
    if (target.closest('.deck-tweak-hover-outline')) return null;
    if (target.closest('.deck-tweak-picker')) return null;
    if (target.closest('.deck-tweak-popover')) return null;
    if (target.closest('.deck-tweak-pin, .deck-tweak-flag, .deck-tweak-sticky')) return null;
    if (target.closest('#deck-toolbar, #deck-notes-panel, #deck-blank-overlay')) return null;
    const slide = getActiveSlide();
    if (!slide) return null;
    if (target === slide) return null;
    if (!slide.contains(target)) return null;
    return target.closest('*');
  }

  function insideSlide(target, slide) {
    return target === slide || slide.contains(target);
  }

  function getActiveSlide() {
    const i = state.stage.index;
    return state.stage.querySelectorAll(':scope > *')[i] || null;
  }

  function getSlideLabel(slide) {
    return slide ? (slide.getAttribute('data-label') || '') : '';
  }

  function showHoverOutline(el) {
    const r = el.getBoundingClientRect();
    dom.hoverOutline.style.display = 'block';
    dom.hoverOutline.style.left = r.left + 'px';
    dom.hoverOutline.style.top = r.top + 'px';
    dom.hoverOutline.style.width = r.width + 'px';
    dom.hoverOutline.style.height = r.height + 'px';
  }

  function hideHoverOutline() {
    if (dom.hoverOutline) dom.hoverOutline.style.display = 'none';
  }

  // Slide-space coords (0..1920, 0..1080). We store these instead of raw
  // screen pixels so pins/stickies survive window resize and scale changes.
  function clientToSlide(cx, cy, slide) {
    const r = slide.getBoundingClientRect();
    if (r.width === 0 || r.height === 0) return { x: 0, y: 0 };
    const x = ((cx - r.left) / r.width) * SLIDE_W;
    const y = ((cy - r.top) / r.height) * SLIDE_H;
    return { x: Math.round(x), y: Math.round(y) };
  }

  function slideToClient(x, y, slide) {
    const r = slide.getBoundingClientRect();
    return {
      cx: r.left + (x / SLIDE_W) * r.width,
      cy: r.top + (y / SLIDE_H) * r.height,
    };
  }

  function dropPin(e, slide) {
    const { x, y } = clientToSlide(e.clientX, e.clientY, slide);
    const marker = {
      id: uid(),
      slideIndex: state.stage.index,
      slideLabel: getSlideLabel(slide),
      kind: 'pin',
      anchor: { x, y },
      text: '',
    };
    state.markers.push(marker);
    renderMarkers();
    saveMarker(marker);
    setActiveTool(null);
    openPopover(marker, e.clientX, e.clientY);
  }

  function dropSticky(e, slide) {
    const { x, y } = clientToSlide(e.clientX, e.clientY, slide);
    const marker = {
      id: uid(),
      slideIndex: state.stage.index,
      slideLabel: getSlideLabel(slide),
      kind: 'sticky',
      anchor: { x, y },
      text: '',
    };
    state.markers.push(marker);
    renderMarkers();
    saveMarker(marker);
    setActiveTool(null);
  }

  function attachFlag(el, slide, cx, cy) {
    const selector = generateSelector(el, slide);
    const label = getSlideLabel(slide);
    const marker = {
      id: uid(),
      slideIndex: state.stage.index,
      slideLabel: label,
      kind: 'flag',
      anchor: {
        selector,
        elementText: (el.textContent || '').trim().slice(0, 80),
      },
      text: '',
    };
    state.markers.push(marker);
    renderMarkers();
    saveMarker(marker);
    setActiveTool(null);
    openPopover(marker, cx, cy);
  }

  // Simple CSS selector anchored at the slide. We build it from tag name +
  // nth-of-type index of each ancestor up to the slide root. CSS.escape guards
  // against quote/bracket chars in the data-label; the rest of the path is
  // tag/index, no user content.
  function generateSelector(el, slide) {
    const label = getSlideLabel(slide);
    const parts = [];
    let cur = el;
    while (cur && cur !== slide && cur.parentElement) {
      const parent = cur.parentElement;
      const tag = cur.tagName.toLowerCase();
      const siblings = Array.from(parent.children).filter(c => c.tagName === cur.tagName);
      const idx = siblings.length > 1 ? siblings.indexOf(cur) + 1 : 0;
      parts.unshift(idx > 0 ? tag + ':nth-of-type(' + idx + ')' : tag);
      cur = parent;
    }
    const root = 'section[data-label="' + CSS.escape(label) + '"]';
    return parts.length ? root + ' ' + parts.join(' > ') : root;
  }

  function uid() {
    return 'c' + Math.random().toString(36).slice(2, 8);
  }

  // Re-render routine: clear DOM layer, project each marker for the current
  // slide into screen space, draw. Called on scroll/resize/slidechange and
  // after save/delete/update. Scroll uses capture because the canvas scroll
  // doesn't bubble.
  function renderMarkers() {
    dom.markerLayer.innerHTML = '';
    if (!state.on && !hasAnyMarkerForSlide()) return;
    const slide = getActiveSlide();
    if (!slide) return;
    const activeIdx = state.stage.index;
    for (const m of state.markers) {
      if (m.slideIndex !== activeIdx) continue;
      if (m.kind === 'pin') renderPin(m, slide);
      else if (m.kind === 'flag') renderFlag(m, slide);
      else if (m.kind === 'sticky') renderSticky(m, slide);
    }
  }

  function hasAnyMarkerForSlide() {
    const i = state.stage.index;
    return state.markers.some(m => m.slideIndex === i);
  }

  function rerender() {
    renderMarkers();
  }

  function renderPin(m, slide) {
    const { cx, cy } = slideToClient(m.anchor.x, m.anchor.y, slide);
    const el = document.createElement('div');
    el.className = 'deck-tweak-pin';
    el.style.left = cx + 'px';
    el.style.top = cy + 'px';
    el.dataset.id = m.id;
    const span = document.createElement('span');
    span.textContent = m.text ? '✓' : '!';
    el.appendChild(span);
    el.addEventListener('click', (e) => {
      e.stopPropagation();
      openPopover(m, cx, cy);
    });
    dom.markerLayer.appendChild(el);
  }

  function renderFlag(m, slide) {
    let target = null;
    try { target = slide.querySelector(m.anchor.selector); } catch (e) { /* bad selector */ }
    if (!target) return;
    const r = target.getBoundingClientRect();
    const el = document.createElement('div');
    el.className = 'deck-tweak-flag';
    el.style.left = (r.right - 8) + 'px';
    el.style.top = (r.top - 8) + 'px';
    el.textContent = m.text ? m.text.slice(0, 24) : 'flag';
    el.dataset.id = m.id;
    el.addEventListener('click', (e) => {
      e.stopPropagation();
      openPopover(m, r.right, r.top);
    });
    dom.markerLayer.appendChild(el);
  }

  function renderSticky(m, slide) {
    const { cx, cy } = slideToClient(m.anchor.x, m.anchor.y, slide);
    const el = document.createElement('div');
    el.className = 'deck-tweak-sticky';
    el.style.left = cx + 'px';
    el.style.top = cy + 'px';
    el.dataset.id = m.id;

    const chrome = document.createElement('div');
    chrome.className = 'chrome';
    const closeBtn = document.createElement('button');
    closeBtn.type = 'button';
    closeBtn.className = 'close';
    closeBtn.setAttribute('aria-label', 'Delete sticky');
    closeBtn.textContent = '×';
    closeBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      removeMarker(m.id);
    });
    chrome.appendChild(closeBtn);

    const ta = document.createElement('textarea');
    ta.value = m.text || '';
    ta.placeholder = 'Note…';
    ta.addEventListener('input', () => {
      m.text = ta.value;
      scheduleUpdate(m);
    });
    ta.addEventListener('keydown', (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
        e.preventDefault();
        ta.blur();
      } else if (e.key === 'Escape') {
        e.preventDefault();
        ta.blur();
      }
    });

    el.appendChild(chrome);
    el.appendChild(ta);
    attachStickyDrag(el, chrome, m, slide);
    dom.markerLayer.appendChild(el);
  }

  function attachStickyDrag(el, handle, m, slide) {
    let drag = null;
    handle.addEventListener('mousedown', (e) => {
      if (e.target.closest('.close')) return;
      const rect = el.getBoundingClientRect();
      drag = { dx: e.clientX - rect.left, dy: e.clientY - rect.top };
      e.preventDefault();
    });
    document.addEventListener('mousemove', (e) => {
      if (!drag) return;
      const cx = e.clientX - drag.dx;
      const cy = e.clientY - drag.dy;
      el.style.left = cx + 'px';
      el.style.top = cy + 'px';
      const p = clientToSlide(cx, cy, slide);
      m.anchor.x = p.x;
      m.anchor.y = p.y;
    });
    document.addEventListener('mouseup', () => {
      if (!drag) return;
      drag = null;
      scheduleUpdate(m);
    });
  }

  // Debounce sticky text/position updates — each keystroke firing a PUT is
  // wasteful and can saturate the dev server on fast typists.
  const updateTimers = new Map();
  function scheduleUpdate(m) {
    if (updateTimers.has(m.id)) clearTimeout(updateTimers.get(m.id));
    const t = setTimeout(() => {
      updateTimers.delete(m.id);
      updateMarker(m.id, { text: m.text, anchor: m.anchor });
    }, 400);
    updateTimers.set(m.id, t);
  }

  function openPopover(m, cx, cy) {
    closePopover();
    const pop = document.createElement('div');
    pop.className = 'deck-tweak-popover';
    pop.style.left = Math.min(cx, window.innerWidth - 240) + 'px';
    pop.style.top = Math.min(cy, window.innerHeight - 160) + 'px';

    const ta = document.createElement('textarea');
    ta.placeholder = 'Comment…';
    ta.value = m.text || '';
    pop.appendChild(ta);

    const row = document.createElement('div');
    row.className = 'row';
    const del = document.createElement('button');
    del.type = 'button';
    del.className = 'danger';
    del.textContent = 'Delete';
    del.addEventListener('click', () => {
      closePopover();
      removeMarker(m.id);
    });
    const save = document.createElement('button');
    save.type = 'button';
    save.className = 'primary';
    save.textContent = 'Save';
    const commit = () => {
      m.text = ta.value;
      updateMarker(m.id, { text: m.text });
      closePopover();
      renderMarkers();
    };
    save.addEventListener('click', commit);
    ta.addEventListener('keydown', (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') { e.preventDefault(); commit(); }
      else if (e.key === 'Escape') { e.preventDefault(); closePopover(); }
    });
    row.appendChild(del);
    row.appendChild(save);
    pop.appendChild(row);

    document.body.appendChild(pop);
    dom.popover = pop;
    setTimeout(() => ta.focus(), 30);

    // Click-outside dismiss. Registered on next tick so the current click
    // doesn't immediately fire the dismiss handler.
    setTimeout(() => {
      const off = (e) => {
        if (!dom.popover) return;
        if (dom.popover.contains(e.target)) return;
        if (e.target.closest('.deck-tweak-pin, .deck-tweak-flag')) return;
        closePopover();
        document.removeEventListener('mousedown', off, true);
      };
      document.addEventListener('mousedown', off, true);
      dom.popover.__off = off;
    }, 0);
  }

  function closePopover() {
    if (!dom.popover) return;
    if (dom.popover.__off) document.removeEventListener('mousedown', dom.popover.__off, true);
    dom.popover.remove();
    dom.popover = null;
  }

  function removeMarker(id) {
    state.markers = state.markers.filter(m => m.id !== id);
    renderMarkers();
    deleteMarker(id);
  }

  // ---- Transport ----
  // POST new marker, PUT partial updates, DELETE by id, GET list scoped to
  // a slide. All fire-and-forget w/r/t user flow; UI updates optimistically
  // and logs on failure without rolling back (dev tool, not a production app).

  async function loadMarkers() {
    const i = state.stage.index;
    try {
      const res = await fetch('/feedback?slide=' + i);
      if (!res.ok) throw new Error('HTTP ' + res.status);
      const data = await res.json();
      const list = Array.isArray(data && data.markers) ? data.markers : [];
      // Keep markers from other slides that are already in memory; replace
      // the current slide's slice with the server copy.
      state.markers = state.markers.filter(m => m.slideIndex !== i).concat(list);
      renderMarkers();
    } catch (e) {
      console.warn('[feedback] load failed:', e.message);
    }
  }

  async function saveMarker(m) {
    try {
      const res = await fetch('/feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(m),
      });
      if (!res.ok) throw new Error('HTTP ' + res.status);
    } catch (e) {
      console.warn('[feedback] save failed:', e.message);
    }
  }

  async function updateMarker(id, patch) {
    try {
      const res = await fetch('/feedback/' + encodeURIComponent(id), {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(patch),
      });
      if (!res.ok) throw new Error('HTTP ' + res.status);
    } catch (e) {
      console.warn('[feedback] update failed:', e.message);
    }
  }

  async function deleteMarker(id) {
    try {
      const res = await fetch('/feedback/' + encodeURIComponent(id), { method: 'DELETE' });
      if (!res.ok && res.status !== 404) throw new Error('HTTP ' + res.status);
    } catch (e) {
      console.warn('[feedback] delete failed:', e.message);
    }
  }

  window.__deckFeedback = { mount, open, close, toggle };
})();
