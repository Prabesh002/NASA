/* Rasuwa flood story map.
   SI disclosure: this code was written with SI assistance (Claude, Anthropic). The idea, study area and
   story text are the team's. All numbers are read from /data/river_stats.json, which is produced by
   pipeline/river_stats.py from NISAR L2 GCOV data. Nothing here is generated or estimated in the browser. */
(() => {
  "use strict";
  const $ = (s, el = document) => el.querySelector(s);
  const $$ = (s, el = document) => [...el.querySelectorAll(s)];
  const reduceMotion = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const isNarrow = () => innerWidth <= 760;
  const EVENT = "2026-08-19_2026-08-31";
  const REGION = [85.09, 27.84, 85.66, 28.43];
  const fmtDate = (iso) => new Date(iso + "T00:00:00Z").toLocaleDateString("en-GB", { day: "numeric", month: "short", timeZone: "UTC" });

  // Places: coordinates from OpenStreetMap nodes (retrieved 14 Nov 2026).
  const PLACES = [
    { name: "Langtang Lirung, 7,227 m", lngLat: [85.5166508, 28.2563528] },
    { name: "Rasuwagadhi", lngLat: [85.3777789, 28.2777749] },
    { name: "Syabrubesi", lngLat: [85.3427433, 28.164569] },
    { name: "Betrawati", lngLat: [85.1859528, 27.9731085] },
  ];

  // Camera per chapter. km = position along the traced river path used for the profile cursor.
  const CHAPTERS = {
    intro:       { center: [85.36, 28.17], zoom: 9.9, pitch: 0, bearing: 0, path: true },
    source:      { center: [85.498, 28.312], zoom: 11.9, pitch: 35, bearing: 0, kmAt: [85.50, 28.31] },
    lende:       { center: [85.435, 28.325], zoom: 11.9, pitch: 35, bearing: 20, kmAt: [85.4307, 28.3304] },
    rasuwagadhi: { center: [85.3778, 28.2778], zoom: 12.2, pitch: 40, bearing: 15, kmAt: [85.3778, 28.2778] },
    minutes:     { center: [85.30, 28.14], zoom: 10.2, pitch: 0, bearing: 0, path: true },
    syabrubesi:  { center: [85.3427, 28.1646], zoom: 12.2, pitch: 40, bearing: -20, kmAt: [85.3427, 28.1646] },
    betrawati:   { center: [85.1905, 27.979], zoom: 12.2, pitch: 35, bearing: 30, kmAt: [85.186, 27.9731] },
    season:      { center: [85.47, 28.315], zoom: 11.1, pitch: 0, bearing: 0, mode: "season" },
    glaciers:    { center: [85.53, 28.27], zoom: 10.8, pitch: 0, bearing: 0, mode: "glacier" },
    water:       { center: [85.36, 28.17], zoom: 9.9, pitch: 0, bearing: 0, path: true, mode: "water" },
    research:    { center: [85.36, 28.17], zoom: 9.9, pitch: 0, bearing: 0, path: true },
    method:      { center: [85.40, 28.24], zoom: 10.4, pitch: 0, bearing: 0, path: true, controls: true },
    prepare:     { center: [85.33, 28.15], zoom: 9.9, pitch: 0, bearing: 0, path: true },
    credits:     { center: [85.33, 28.15], zoom: 9.9, pitch: 0, bearing: 0, path: true },
  };

  let map, stats, flow, layersMeta = [], hereMarker, currentChapter = null, currentKm = null;

  /* ---------- text slots: hidden when empty; outlined on localhost so the author can see them ---------- */
  const local = ["localhost", "127.0.0.1"].includes(location.hostname);
  $$(".user-text").forEach((el) => {
    if (!el.textContent.trim() && !el.children.length) {
      el.classList.add("is-empty");
      if (local) { el.classList.add("show-slot"); el.append(`Text slot “${el.dataset.slot}” (empty; this note shows on localhost only)`); }
    }
  });

  /* ---------- geometry helpers ---------- */
  const hav = (a, b) => {
    const R = 6371.0088, r = Math.PI / 180, dLat = (b[1] - a[1]) * r, dLon = (b[0] - a[0]) * r;
    const h = Math.sin(dLat / 2) ** 2 + Math.cos(a[1] * r) * Math.cos(b[1] * r) * Math.sin(dLon / 2) ** 2;
    return 2 * R * Math.asin(Math.sqrt(h));
  };
  function preparePath(feature, lengthKm) {
    const c = feature.geometry.coordinates, cum = [0];
    for (let i = 1; i < c.length; i++) cum.push(cum[i - 1] + hav(c[i - 1], c[i]));
    const k = lengthKm / cum[cum.length - 1];        // rescale to the pipeline's UTM-measured length
    return { coords: c, km: cum.map((v) => v * k), length: lengthKm };
  }
  function pointAtKm(p, km) {
    let i = p.km.findIndex((v) => v >= km);
    if (i <= 0) return p.coords[i === 0 ? 0 : p.coords.length - 1];
    const t = (km - p.km[i - 1]) / (p.km[i] - p.km[i - 1] || 1);
    return [p.coords[i - 1][0] + t * (p.coords[i][0] - p.coords[i - 1][0]), p.coords[i - 1][1] + t * (p.coords[i][1] - p.coords[i - 1][1])];
  }
  function kmOf(p, lngLat) {
    let best = 0, d = Infinity;
    p.coords.forEach((c, i) => { const v = hav(c, lngLat); if (v < d) { d = v; best = i; } });
    return p.km[best];
  }

  /* ---------- statistics helpers (all from river_stats.json) ---------- */
  function rangePct(pathKey, pair, pol, a, b) {
    const P = stats.paths[pathKey], s = P.series[pair] && P.series[pair][pol];
    if (!s) return null;
    let n = 0, big = 0;
    P.bin_km.forEach((km, i) => {
      if (km >= a && km < b && s.pct_beyond_3dB[i] != null) { n += s.n_px[i]; big += s.pct_beyond_3dB[i] * s.n_px[i] / 100; }
    });
    return n ? (100 * big) / n : null;
  }
  const ordinaryPairs = () => stats.pairs.map((p) => p.join("_")).filter((p) => p !== EVENT);
  const median = (v) => { const s = [...v].sort((x, y) => x - y), m = s.length >> 1; return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2; };

  const INK = "#0f1a22", INK2 = "#46555f", ROSE = "#b2182b", WASH = "#eef2f4", RULE = "#d3dbe0";

  /* ---------- per-stop comparison: flood 12 days against ordinary 12 days ---------- */
  function fillMeasures() {
    const F = stats.paths.flood, pk = F.places_km, R = pk.Rasuwagadhi.km, S = pk.Syabrubesi.km, B = pk.Betrawati.km;
    const J = kmOf(flow, [85.4307, 28.3304]);           // where the traced tributary meets the Lende Khola (OSM)
    const ranges = { source: [0, J], lende: [J, R], rasuwagadhi: [R, R + 5], syabrubesi: [R + 5, S + 2], betrawati: [S + 2, B] };
    const rows = {};
    for (const [key, [a, b]] of Object.entries(ranges)) {
      const ev = rangePct("flood", EVENT, "HHHH", a, b);
      const ord = ordinaryPairs().map((p) => rangePct("flood", p, "HHHH", a, b)).filter((v) => v != null);
      rows[key] = { a, b, ev, ord };
    }
    const scale = Math.max(1, ...Object.values(rows).map((r) => r.ev ?? 0));
    for (const [key, { a, b, ev, ord }] of Object.entries(rows)) {
      const lab = $(`[data-km-label="${key}"]`); if (lab) lab.textContent = `Kilometre ${a.toFixed(0)} to ${b.toFixed(0)} of the flood path`;
      const box = $(`[data-measure="${key}"]`); if (!box || ev == null) continue;
      let html = "";
      if (ord.length) {
        const med = median(ord), mx = Math.max(...ord), ratio = ev / med;
        html += `<p class="stat"><b>${ev.toFixed(0)}%</b><span>of the riverside changed here</span></p>`
          + `<div class="cmp" role="img" aria-label="Flood 12 days ${ev.toFixed(1)} percent, normal 12 days ${med.toFixed(1)} percent">`
          + `<span>Flood</span><span class="track"><i class="f" style="width:${(100 * ev) / scale}%"></i></span><span class="val">${ev.toFixed(0)}%</span>`
          + `<span>Normal</span><span class="track"><i class="o" style="width:${(100 * med) / scale}%"></i></span><span class="val">${med.toFixed(1)}%</span></div>`
          + `<p class="vs">${ev > mx ? `About ${ratio >= 10 ? ratio.toFixed(0) : ratio.toFixed(1)} times a normal 12 days.` : `Inside the normal range for this stretch (up to ${mx.toFixed(1)}%).`}</p>`;
      } else {
        html += `<p class="stat"><b>${ev.toFixed(0)}%</b><span>of the riverside changed here</span></p>`;
      }
      box.innerHTML = html;
    }
    document.addEventListener("click", (e) => { const g = e.target.closest("[data-goto]"); if (g) { setMode("flood"); goChapter(g.dataset.goto, true); } });
  }

  /* ---------- dot plot: flood path vs control rivers, every 12-day step ---------- */
  function drawDotplot() {
    const el = $("#dotplot"), keys = Object.keys(stats.paths), W = 440, rowH = 50, L = 8, top = 8;
    const all = keys.flatMap((k) => Object.values(stats.paths[k].series).map((s) => s.HHHH.whole_path.pct_beyond_3dB));
    const max = Math.max(5, Math.ceil(Math.max(...all) / 5) * 5), x = (v) => L + (v / max) * (W - L - 16);
    let svg = `<svg viewBox="0 0 ${W} ${top + keys.length * rowH + 26}" xmlns="http://www.w3.org/2000/svg">`;
    for (let t = 0; t <= max; t += 5) svg += `<line x1="${x(t)}" x2="${x(t)}" y1="${top}" y2="${top + keys.length * rowH}" stroke="#d3dbe0"/><text x="${x(t)}" y="${top + keys.length * rowH + 16}" text-anchor="${t ? "middle" : "start"}">${t}%</text>`;
    keys.forEach((k, r) => {
      const y = top + r * rowH, P = stats.paths[k];
      svg += `<text class="row-label" x="${L}" y="${y + 15}">${{ flood: "Flood path", lende_upper: "Upper Lende Khola", kyirong: "Kyirong Tsangpo", langtang: "Langtang Khola", chilime: "Chilime Khola" }[k] || P.label}</text>`;
      for (const [pair, s] of Object.entries(P.series)) {
        const v = s.HHHH.whole_path.pct_beyond_3dB, ev = pair === EVENT;
        svg += `<circle cx="${x(v)}" cy="${y + 31}" r="${ev ? 7 : 5}" fill="${ev ? "#b2182b" : "#ffffff"}" stroke="${ev ? "#b2182b" : "#46555f"}" stroke-width="1.5"><title>${pair.replace("_", " to ")}: ${v}%</title></circle>`;
      }
    });
    el.innerHTML = svg + "</svg>";
    const n = ordinaryPairs().length, F = stats.paths.flood.series[EVENT].HHHH.whole_path;
    $("#dotplot-note").textContent = `Share of pixels within ${stats.buffer_m} m of each river line whose HH backscatter changed by more than 3 dB. `
      + `Flood path, flood step: ${F.pct_beyond_3dB}% of ${F.n_px.toLocaleString("en")} pixels. `
      + (n ? `${n} ordinary steps shown as open dots (${ordinaryPairs().map((p) => fmtDate(p.slice(0, 10))).join(", ")} start dates). ` : "Ordinary steps are still being processed. ")
      + "Track 98 ascending, NISAR L2 GCOV provisional.";
  }

  /* ---------- river profile strip ---------- */
  function drawProfile() {
    const svg = $("#profile-svg"), W = svg.clientWidth, H = svg.clientHeight;
    if (!W || !H) return;
    const F = stats.paths.flood, len = F.length_km, padB = 17, top = 14, x = (km) => (km / len) * W;
    const ev = F.series[EVENT].HHHH.pct_beyond_3dB;
    const ords = ordinaryPairs().map((p) => F.series[p].HHHH.pct_beyond_3dB);
    const ordMax = F.bin_km.map((_, i) => { const v = ords.map((o) => o[i]).filter((q) => q != null); return v.length ? Math.max(...v) : null; });
    const ymax = Math.max(...ev.filter((v) => v != null), 10), y = (v) => top + (1 - v / ymax) * (H - padB - top);
    const pts = (arr) => arr.map((v, i) => `L${x(F.bin_km[i]).toFixed(1)},${y(v ?? 0).toFixed(1)}`).join("");
    let h = `<path d="M0,${y(0)}${pts(ev)}L${W},${y(0)}Z" fill="${ROSE}"/>`;
    if (ords.length) h += `<path d="M0,${y(0)}${pts(ordMax)}L${W},${y(0)}Z" fill="#fff" opacity="0.55"/><path d="M0,${y(ordMax[0] ?? 0)}${pts(ordMax)}" fill="none" stroke="${INK}" stroke-width="1.5"/>`;
    h += `<line x1="0" x2="${W}" y1="${y(0)}" y2="${y(0)}" stroke="${RULE}"/><text x="2" y="${top - 3}">${ymax.toFixed(0)}% changed</text>`;
    const marks = [["Source", 0], ...Object.entries(F.places_km).map(([n, v]) => [n, v.km])];
    marks.forEach(([n, km]) => {
      const end = km > len - 4;
      h += `<line x1="${x(km)}" x2="${x(km)}" y1="${top}" y2="${y(0)}" stroke="${INK}" stroke-dasharray="2 3"/>`
        + `<text class="place" x="${x(km) + (end ? -4 : 4)}" y="${H - 3}" text-anchor="${end ? "end" : "start"}">${n}, km ${km.toFixed(0)}</text>`;
    });
    if (currentKm != null) h += `<line x1="${x(currentKm)}" x2="${x(currentKm)}" y1="0" y2="${y(0)}" stroke="${INK}" stroke-width="3"/>`;
    svg.innerHTML = h;
    const rest = ords.length ? "Red: flood. Black line: highest ordinary period. Click to go there." : "Red: flood 12 days. Click to go there.";
    svg.onmousemove = (e) => {
      const km = Math.min(len, Math.max(0, (e.offsetX / W) * len)), i = Math.min(F.bin_km.length - 1, Math.floor(km / (stats.bin_m / 1000)));
      $("#profile-readout").textContent = `km ${km.toFixed(1)}: flood ${ev[i] ?? "–"}%` + (ords.length ? `, highest ordinary ${ordMax[i] ?? "–"}%` : "");
    };
    svg.onmouseleave = () => { $("#profile-readout").textContent = rest; };
    svg.onmouseleave();
    svg.onclick = (e) => {
      const km = (e.offsetX / W) * len;
      stopPlay(); setHere(km);
      map[reduceMotion ? "jumpTo" : "flyTo"]({ center: pointAtKm(flow, km), zoom: Math.max(map.getZoom(), 12.5), essential: true });
    };
  }
  function setHere(km) {
    currentKm = km;
    if (km == null) hereMarker.remove(); else hereMarker.setLngLat(pointAtKm(flow, km)).addTo(map);
    drawProfile();
  }

  /* ---------- maps ---------- */
  const DEM = "https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png";
  const tileUrl = (name) => `${location.origin}/tiles/${name}/{z}/{x}/{y}.webp`;
  let style, fpData, view = "flood";
  const TERRAIN = { source: "dem", exaggeration: 1 };

  function makeMap(container, interactive) {
    return new maplibregl.Map({ container, style, center: CHAPTERS.intro.center, zoom: CHAPTERS.intro.zoom - (isNarrow() ? 1.3 : 0.4),
      maxBounds: [[84.3, 27.3], [86.4, 29.0]], minZoom: 8, maxZoom: 15.5, maxPitch: 70, interactive,
      cooperativeGestures: interactive, attributionControl: interactive ? { compact: isNarrow() } : false });
  }
  // Radar layers, terrain and the traced path. Identical on both maps so the slider compares like with like.
  function addData(m) {
    const firstSymbol = m.getStyle().layers.find((l) => l.type === "symbol")?.id;
    m.addSource("dem", { type: "raster-dem", tiles: [DEM], tileSize: 256, maxzoom: 14, encoding: "terrarium", attribution: "Terrain: Mapzen Terrain Tiles (AWS Open Data)" });
    m.addSource("dem-shade", { type: "raster-dem", tiles: [DEM], tileSize: 256, maxzoom: 14, encoding: "terrarium" });
    m.addLayer({ id: "hillshade", type: "hillshade", source: "dem-shade",
      paint: { "hillshade-exaggeration": 0.28, "hillshade-shadow-color": "#5d6e79", "hillshade-highlight-color": "#ffffff", "hillshade-accent-color": "#93a3ad" } }, firstSymbol);
    if (m === map) m.setTerrain(TERRAIN);   // true vertical scale, no exaggeration. The comparison map stays flat (see setView).
    const add = (meta) => {
      m.addSource(meta.layer, { type: "raster", tiles: [tileUrl(meta.layer)], tileSize: 256, minzoom: meta.minzoom, maxzoom: meta.maxzoom, bounds: meta.bounds,
        attribution: "Radar: NISAR (NASA/JPL, ISRO) via ASF DAAC" });
      m.addLayer({ id: meta.layer, type: "raster", source: meta.layer, layout: { visibility: "none" },
        paint: { "raster-opacity": meta.kind === "sar" ? 0.95 : 1, "raster-fade-duration": 150, "raster-resampling": "linear" } }, firstSymbol);
    };
    layersMeta.filter((x) => x.kind === "sar").forEach(add);
    layersMeta.filter((x) => x.kind === "change").forEach(add);

    m.addSource("flow", { type: "geojson", data: fpData });
    m.addSource("flowline", { type: "geojson", lineMetrics: true, data: fpData.features.find((f) => f.properties.id === "flood") });
    m.addLayer({ id: "controls", type: "line", source: "flow", filter: ["all", ["==", ["geometry-type"], "LineString"], ["!=", ["get", "id"], "flood"]],
      paint: { "line-color": INK2, "line-width": 2, "line-dasharray": [2, 2], "line-opacity": 0, "line-opacity-transition": { duration: 600 } } });
    m.addLayer({ id: "flowpath-case", type: "line", source: "flowline", layout: { "line-cap": "round", "line-join": "round" },
      paint: { "line-color": "#ffffff", "line-width": 5, "line-opacity": 0.9, "line-opacity-transition": { duration: 600 } } });
    m.addLayer({ id: "flowpath", type: "line", source: "flowline", layout: { "line-cap": "round", "line-join": "round" },
      paint: { "line-color": INK, "line-width": 2, "line-opacity": 0.9, "line-opacity-transition": { duration: 600 } } });
    m.addLayer({ id: "flowplay", type: "line", source: "flowline", layout: { "line-cap": "round", "line-join": "round", visibility: "none" },
      paint: { "line-width": 7, "line-gradient": ["step", ["line-progress"], INK, 0.0001, "rgba(0,0,0,0)"] } });
    m.addLayer({ id: "control-labels", type: "symbol", source: "flow", filter: ["all", ["==", ["geometry-type"], "LineString"], ["!=", ["get", "id"], "flood"]],
      layout: { "symbol-placement": "line-center", "text-field": ["get", "label"], "text-font": ["Noto Sans Regular"], "text-size": 12, visibility: "none" },
      paint: { "text-color": INK, "text-halo-color": "#ffffff", "text-halo-width": 2 } });
    m.addLayer({ id: "km-marks", type: "symbol", source: "flow", filter: ["==", ["get", "id"], "km"], minzoom: 10.5,
      layout: { "text-field": ["concat", "km ", ["to-string", ["get", "km"]]], "text-font": ["Noto Sans Bold"], "text-size": 12, "text-offset": [0, -1.1], "text-allow-overlap": false },
      paint: { "text-color": INK, "text-halo-color": "#ffffff", "text-halo-width": 2 } });
    PLACES.forEach((p) => new maplibregl.Marker({ element: Object.assign(document.createElement("div"), { className: "place-marker", textContent: p.name }), anchor: "left", offset: [-5, 0] })
      .setLngLat(p.lngLat).addTo(m));
  }
  const showOnly = (m, kind, name) => layersMeta.filter((x) => x.kind === kind).forEach((x) => m.setLayoutProperty(x.layer, "visibility", x.layer === name ? "visible" : "none"));
  const pathStyle = (m, c) => {
    ["flowpath", "flowpath-case"].forEach((id) => m.setPaintProperty(id, "line-opacity", c.path ? 0.9 : 0));
    m.setPaintProperty("controls", "line-opacity", c.controls ? 0.9 : 0);
    m.setLayoutProperty("control-labels", "visibility", c.controls ? "visible" : "none");
  };

  /* ---------- what the map shows: flood, ordinary, or both with a slider ---------- */
  function applyLayers() {
    const on = $("#chg-on").checked, flood = $("#flood-select").value, ord = $("#base-select").value, bg = $("#bg-select").value;
    showOnly(map, "change", !on ? null : mode === "season" ? seasonSteps()[seasonIdx].layer : mode === "flood" ? flood : null);
    showOnly(map, "sar", bg);
    if (map2Ready) { showOnly(map2, "change", on ? ord : null); showOnly(map2, "sar", bg); }
    const o = $("#base-select").selectedOptions[0];
    $("#tag-left").textContent = o ? `Ordinary${isNarrow() ? "" : " 12 days"}, ${o.textContent}` : "";
    $(".side-tag.right").textContent = `Flood${isNarrow() ? "" : " 12 days"}, 19 to 31 Aug`;
  }
  function setView(v) {
    view = v;
    const cmp = v === "compare";
    $("#cmp-btn").setAttribute("aria-pressed", cmp);
    if (cmp) closeCard();
    document.body.classList.toggle("comparing", cmp);
    // 3D terrain shifts each map's zoom by the ground height under its centre, so the two sides can drift apart.
    // Both sides are drawn flat while comparing, which keeps them at exactly the same scale.
    if (map.getSource("dem")) map.setTerrain(cmp ? null : TERRAIN);
    $("#swipe").hidden = !cmp;
    if (cmp && !map2) {
      map2 = makeMap("map2", false);
      map2.on("load", () => { addData(map2); map2Ready = true; pathStyle(map2, CHAPTERS[currentChapter] || CHAPTERS.intro); applyLayers(); syncMap2(); });
    }
    if (cmp) { map2.resize(); syncMap2(); setSwipe($("#swipe-range").value); }
    applyLayers();
  }
  const syncMap2 = () => { if (map2 && view === "compare") map2.jumpTo({ center: map.getCenter(), zoom: map.getZoom(), bearing: map.getBearing(), pitch: map.getPitch(), padding: map.getPadding() }); };
  function setSwipe(pct) {
    $("#swipe").style.setProperty("--x", pct + "%");
    $("#map2").style.clipPath = `inset(0 ${100 - pct}% 0 0)`;
  }

  /* ---------- play the traced path from the source to Betrawati ---------- */
  // This animates the line that the river follows. It is not a flood simulation: the speed is constant and arbitrary.
  // The clock times are the ones in the page timeline (ICIMOD, Nepal time, 26 Aug 2026).
  let playRaf = 0;
  const PLAY_NOTE = "<small>This draws the traced river path at a steady speed. It is not a flood simulation. Times are as reported by ICIMOD (Nepal time, 26 August); some scientists doubt the reported arrival times.</small>";
  function playSteps() {
    const pk = stats.paths.flood.places_km;
    return [
      { km: 0, t: "Source, km 0", d: "8:37, seismic signal of the collapse" },
      { km: pk.Rasuwagadhi.km, t: `Rasuwagadhi, km ${pk.Rasuwagadhi.km.toFixed(0)}`, d: "8:40, reported arrival of the flood" },
      { km: pk.Syabrubesi.km, t: `Syabrubesi, km ${pk.Syabrubesi.km.toFixed(0)}`, d: "No arrival time reported in our source" },
      { km: pk.Betrawati.km - 0.2, t: `Betrawati, km ${pk.Betrawati.km.toFixed(0)}`, d: "9:20, reported arrival" },
    ];
  }
  function drawPlay(frac) {
    const f = Math.min(0.9999, Math.max(0.0001, frac));
    map.setPaintProperty("flowplay", "line-gradient", ["step", ["line-progress"], INK, f, "rgba(0,0,0,0)"]);
    const km = frac * flow.length, step = playSteps().filter((s) => s.km <= km).pop();
    hereMarker.setLngLat(pointAtKm(flow, km)).addTo(map);
    $("#play-note").innerHTML = `<b>${step.t}</b>${step.d}${PLAY_NOTE}`;
  }
  function stopPlay(keep) {
    cancelAnimationFrame(playRaf); playRaf = 0;
    const btn = $("#play-btn"); btn.classList.remove("playing"); btn.textContent = "Play the flood path";
    if (!keep) { $("#play-note").hidden = true; if (map.getLayer("flowplay")) map.setLayoutProperty("flowplay", "visibility", "none"); }
  }
  function startPlay() {
    if (mode !== "flood") setMode("flood");
    setView("flood"); closeCard();
    const btn = $("#play-btn"); btn.classList.add("playing"); btn.textContent = "Stop";
    currentChapter = null; currentKm = null; drawProfile();
    $$(".chapter").forEach((s) => s.classList.remove("is-active"));
    fitPath(reduceMotion ? 0 : 1200, true);
    pathStyle(map, { path: true });
    map.setLayoutProperty("flowplay", "visibility", "visible");
    $("#play-note").hidden = false;
    if (reduceMotion) { drawPlay(1); stopPlay(true); return; }
    drawPlay(0);
    const t0 = performance.now() + 1300, dur = 16000;
    const tick = (now) => {
      const f = Math.min(1, Math.max(0, (now - t0) / dur));
      drawPlay(f);
      if (f < 1) playRaf = requestAnimationFrame(tick); else stopPlay(true);
    };
    playRaf = requestAnimationFrame(tick);
  }

  // Whole traced path in view, clear of the controls and the legend.
  function fitPath(duration, playing) {
    const c = flow.coords, b = c.reduce((bb, p) => bb.extend(p), new maplibregl.LngLatBounds(c[0], c[0]));
    const padding = isNarrow() ? { top: 112, bottom: playing ? 120 : 56, left: 24, right: 70 } : { top: playing ? 190 : 90, bottom: 80, left: 60, right: 200 };
    map.fitBounds(b, { padding, pitch: 0, bearing: 0, duration, essential: true });
  }

  /* ---------- story scroll ---------- */
  function goChapter(id, force) {
    if ((!force && id === currentChapter) || !CHAPTERS[id]) return;
    stopPlay();
    currentChapter = id;
    if ((CHAPTERS[id].mode || "flood") !== mode) setMode(CHAPTERS[id].mode || "flood");
    $$(".chapter").forEach((s) => s.classList.toggle("is-active", s.dataset.chapter === id));
    const c = CHAPTERS[id];
    if (c.path && !c.controls) fitPath(reduceMotion ? 0 : 2200);
    else {
      const cam = { center: c.center, zoom: c.zoom - (isNarrow() ? 0.9 : 0), pitch: c.pitch, bearing: c.bearing };
      if (reduceMotion) map.jumpTo(cam); else map.flyTo({ ...cam, duration: 2200, essential: true });
    }
    pathStyle(map, c); if (map2Ready) pathStyle(map2, c);
    setHere(c.kmAt ? kmOf(flow, c.kmAt) : null);
    if ($("#stepper")) updateStepper();
  }
  function onScroll() {
    if (playRaf) return;
    const line = isNarrow() ? innerHeight * 0.62 : innerHeight * 0.4;
    let hit = null;
    for (const s of $$(".chapter")) { if (s.getBoundingClientRect().top <= line) hit = s.dataset.chapter; }
    if (hit) goChapter(hit);
  }

  /* ================= tabs: flood, season, glaciers, water paths ================= */
  let mode = "flood", glacierMeta = null, terrainMeta = null, seasonIdx = 0, seasonTimer = 0, pin = null;
  const TEAL = "#0b7285", LOW10 = "rgb(120,60,160)", LOW20 = "rgb(230,159,0)";
  const seasonSteps = () => {
    const have = new Set(layersMeta.map((m) => m.layer));
    return stats.pairs.map(([a, b]) => ({ a, b, event: `${a}_${b}` === EVENT, layer: `${a}_${b}` === EVENT ? "chg-098A-hh" : `base-098A-hh-${a.slice(5, 7)}${a.slice(8, 10)}` }))
      .filter((s) => have.has(s.layer));
  };
  const wholePct = (s) => stats.paths.flood.series[`${s.a}_${s.b}`].HHHH.whole_path.pct_beyond_3dB;

  function addExtras() {
    const vis = { visibility: "none" }, empty = { type: "FeatureCollection", features: [] };
    const t = terrainMeta.lowground.bounds_lonlat;   // w, s, e, n
    map.addSource("low-img", { type: "image", url: "/data/lowground.png", coordinates: [[t[0], t[3]], [t[2], t[3]], [t[2], t[1]], [t[0], t[1]]] });
    map.addLayer({ id: "low-img", type: "raster", source: "low-img", layout: vis, paint: { "raster-fade-duration": 0, "raster-resampling": "nearest" } }, "controls");
    map.addSource("glacier-img", { type: "image", url: "/data/glacier/" + glacierMeta.overlay_files[+$("#glacier-range").value], coordinates: glacierMeta.corners_lonlat });
    map.addLayer({ id: "glacier-img", type: "raster", source: "glacier-img", layout: vis, paint: { "raster-fade-duration": 0, "raster-resampling": "nearest" } }, "controls");
    map.addSource("glaciers", { type: "geojson", data: "/data/glacier/glaciers.geojson" });
    map.addLayer({ id: "glaciers", type: "line", source: "glaciers", layout: vis, paint: { "line-color": INK2, "line-width": 1 } }, "controls");
    map.addSource("lakes", { type: "geojson", data: "/data/glacial_lakes.geojson" });
    map.addLayer({ id: "lakes", type: "fill", source: "lakes", layout: vis, paint: { "fill-color": TEAL, "fill-opacity": 0.85 } });
    map.addSource("lake-pts", { type: "geojson", data: empty });
    fetch("/data/glacial_lakes.geojson").then((r) => r.json()).then((g) => map.getSource("lake-pts").setData({ type: "FeatureCollection",
      features: g.features.map((f) => ({ type: "Feature", properties: f.properties, geometry: { type: "Point", coordinates: [f.properties.lon, f.properties.lat] } })) }));
    map.addLayer({ id: "lakes-ring", type: "circle", source: "lake-pts", layout: vis,
      paint: { "circle-radius": 9, "circle-color": "rgba(0,0,0,0)", "circle-stroke-color": TEAL, "circle-stroke-width": 2.5 } });
    map.addSource("route", { type: "geojson", data: empty });
    map.addLayer({ id: "route-case", type: "line", source: "route", layout: { "line-cap": "round", "line-join": "round" }, paint: { "line-color": "#fff", "line-width": 7 } });
    map.addLayer({ id: "route", type: "line", source: "route", layout: { "line-cap": "round", "line-join": "round" }, paint: { "line-color": INK, "line-width": 3.5 } });
    pin = new maplibregl.Marker({ element: Object.assign(document.createElement("div"), { className: "pin-marker" }) });
    map.on("click", onMapClick);
    map.on("mouseenter", "lakes-ring", () => { map.getCanvas().style.cursor = "pointer"; });
    map.on("mouseleave", "lakes-ring", () => { map.getCanvas().style.cursor = ""; });
  }

  const LEGEND = {
    flood: [[`<i class="sw rose"></i>Ground changed: echo stronger`, `<i class="sw fell"></i>Ground changed: echo weaker`, `<i class="sw line"></i>Traced flood path`], "Click any spot for its radar record on ten dates."],
    season: [[`<i class="sw rose"></i>Echo stronger than 12 days before`, `<i class="sw fell"></i>Echo weaker`], "Drag the slider or press Play. Click any spot for its record."],
    glacier: [[`<i class="sw fell"></i>Echo lower than on 20 Jun`, `<i class="sw rose"></i>Echo higher`, `<i class="sw ring"></i>Glacial lake (click one)`], "Blue on high snow may be a sign of surface melt. We have not verified it."],
    water: [[`<i class="sw" style="background:${LOW10}"></i>Under 10 m above the river`, `<i class="sw" style="background:${LOW20}"></i>10 to 20 m above`, `<i class="sw line"></i>Downhill route`], "Click the map to drop water. The route follows the shape of the land and does not forecast a flood."],
  };
  function setMode(m) {
    if (m !== "flood" && view === "compare") setView("flood");
    stopPlay(); seasonPlay(false);
    mode = m; document.body.dataset.mode = m;
    $$("#modes button").forEach((b) => b.setAttribute("aria-pressed", b.dataset.mode === m));
    $$("#subbar > div").forEach((d) => { d.hidden = d.dataset.for !== m; });
    const show = (id, on) => map.getLayer(id) && map.setLayoutProperty(id, "visibility", on ? "visible" : "none");
    show("glacier-img", m === "glacier"); show("glaciers", m === "glacier");
    show("lakes", m === "glacier" || m === "water"); show("lakes-ring", m === "glacier" || m === "water");
    show("low-img", m === "water" && $("#low-on").checked);
    show("km-marks", m === "flood" || m === "season");
    $("#legend-keys").innerHTML = LEGEND[m][0].map((k) => `<span>${k}</span>`).join("");
    $("#legend-tip").textContent = LEGEND[m][1];
    closeCard();
    if (m === "season") setSeason(seasonIdx);
    if (m === "glacier") setGlacier(+$("#glacier-range").value);
    applyLayers();
  }

  /* ---------- season: every 12-day step in order ---------- */
  function setSeason(i) {
    const steps = seasonSteps(); seasonIdx = Math.max(0, Math.min(steps.length - 1, i));
    const s = steps[seasonIdx];
    $("#season-range").max = steps.length - 1; $("#season-range").value = seasonIdx;
    $("#season-label").innerHTML = `<b>${fmtDate(s.a)} to ${fmtDate(s.b)}</b> ${s.event ? "The flood." : "A normal period."} ${wholePct(s).toFixed(1)}% of the riverside changed.`;
    applyLayers();
  }
  function seasonPlay(on) {
    clearInterval(seasonTimer); seasonTimer = 0;
    const b = $("#season-play"); b.classList.toggle("playing", !!on); b.textContent = on ? "Pause" : "Play";
    if (!on) return;
    if (seasonIdx >= seasonSteps().length - 1) setSeason(0);
    seasonTimer = setInterval(() => { if (seasonIdx >= seasonSteps().length - 1) seasonPlay(false); else setSeason(seasonIdx + 1); }, reduceMotion ? 2600 : 1700);
  }
  function drawSeasonFig() {
    const steps = seasonSteps(), W = 440, H = 190, L = 34, B = 44, T = 14, max = Math.ceil(Math.max(...steps.map(wholePct)) / 5) * 5;
    const bw = (W - L - 6) / steps.length, y = (v) => T + (1 - v / max) * (H - T - B);
    let s = `<svg viewBox="0 0 ${W} ${H}" xmlns="http://www.w3.org/2000/svg">`;
    for (let t = 0; t <= max; t += 5) s += `<line x1="${L}" x2="${W}" y1="${y(t)}" y2="${y(t)}" stroke="${RULE}"/><text x="${L - 6}" y="${y(t) + 4}" text-anchor="end">${t}%</text>`;
    steps.forEach((st, i) => {
      const v = wholePct(st), x = L + i * bw + 5;
      s += `<rect x="${x}" y="${y(v)}" width="${bw - 10}" height="${Math.max(1.5, y(0) - y(v))}" rx="3" fill="${st.event ? ROSE : INK2}"><title>${fmtDate(st.a)} to ${fmtDate(st.b)}: ${v}%</title></rect>`
        + `<text x="${x + (bw - 10) / 2}" y="${y(v) - 5}" text-anchor="middle" class="row-label">${v.toFixed(1)}</text>`
        + `<text x="${x + (bw - 10) / 2}" y="${H - B + 16}" text-anchor="middle">${fmtDate(st.a).replace(" ", " ")}</text>`
        + `<text x="${x + (bw - 10) / 2}" y="${H - B + 31}" text-anchor="middle">${st.event ? "flood" : ""}</text>`;
    });
    $("#season-fig").innerHTML = s + "</svg>";
    $("#season-note").textContent = `Share of ground within ${stats.buffer_m} m of the flood path that changed by more than 3 dB in each 12-day period (start date under each bar). The archive we used has no pair between 26 July and 19 August, so that stretch is missing. NISAR track 98, HH.`;
  }

  /* ---------- the headline finding in plain terms ---------- */
  function drawFinding() {
    const F = stats.paths.flood, ev = F.series[EVENT].HHHH.whole_path, ord = ordinaryPairs().map((p) => F.series[p].HHHH.whole_path.pct_beyond_3dB);
    if (!ord.length) return;
    const med = median(ord), lo = Math.min(...ord), hi = Math.max(...ord);
    const grid = (n, cls) => `<span class="grid100" aria-hidden="true">${Array.from({ length: 100 }, (_, i) => `<i class="${i < n ? cls : ""}"></i>`).join("")}</span>`;
    $("#finding").innerHTML = ``
      + `<p class="say">After the flood, about <b>1 in ${Math.round(100 / ev.pct_beyond_3dB)}</b> patches of ground beside the river looked different to the radar. In a normal 12 days it is about <b>1 in ${Math.round(100 / med)}</b>.</p>`
      + `<div class="grids"><figure>${grid(Math.round(ev.pct_beyond_3dB), "f")}<figcaption><b>Flood 12 days</b>${Math.round(ev.pct_beyond_3dB)} of every 100 patches changed</figcaption></figure>`
      + `<figure>${grid(Math.max(1, Math.round(med)), "o")}<figcaption><b>Ordinary 12 days</b>about ${Math.max(1, Math.round(med))} of every 100</figcaption></figure></div>`
      + `<details class="sources"><summary>Exact figures</summary><p>${ev.pct_beyond_3dB}% of ${ev.n_px.toLocaleString("en")} radar pixels within ${stats.buffer_m} m of the ${F.length_km.toFixed(0)} km flood path changed by more than 3 dB (a doubling or halving of the echo) between 19 and 31 August. In ${ord.length} other 12-day periods the figure ran from ${lo}% to ${hi}%, median ${med}%. “Patch” means one 10 m radar pixel.</p></details>`;
  }

  /* ---------- glaciers ---------- */
  function setGlacier(i) {
    const d = glacierMeta.overlay_dates[i];
    $("#glacier-label").innerHTML = `Glacier echo on <b>${fmtDate(d)}</b> against ${fmtDate(glacierMeta.reference_date)}. Blue = weaker, a possible sign of melt.`;
    const src = map.getSource("glacier-img");
    if (src) src.updateImage({ url: "/data/glacier/" + glacierMeta.overlay_files[i], coordinates: glacierMeta.corners_lonlat });
  }
  function drawGlacierFig() {
    const G = glacierMeta, b = G.bands[G.bands.length - 1], sh = b.share_fell_3db_vs_first, n = G.dates.length;
    const W = 440, H = 180, L = 34, B = 30, T = 16, max = Math.ceil(Math.max(...sh) / 10) * 10, bw = (W - L - 6) / n, y = (v) => T + (1 - v / max) * (H - T - B);
    let s = `<svg viewBox="0 0 ${W} ${H}" xmlns="http://www.w3.org/2000/svg">`;
    for (let t = 0; t <= max; t += 10) s += `<line x1="${L}" x2="${W}" y1="${y(t)}" y2="${y(t)}" stroke="${RULE}"/><text x="${L - 6}" y="${y(t) + 4}" text-anchor="end">${t}%</text>`;
    sh.forEach((v, i) => {
      const x = L + i * bw + 4;
      s += `<rect x="${x}" y="${y(v)}" width="${bw - 8}" height="${Math.max(1.5, y(0) - y(v))}" rx="3" fill="#2166ac"><title>${fmtDate(G.dates[i])}: ${v}%</title></rect>`
        + (i % 2 === 0 ? `<text x="${x + (bw - 8) / 2}" y="${H - B + 16}" text-anchor="middle">${fmtDate(G.dates[i]).replace(" ", "\u00a0")}</text>` : "");
    });
    $("#glacier-fig").innerHTML = s + "</svg>";
    const k = sh.indexOf(Math.max(...sh));
    $("#glacier-say").innerHTML = `Ice above ${b.from_m.toLocaleString("en")} m with a much weaker echo than on 20 June: <b>${sh[k].toFixed(0)}%</b> by ${fmtDate(G.dates[k])}, back to ${sh[n - 1].toFixed(0)}% by ${fmtDate(G.dates[n - 1])}.`;
    $("#lake-say").innerHTML = `The rings are ${terrainMeta.lakes.count} glacial lakes from a NASA inventory. Click one to see where its water would run.`;
  }

  /* ---------- card ---------- */
  function showCard(html) { $("#card-body").innerHTML = html; $("#card").hidden = false; }
  function closeCard() { $("#card").hidden = true; if (pin) pin.remove(); const r = map.getSource("route"); if (r) r.setData({ type: "FeatureCollection", features: [] }); }

  /* ---------- click a spot: its radar record on ten dates ---------- */
  let series = null, seriesP = null;
  const MERC = 6378137, mercX = (lon) => (lon * Math.PI / 180) * MERC, mercY = (lat) => Math.log(Math.tan(Math.PI / 4 + (lat * Math.PI) / 360)) * MERC;
  async function loadGrey(url, w, h) {
    const img = new Image(); img.src = url; await img.decode();
    const c = Object.assign(document.createElement("canvas"), { width: w, height: h }), ctx = c.getContext("2d", { willReadFrequently: true });
    ctx.drawImage(img, 0, 0);
    const d = ctx.getImageData(0, 0, w, h).data, out = new Uint8Array(w * h);
    for (let i = 0; i < out.length; i++) out[i] = d[i * 4];
    return out;
  }
  function loadSeries() {
    seriesP ??= (async () => {
      const meta = await fetch("/data/series/series.json").then((r) => r.json());
      const bands = await Promise.all(meta.files.map((f) => loadGrey("/data/series/" + f, meta.width, meta.height)));
      series = { meta, bands }; return series;
    })();
    return seriesP;
  }
  async function inspect(lngLat) {
    pin.setLngLat(lngLat).addTo(map);
    const where = `${Math.abs(lngLat.lat).toFixed(4)}°${lngLat.lat >= 0 ? "N" : "S"}, ${Math.abs(lngLat.lng).toFixed(4)}°${lngLat.lng >= 0 ? "E" : "W"}`;
    if (!series) showCard(`<h3>Reading the radar record</h3><p>Loading ten radar images (about 8 MB, first click only).</p>`);
    const { meta, bands } = await loadSeries();
    const col = Math.floor((mercX(lngLat.lng) - meta.x0) / meta.cell_m_mercator), row = Math.floor((meta.y1 - mercY(lngLat.lat)) / meta.cell_m_mercator);
    const inside = col >= 0 && row >= 0 && col < meta.width && row < meta.height;
    const v = bands.map((b) => { const q = inside ? b[row * meta.width + col] : 0; return q ? +(meta.db_min + (q - 1) * meta.db_step).toFixed(2) : null; });
    if (v.every((q) => q == null)) { showCard(`<h3>No radar data here</h3><p>${where} is outside the area we processed, or the radar could not see it. Try a spot nearer the river.</p>`); return; }
    const t = meta.dates.map((d) => Date.parse(d)), n = t.length, iA = meta.dates.indexOf(meta.event_between[0]), iB = meta.dates.indexOf(meta.event_between[1]);
    const W = 320, H = 150, L = 34, T = 10, B = 24, ok = v.filter((q) => q != null), lo = Math.floor(Math.min(...ok) - 0.5), hi = Math.ceil(Math.max(...ok) + 0.5);
    const x = (i) => L + ((t[i] - t[0]) / (t[n - 1] - t[0])) * (W - L - 8), y = (q) => T + ((hi - q) / (hi - lo)) * (H - T - B);
    let s = `<svg viewBox="0 0 ${W} ${H}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Radar brightness on ten dates">`
      + `<rect x="${x(iA)}" y="${T}" width="${x(iB) - x(iA)}" height="${H - T - B}" fill="${ROSE}" opacity="0.14"/><text x="${(x(iA) + x(iB)) / 2}" y="${T + 11}" text-anchor="middle" fill="${ROSE}">flood</text>`;
    for (let q = lo; q <= hi; q += Math.max(1, Math.round((hi - lo) / 4))) s += `<line x1="${L}" x2="${W - 8}" y1="${y(q)}" y2="${y(q)}" stroke="${RULE}"/><text x="${L - 5}" y="${y(q) + 4}" text-anchor="end">${q}</text>`;
    for (let i = 1; i < n; i++) if (v[i] != null && v[i - 1] != null) {
      const gap = t[i] - t[i - 1] > 13 * 864e5;
      s += `<line x1="${x(i - 1)}" y1="${y(v[i - 1])}" x2="${x(i)}" y2="${y(v[i])}" stroke="${INK}" stroke-width="2" ${gap ? 'stroke-dasharray="3 4" opacity="0.5"' : ""}/>`;
    }
    v.forEach((q, i) => { if (q != null) s += `<circle cx="${x(i)}" cy="${y(q)}" r="4" fill="${i === iB ? ROSE : INK}"><title>${fmtDate(meta.dates[i])}: ${q} dB</title></circle>`; });
    [0, iA, n - 1].forEach((i) => { s += `<text x="${x(i)}" y="${H - 6}" text-anchor="${i === 0 ? "start" : i === n - 1 ? "end" : "middle"}">${fmtDate(meta.dates[i])}</text>`; });
    s += "</svg>";
    let say = "";
    if (v[iA] != null && v[iB] != null) {
      const ev = v[iB] - v[iA], others = [];
      for (let i = 1; i < n; i++) if (i !== iB && v[i] != null && v[i - 1] != null && t[i] - t[i - 1] < 13 * 864e5) others.push(Math.abs(v[i] - v[i - 1]));
      say = `Across the flood (19 to 31 Aug) the echo here ${Math.abs(ev) < 0.05 ? "did not change" : `${ev > 0 ? "rose" : "fell"} by <b>${Math.abs(ev).toFixed(1)} dB</b>`}.`
        + (others.length ? ` The biggest change in any other 12-day period was ${Math.max(...others).toFixed(1)} dB.` : "") + ` 3 dB is a doubling or halving.`;
    }
    const csv = "date,hh_backscatter_db,lat,lon,source\n" + meta.dates.map((d, i) => `${d},${v[i] ?? ""},${lngLat.lat.toFixed(5)},${lngLat.lng.toFixed(5)},NISAR L2 GCOV provisional track 098A HH ~50 m cell`).join("\n") + "\n";
    showCard(`<h3>Radar record at ${where}</h3><div class="figure">${s}</div><p>${say}</p>`
      + `<p class="fine">Radar brightness (HH backscatter, dB) of the roughly 50 m patch you clicked, on each NISAR pass of track 98. The dashed part spans a gap in the data.</p>`
      + `<a class="goto dl" download="nisar_hh_${lngLat.lat.toFixed(4)}N_${lngLat.lng.toFixed(4)}E.csv" href="data:text/csv;charset=utf-8,${encodeURIComponent(csv)}">Download CSV</a>`);
  }

  /* ---------- drop water: follow NASADEM flow directions downhill ---------- */
  let flowGrid = null, flowP = null;
  const DX = [0, 0, 1, 1, 1, 0, -1, -1, -1], DY = [0, -1, -1, 0, 1, 1, 1, 0, -1];   // codes 1..8 = N, NE, E, SE, S, SW, W, NW
  function loadFlow() { const f = terrainMeta.flowdir; flowP ??= loadGrey("/data/" + f.file, f.width, f.height).then((g) => (flowGrid = g)); return flowP; }
  async function dropWater(lngLat, label) {
    pin.setLngLat(lngLat).addTo(map);
    if (!flowGrid) showCard(`<h3>Tracing the way downhill</h3><p>Loading the flow directions (about 1.4 MB, first click only).</p>`);
    await loadFlow();
    const f = terrainMeta.flowdir;
    let c = Math.floor((lngLat.lng - f.west) / f.step_deg), r = Math.floor((f.north - lngLat.lat) / f.step_deg);
    if (c < 0 || r < 0 || c >= f.width || r >= f.height) { showCard(`<h3>Outside the elevation data</h3><p>Click inside the mapped valley.</p>`); return; }
    const pts = [], seen = new Set(); let edge = false;
    for (let k = 0; k < 40000; k++) {
      pts.push([f.west + (c + 0.5) * f.step_deg, f.north - (r + 0.5) * f.step_deg]);
      const code = flowGrid[r * f.width + c];
      if (!code || seen.has(r * f.width + c)) { edge = c < 3 || r < 3 || c > f.width - 4 || r > f.height - 4; break; }
      seen.add(r * f.width + c);
      c += DX[code]; r += DY[code];
      if (c < 0 || r < 0 || c >= f.width || r >= f.height) { edge = true; break; }
    }
    let km = 0; const cum = [0];
    for (let i = 1; i < pts.length; i++) { km += hav(pts[i - 1], pts[i]); cum.push(km); }
    const passes = PLACES.slice(1).map((p) => {
      let best = Infinity, at = 0;
      pts.forEach((q, i) => { const d = hav(q, p.lngLat); if (d < best) { best = d; at = cum[i]; } });
      return best < 1.2 ? `${p.name} after ${at.toFixed(0)} km` : null;
    }).filter(Boolean);
    map.getSource("route").setData({ type: "Feature", geometry: { type: "LineString", coordinates: pts }, properties: {} });
    if (pts.length > 2) map.fitBounds(pts.reduce((b, p) => b.extend(p), new maplibregl.LngLatBounds(pts[0], pts[0])),
      { padding: isNarrow() ? { top: 120, bottom: 60, left: 30, right: 30 } : { top: 130, bottom: 90, left: 70, right: 380 }, maxZoom: 13, pitch: 0, bearing: 0, duration: reduceMotion ? 0 : 1400 });
    showCard(`<h3>${label || "Water dropped here"}</h3>`
      + `<p>From this spot the land leads water <b>${km.toFixed(1)} km</b> downhill ${edge ? "to the edge of our elevation data" : "to a low point where the route stops"}. `
      + (passes.length ? `It passes ${passes.join(", ")}.` : "It does not come within 1.2 km of Rasuwagadhi, Syabrubesi or Betrawati inside this map.") + `</p>`
      + `<p class="fine">Steepest-descent route on NASADEM (NASA, 30 m, measured in 2000). This shows direction only. It says nothing about how much water, how deep or how fast, and it is not a flood forecast.</p>`);
  }
  function onMapClick(e) {
    if (view === "compare") return;
    const lake = map.getLayer("lakes-ring") && map.getLayoutProperty("lakes-ring", "visibility") === "visible"
      ? map.queryRenderedFeatures([[e.point.x - 8, e.point.y - 8], [e.point.x + 8, e.point.y + 8]], { layers: ["lakes-ring", "lakes"] })[0] : null;
    if (lake) {
      const p = lake.properties;
      dropWater({ lng: +p.lon, lat: +p.lat }, `Glacial lake at ${(+p.elevation_m).toLocaleString("en")} m, ${(p.area_m2 / 10000).toFixed(1)} hectares`);
    } else if (mode === "water") dropWater(e.lngLat);
    else inspect(e.lngLat);
  }

  /* ---------- stepper: previous / next through the story, also with the arrow keys ---------- */
  const STEP_NAMES = { intro: "Start", source: "The source", lende: "Lende Khola", rasuwagadhi: "Rasuwagadhi", minutes: "The warning", syabrubesi: "Syabrubesi",
    betrawati: "Betrawati", season: "Over time", glaciers: "The ice", water: "Where water goes", research: "Use the data", method: "How we know", prepare: "Official warnings", credits: "Credits" };
  const stepList = () => $$(".chapter").map((el) => el.dataset.chapter);
  function goStep(delta) {
    const list = stepList(), i = Math.max(0, list.indexOf(currentChapter)), j = Math.max(0, Math.min(list.length - 1, i + delta));
    const el = $(`.chapter[data-chapter="${list[j]}"]`), off = isNarrow() ? innerHeight * 0.48 + 44 : 52;
    scrollTo({ top: j === 0 ? 0 : el.getBoundingClientRect().top + scrollY - off, behavior: reduceMotion ? "auto" : "smooth" });
  }
  function updateStepper() {
    const list = stepList(), i = Math.max(0, list.indexOf(currentChapter));
    $("#step-name").textContent = STEP_NAMES[list[i]] || "";
    $("#step-count").textContent = `${i + 1} of ${list.length}`;
    $("#step-bar i").style.width = `${((i + 1) / list.length) * 100}%`;
    $("#step-prev").disabled = i === 0; $("#step-next").disabled = i === list.length - 1;
    $("#step-next").textContent = i < list.length - 1 ? `Next: ${STEP_NAMES[list[i + 1]]}` : "End";
  }
  function setupStepper() {
    $("#story").insertAdjacentHTML("afterbegin", `<nav id="stepper" aria-label="Story steps"><div class="step-row">`
      + `<button type="button" id="step-prev" aria-label="Previous step">Back</button><span class="step-where"><b id="step-name"></b><small id="step-count"></small></span>`
      + `<button type="button" id="step-next"></button></div><div id="step-bar"><i></i></div></nav>`);
    $("#step-prev").addEventListener("click", () => goStep(-1));
    $("#step-next").addEventListener("click", () => goStep(1));
    addEventListener("keydown", (e) => {
      if (e.target.closest("input, select, textarea, [contenteditable]") || e.altKey || e.ctrlKey || e.metaKey) return;
      if (e.key === "ArrowRight") { e.preventDefault(); goStep(1); }
      if (e.key === "ArrowLeft") { e.preventDefault(); goStep(-1); }
    });
    updateStepper();
  }

  let map2 = null, map2Ready = false;
  let glacierTimer = null;
  async function init() {
    const [sty, st, fp, lm, gm, tm] = await Promise.all([
      fetch("https://tiles.openfreemap.org/styles/positron").then((r) => r.json()),
      fetch("/data/river_stats.json").then((r) => r.json()),
      fetch("/data/flowpath.geojson").then((r) => r.json()),
      fetch("/data/layers.json").then((r) => r.json()),
      fetch("/data/glacier/glacier_season.json").then((r) => r.json()),
      fetch("/data/terrain.json").then((r) => r.json()),
    ]);
    glacierMeta = gm; terrainMeta = tm;
    style = sty; stats = st; fpData = fp; layersMeta = lm.layers;
    flow = preparePath(fp.features.find((f) => f.properties.id === "flood"), stats.paths.flood.length_km);

    map = makeMap("map", true);
    fitPath(0);
    map.addControl(new maplibregl.NavigationControl({ visualizePitch: true }), "top-right");
    map.addControl(new maplibregl.ScaleControl({ unit: "metric" }), "bottom-right");
    window.__map = map; window.__rf = { inspect: (lng, lat) => inspect({ lng, lat }), dropWater: (lng, lat) => dropWater({ lng, lat }), setMode };   // handy for debugging in the console
    hereMarker = new maplibregl.Marker({ element: Object.assign(document.createElement("div"), { className: "here-marker" }) });
    map.on("move", syncMap2);

    map.on("load", () => {
      addData(map);
      if (isNarrow()) { const at = $(".maplibregl-ctrl-attrib"); if (at) { at.classList.remove("maplibregl-compact-show"); at.removeAttribute("open"); } }
      addExtras();
      setupControls(); setupStepper();
      fillMeasures(); drawDotplot(); drawProfile(); drawFinding(); drawSeasonFig(); drawGlacierFig();
      addEventListener("scroll", onScroll, { passive: true });
      addEventListener("resize", () => { drawProfile(); if (map2) map2.resize(); });
      onScroll();
    });
  }

  function setupControls() {
    const sel = $("#base-select"), have = new Set(layersMeta.map((m) => m.layer));
    layersMeta.filter((m) => m.layer.startsWith("base-")).forEach((m) => {
      const [a, b] = m.sources[0].match(/\d{4}-\d{2}-\d{2}/g); sel.add(new Option(`${fmtDate(a)} to ${fmtDate(b)}`, m.layer));
    });
    if (!sel.options.length) $("#cmp-btn").hidden = true;
    $$("#flood-select option, #bg-select option").forEach((o) => { if (o.value !== "map" && !have.has(o.value)) o.remove(); });
    seasonIdx = Math.max(0, seasonSteps().findIndex((x) => x.event));
    $("#glacier-range").max = glacierMeta.overlay_files.length - 1;
    $$("#modes button").forEach((b) => b.addEventListener("click", () => setMode(b.dataset.mode)));
    $("#cmp-btn").addEventListener("click", () => { stopPlay(); setView(view === "compare" ? "flood" : "compare"); });
    $("#more").addEventListener("change", applyLayers);
    $("#swipe-range").addEventListener("input", (e) => setSwipe(e.target.value));
    $("#play-btn").addEventListener("click", () => (playRaf ? stopPlay() : startPlay()));
    $("#season-range").addEventListener("input", (e) => { seasonPlay(false); setSeason(+e.target.value); });
    $("#season-play").addEventListener("click", () => seasonPlay(!seasonTimer));
    $("#glacier-range").addEventListener("input", (e) => setGlacier(+e.target.value));
    $("#low-on").addEventListener("change", () => setMode("water"));
    $("#card-close").addEventListener("click", closeCard);
    document.addEventListener("click", (e) => {
      const m = $("#more"); if (m.open && !m.contains(e.target)) m.open = false;
      const b = e.target.closest("[data-do]"); if (!b) return;
      const [k, v] = b.dataset.do.split(":");
      if (k === "compare") { setMode("flood"); setView("compare"); }
      if (k === "mode") setMode(v);
      if (k === "season-play") { setMode("season"); setSeason(0); seasonPlay(true); }
      if (k === "play") { setMode("flood"); setView("flood"); startPlay(); }
      if (k === "inspect") { const c = CHAPTERS[currentChapter] || {}, at = c.kmAt || c.center; setMode("flood"); inspect({ lng: at[0], lat: at[1] }); }
      if (k === "drop") { setMode("water"); dropWater({ lng: 85.50, lat: 28.31 }, "The flood source"); }
      if (k === "glacier-play") {
        setMode("glacier"); clearInterval(glacierTimer);
        let i = 0; const r = $("#glacier-range"), n = +r.max;
        const step = () => { r.value = i; setGlacier(i); if (++i > n) clearInterval(glacierTimer); };
        step(); glacierTimer = setInterval(step, 1100);
      }
    });
    setMode("flood");
  }

  init().catch((err) => {
    console.error(err);
    $("#map").insertAdjacentHTML("beforeend", `<p style="position:absolute;inset:auto 0 50% 0;text-align:center;padding:0 1rem">The map could not load. Check your connection and reload the page.</p>`);
  });
})();
