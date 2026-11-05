"use strict";

// The browser only renders Python's trace. Algorithm logic is in algorithms.py.
const $ = (id) => document.getElementById(id);
const META = {
  bubble: {
    title: "Bubble Sort", best: "O(n)", average: "O(n²)", worst: "O(n²)", space: "O(1)",
    description: "Compare neighbors and swap them when they are out of order. Each pass moves the largest remaining value to its final position.",
    note: "Stable · In place · Stops early when a pass makes no swaps.",
    code: ["for each shrinking unsorted range", "  for each adjacent pair", "    compare left and right", "    if left > right: swap", "  mark the final value as fixed", "  if no swaps: stop"],
    cases: {best: "Already sorted ascending; early exit after one pass.", average: "A reproducibly shuffled array of unique values.", worst: "Reverse-sorted unique values; every pair is inverted."}, color: "#347e69"
  },
  merge: {
    title: "Merge Sort", best: "O(n log n)", average: "O(n log n)", worst: "O(n log n)", space: "O(n)",
    description: "Split the array into halves, sort each half, then merge their values in order. The temporary buffers show which values are being read.",
    note: "Stable · Uses an auxiliary array · All cases have Θ(n log n) time.",
    code: ["merge_sort(low, high)", "  split at the midpoint", "  sort both halves recursively", "  copy the halves into a buffer", "  compare the two front values", "  write the smaller value", "  copy any remaining values"],
    cases: {best: "Ascending input; halves do not interleave. Time remains Θ(n log n).", average: "A reproducibly shuffled array of unique values.", worst: "Recursively interleaved halves maximize merge comparisons at these power-of-two sizes."}, color: "#c2904b"
  },
  quick: {
    title: "Quick Sort", best: "O(n log n)", average: "O(n log n)", worst: "O(n²)", space: "O(log n)",
    description: "Choose the last value as a pivot. Partition smaller values to its left and larger ones to its right, then sort the remaining ranges.",
    note: "Unstable · Lomuto partition · Recurse on the smaller side to bound stack space.",
    code: ["while range has multiple values", "  pivot = last value", "  i = first index", "  compare each value with pivot", "  if value ≤ pivot: swap; i++", "  move pivot to index i", "  recurse smaller; repeat larger"],
    cases: {best: "A constructed permutation gives balanced partitions for the last-element pivot.", average: "A reproducibly shuffled array of unique values.", worst: "Ascending values with a last-element pivot create maximally unbalanced partitions."}, color: "#9680b6"
  },
  linear: {
    title: "Linear Search", best: "O(1)", average: "O(n)", worst: "O(n)", space: "O(1)",
    description: "Check values from left to right until the target is found. This works on any array, even when its values are not sorted.",
    note: "Returns the first matching index · An absent value returns −1.",
    code: ["for each index from left to right", "  compare value with target", "  if equal: return index", "return −1"],
    cases: {best: "Every query targets the first element.", average: "The target can be at any position in the array.", worst: "Target is absent; every value must be checked."}, color: "#347e69"
  },
  binary: {
    title: "Binary Search", best: "O(1)", average: "O(log n)", worst: "O(log n)", space: "O(1)",
    description: "Check the middle value of a sorted array. Discard the half that cannot contain the target, then repeat on the remaining half.",
    note: "Requires ascending input · Returns any matching index · Sort preparation is separate.",
    code: ["low = 0; high = last index", "while low ≤ high", "  mid = floor((low + high) / 2)", "  if value == target: return mid", "  if value < target: low = mid + 1", "  otherwise: high = mid − 1", "return −1"],
    cases: {best: "Every query targets the initial midpoint.", average: "The target can be at any position in the sorted array.", worst: "Absent target above the maximum follows a deepest unsuccessful path at these sizes."}, color: "#9680b6"
  }
};

let frames = [], position = 0, playing = false, timer = null;
let loading = false, serial = 0, barNodes = [], traceNodes = [];
let benchmarkGroup = "sort", benchmarkCache = {}, benchmarkRunning = false;

async function api(path, body) {
  let response;
  try {
    response = await fetch(path, {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(body)});
  } catch (_) {
    throw new Error("Cannot reach Python. Start server.py and open the address printed in its terminal.");
  }
  let data;
  try { data = await response.json(); }
  catch (_) { throw new Error("The server returned an unexpected response. Check the Python terminal."); }
  if (!response.ok) throw new Error(data.error || "Request failed.");
  return data;
}

function showError(id, message) {
  $(id).textContent = message || "";
  $(id).hidden = !message;
}

function pause() {
  playing = false;
  clearTimeout(timer);
  updateTransport();
}

function updateTransport() {
  $("play-label").textContent = playing ? "Pause" : (position === frames.length - 1 && frames.length > 1 ? "Replay" : "Play");
  $("play-icon").textContent = playing ? "Ⅱ" : "▶";
  $("play").disabled = loading || frames.length < 2;
  $("back").disabled = loading || position <= 0;
  $("reset").disabled = loading || position <= 0;
  $("next").disabled = loading || position >= frames.length - 1;
  $("finish").disabled = loading || position >= frames.length - 1;
  $("timeline").disabled = loading || frames.length < 2;
  const final = position === frames.length - 1 && frames.length > 1;
  const badge = $("state-badge");
  badge.textContent = loading ? "Preparing" : playing ? "Running" : final ? "Complete" : position ? "Paused" : "Ready";
  badge.className = "state-badge" + (playing ? " running" : final ? " complete" : "");
}

function setLoading(value) {
  loading = value;
  $("controls-form").querySelectorAll("input, select, button").forEach((node) => { node.disabled = value; });
  updateTransport();
}

function parseValues() {
  const text = $("array-input").value.trim();
  if (!text) return [];
  if (!/^[\s,\-+\d]+$/.test(text)) throw new Error("Enter whole numbers separated by commas or spaces.");
  const parts = text.split(/[\s,]+/).filter(Boolean);
  if (parts.length > 48) throw new Error("Use at most 48 values for a readable animation.");
  if (parts.some((value) => !/^[+-]?\d+$/.test(value))) throw new Error("Every entry must be a whole number.");
  const values = parts.map(Number);
  if (values.some((value) => !Number.isInteger(value) || value < -999 || value > 999)) throw new Error("Use integers between −999 and 999.");
  return values;
}

function setAlgorithmInfo() {
  const algorithm = $("algorithm").value;
  const info = META[algorithm];
  $("algorithm-title").textContent = info.title;
  $("description").textContent = info.description;
  $("algorithm-note").textContent = info.note;
  $("target-field").hidden = !["linear", "binary"].includes(algorithm);
  $("complexity").replaceChildren();
  for (const [key, label] of [["best", "Best"], ["average", "Average"], ["worst", "Worst"], ["space", "Space"]]) {
    const item = document.createElement("div");
    const name = document.createElement("span"); name.textContent = label;
    const value = document.createElement("b"); value.textContent = info[key];
    item.append(name, value); $("complexity").append(item);
  }
  $("pseudocode").replaceChildren(...info.code.map((line) => {
    const item = document.createElement("li"); item.textContent = line; return item;
  }));
}

async function loadTrace() {
  pause();
  showError("error", "");
  let values, target;
  try {
    values = parseValues();
    if (["linear", "binary"].includes($("algorithm").value)) {
      const text = $("target").value.trim();
      target = Number(text);
      if (!text || !Number.isInteger(target) || target < -999 || target > 999) throw new Error("Enter a whole-number target between −999 and 999.");
    }
  } catch (error) { showError("error", error.message); return; }
  const request = ++serial;
  setAlgorithmInfo();
  setLoading(true);
  try {
    const data = await api("/api/trace", {algorithm: $("algorithm").value, values, target});
    if (request !== serial) return;
    frames = data.steps;
    position = 0;
    $("preparation-note").hidden = !data.prepared;
    buildBars(frames[0].values.length);
    buildTrace();
    $("timeline").max = String(frames.length - 1);
    render();
  } catch (error) {
    frames = []; position = 0;
    showError("error", error.message);
    $("step-message").textContent = "The trace could not be loaded.";
  } finally { if (request === serial) setLoading(false); }
}

function buildBars(n) {
  const fragment = document.createDocumentFragment();
  barNodes = [];
  for (let i = 0; i < n; i++) {
    const slot = document.createElement("div"); slot.className = "bar-slot";
    const bar = document.createElement("div"); bar.className = "bar";
    const value = document.createElement("span"); value.className = "bar-value";
    const index = document.createElement("span"); index.className = "bar-index"; index.textContent = String(i);
    bar.append(value); slot.append(bar, index); fragment.append(slot);
    barNodes.push({bar, value});
  }
  $("bars").replaceChildren(fragment);
  $("bars").className = "bars" + (n > 24 ? " dense" : "");
  $("empty-state").hidden = n !== 0;
}

function buildTrace() {
  const fragment = document.createDocumentFragment();
  traceNodes = frames.map((frame, index) => {
    const item = document.createElement("li");
    const button = document.createElement("button"); button.type = "button";
    const number = document.createElement("span"); number.textContent = String(index).padStart(2, "0");
    const text = document.createElement("span"); text.textContent = frame.message;
    button.append(number, text);
    button.addEventListener("click", () => { pause(); seek(index); });
    item.append(button); fragment.append(item); return item;
  });
  $("trace-list").replaceChildren(fragment);
  $("trace-count").textContent = `${frames.length - 1} steps`;
}

function renderBuffers(buffers) {
  const container = $("merge-buffers");
  container.hidden = !buffers;
  if (!buffers) return;
  container.replaceChildren();
  for (const [side, pointer, label] of [["left", "i", "Left"], ["right", "j", "Right"]]) {
    const group = document.createElement("span"); group.className = "buffer";
    const name = document.createElement("span"); name.textContent = `${label}: `; group.append(name);
    buffers[side].forEach((value, index) => {
      const cell = document.createElement("b"); cell.textContent = value;
      cell.className = index < buffers[pointer] ? "used" : index === buffers[pointer] ? "selected" : "";
      group.append(cell);
    });
    container.append(group);
  }
}

function render() {
  if (!frames.length) return;
  const frame = frames[position];
  const min = Math.min(0, ...frame.values), max = Math.max(1, ...frame.values);
  const span = max - min;
  // Real zero baseline supports signed inputs. The surrounding padding holds labels.
  $("zero-line").style.top = `${max / span * 100}%`;
  const active = new Set(frame.active), fixed = new Set(frame.fixed);
  barNodes.forEach(({bar, value}, index) => {
    const v = frame.values[index];
    const top = (max - Math.max(0, v)) / span * 100;
    const height = Math.abs(v) / span * 100;
    bar.style.top = `${top}%`; bar.style.height = `${height}%`;
    value.textContent = v;
    const classes = ["bar"];
    if (v < 0) classes.push("negative");
    if (fixed.has(index)) classes.push("fixed");
    if (frame.bounds && (index < frame.bounds[0] || index > frame.bounds[1]) && !fixed.has(index)) classes.push("outside");
    if (active.has(index)) {
      classes.push(frame.kind === "swap" || frame.kind === "write" ? frame.kind : "active");
      if (frame.kind === "found") classes.push("found");
    }
    if (frame.pivot === index) classes.push("pivot");
    if (frame.index === index) classes.push("found");
    bar.className = classes.join(" ");
  });
  $("chart").setAttribute("aria-label", `Array: ${frame.values.join(", ") || "empty"}. ${frame.message}`);
  $("comparisons").textContent = frame.comparisons;
  $("swaps").textContent = frame.swaps;
  $("writes").textContent = frame.writes;
  $("step-message").textContent = frame.message;
  $("step-counter").textContent = `Step ${position} / ${frames.length - 1}`;
  $("timeline").value = String(position);
  $("pseudocode").querySelectorAll("li").forEach((node, index) => { node.classList.toggle("current", index === frame.line); });
  $("trace-list").querySelector(".current")?.classList.remove("current");
  const current = traceNodes[position];
  current?.classList.add("current");
  if (current) {
    const list = $("trace-list");
    list.scrollTop += current.getBoundingClientRect().top - list.getBoundingClientRect().top - list.clientHeight / 2 + current.clientHeight / 2;
  }
  renderBuffers(frame.buffers);
  updateTransport();
}

function seek(index) { position = Math.max(0, Math.min(frames.length - 1, index)); render(); }

function tick() {
  if (!playing) return;
  if (position >= frames.length - 1) { pause(); return; }
  seek(position + 1);
  if (position === frames.length - 1) { pause(); return; }
  timer = setTimeout(tick, Number($("speed").value));
}

function togglePlay() {
  if (loading || frames.length < 2) return;
  if (playing) { pause(); return; }
  if (position >= frames.length - 1) seek(0);
  playing = true; updateTransport();
  timer = setTimeout(tick, Number($("speed").value));
}

function generateDataset(kind) {
  const n = Number($("size").value);
  let values = Array.from({length: n}, (_, i) => 5 + i * Math.floor(90 / n));
  if (kind === "reversed") values.reverse();
  if (kind === "duplicates") values = Array.from({length: n}, (_, i) => [20, 50, 20, 80, 50, 10][i % 6]);
  if (kind === "random") {
    for (let i = values.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [values[i], values[j]] = [values[j], values[i]];
    }
  }
  $("array-input").value = values.join(", ");
  if (values.length) $("target").value = values[Math.floor(values.length / 2)];
  loadTrace();
}

// Benchmark charts use measured data only. No external charting dependency.
function algorithmsInGroup() { return benchmarkGroup === "sort" ? ["bubble", "merge", "quick"] : ["linear", "binary"]; }
function formatMs(value) { return value.toFixed(value >= 1 ? 3 : value >= 0.01 ? 4 : 6); }

function updateCaseDetails() {
  const caseName = $("case").value;
  $("case-details").replaceChildren(...algorithmsInGroup().map((name) => {
    const p = document.createElement("p"), label = document.createElement("strong");
    label.textContent = `${META[name].title}: `;
    p.append(label, document.createTextNode(META[name].cases[caseName])); return p;
  }));
}

function svgNode(tag, attrs = {}, text) {
  const node = document.createElementNS("http://www.w3.org/2000/svg", tag);
  for (const [key, value] of Object.entries(attrs)) node.setAttribute(key, String(value));
  if (text !== undefined) node.textContent = text;
  return node;
}

function renderBenchmark() {
  const result = benchmarkCache[benchmarkGroup], names = algorithmsInGroup();
  $("benchmark-title").textContent = benchmarkGroup === "sort" ? "Sorting algorithms" : "Searching algorithms";
  updateCaseDetails();
  $("benchmark-legend").replaceChildren(...names.map((name) => {
    const item = document.createElement("span"), dot = document.createElement("i");
    dot.style.background = META[name].color; item.append(dot, document.createTextNode(META[name].title)); return item;
  }));
  $("export-csv").disabled = !result;
  $("benchmark-table").hidden = !result;
  if (!result) {
    $("benchmark-chart").replaceChildren();
    const empty = document.createElement("div"); empty.className = "benchmark-empty";
    const icon = document.createElement("span"); icon.className = "empty-chart-icon"; icon.textContent = "↗";
    const title = document.createElement("h3"); title.textContent = "Put the algorithms to the test.";
    const message = document.createElement("p"); message.textContent = "Run a benchmark at 32, 128, 512 and 1,024 elements.";
    empty.append(icon, title, message); $("benchmark-chart").append(empty); return;
  }
  $("method-note").textContent = `For each algorithm and input size, ${result.repeats} timing samples are collected. The middle value (median) is displayed in milliseconds (ms).`;
  const rows = result.rows.filter((row) => row.case === $("case").value);
  const W = 1000, H = 290, left = 67, right = 34, top = 23, bottom = 48;
  const minExp = Math.floor(Math.log10(Math.max(1e-8, Math.min(...rows.map((r) => r.ms)))));
  const maxExp = Math.max(minExp + 1, Math.ceil(Math.log10(Math.max(...rows.map((r) => r.ms)))));
  const x = (n) => left + (n - result.sizes[0]) / (result.sizes.at(-1) - result.sizes[0]) * (W - left - right);
  const y = (ms) => top + (maxExp - Math.log10(Math.max(1e-8, ms))) / (maxExp - minExp) * (H - top - bottom);
  const svg = svgNode("svg", {viewBox: `0 0 ${W} ${H}`, role: "img", "aria-label": `${$("case").value} case measured runtimes; logarithmic vertical scale. Exact timings are in the table below.`});
  for (let exp = minExp; exp <= maxExp; exp++) {
    const Y = y(10 ** exp);
    svg.append(svgNode("line", {x1: left, x2: W - right, y1: Y, y2: Y, stroke: "#e9eee3", "stroke-dasharray": "3 4"}));
    svg.append(svgNode("text", {x: left - 12, y: Y + 4, "text-anchor": "end", fill: "#96a68a", "font-size": 11}, exp >= 0 ? String(10 ** exp) : (10 ** exp).toFixed(-exp)));
  }
  for (const n of result.sizes) {
    svg.append(svgNode("text", {x: x(n), y: H - 23, "text-anchor": "middle", fill: "#96a68a", "font-size": 11}, String(n)));
  }
  svg.append(svgNode("text", {x: W / 2, y: H - 1, "text-anchor": "middle", fill: "#a0ac96", "font-size": 10}, "Input size (n)"));
  for (const name of names) {
    const points = rows.filter((row) => row.algorithm === name);
    svg.append(svgNode("polyline", {points: points.map((row) => `${x(row.n)},${y(row.ms)}`).join(" "), fill: "none", stroke: META[name].color, "stroke-width": 2.5, "stroke-linejoin": "round"}));
    for (const row of points) {
      const point = svgNode("circle", {cx: x(row.n), cy: y(row.ms), r: 4.5, fill: "#fff", stroke: META[name].color, "stroke-width": 2.5});
      point.append(svgNode("title", {}, `${META[name].title}, n=${row.n}: ${formatMs(row.ms)} ms, ${row.comparisons.toFixed(1)} comparisons`)); svg.append(point);
    }
  }
  $("benchmark-chart").replaceChildren(svg);
  const thead = $("benchmark-table").querySelector("thead"), tbody = $("benchmark-table").querySelector("tbody");
  const header = document.createElement("tr");
  for (const label of ["Input size", ...names.map((name) => META[name].title)]) { const th = document.createElement("th"); th.scope = "col"; th.textContent = label; header.append(th); }
  thead.replaceChildren(header); tbody.replaceChildren();
  for (const n of result.sizes) {
    const tr = document.createElement("tr"), label = document.createElement("th"); label.scope = "row"; label.textContent = n; tr.append(label);
    for (const name of names) {
      const row = rows.find((r) => r.algorithm === name && r.n === n);
      const td = document.createElement("td"), small = document.createElement("small");
      td.textContent = `${formatMs(row.ms)} ms`;
      small.textContent = `${Number.isInteger(row.comparisons) ? row.comparisons : row.comparisons.toFixed(1)} comparisons${benchmarkGroup === "search" ? " / query" : ""}`;
      td.append(small); tr.append(td);
    }
    tbody.append(tr);
  }
}

async function benchmark() {
  if (benchmarkRunning) return;
  pause(); benchmarkRunning = true;
  const group = benchmarkGroup;
  $("run-benchmark").disabled = true; $("run-benchmark").textContent = "Measuring…";
  document.querySelectorAll("[data-group]").forEach((button) => { button.disabled = true; });
  showError("benchmark-error", "");
  try { benchmarkCache[group] = await api("/api/benchmark", {group}); renderBenchmark(); }
  catch (error) { showError("benchmark-error", error.message); }
  finally {
    benchmarkRunning = false; $("run-benchmark").disabled = false; $("run-benchmark").textContent = "Run again ↗";
    document.querySelectorAll("[data-group]").forEach((button) => { button.disabled = false; });
  }
}

$("controls-form").addEventListener("submit", (event) => { event.preventDefault(); loadTrace(); });
$("algorithm").addEventListener("change", loadTrace);
document.querySelectorAll("[data-preset]").forEach((button) => { button.addEventListener("click", () => generateDataset(button.dataset.preset)); });
$("size").addEventListener("change", () => generateDataset("random"));
$("play").addEventListener("click", togglePlay);
$("back").addEventListener("click", () => { pause(); seek(position - 1); });
$("next").addEventListener("click", () => { pause(); seek(position + 1); });
$("reset").addEventListener("click", () => { pause(); seek(0); });
$("finish").addEventListener("click", () => { pause(); seek(frames.length - 1); });
$("timeline").addEventListener("input", () => { pause(); seek(Number($("timeline").value)); });
$("speed").addEventListener("change", () => {
  document.documentElement.style.setProperty("--duration", `${Math.min(180, Number($("speed").value) * 0.6)}ms`);
  if (playing) { clearTimeout(timer); timer = setTimeout(tick, Number($("speed").value)); }
});
document.addEventListener("keydown", (event) => {
  if (event.target.closest("input, select, textarea, button, a") || $("visualizer-view").hidden || loading) return;
  if (event.code === "Space") { event.preventDefault(); togglePlay(); }
  else if (event.key === "ArrowLeft" || event.key === "ArrowRight") { event.preventDefault(); pause(); seek(position + (event.key === "ArrowLeft" ? -1 : 1)); }
});
document.addEventListener("visibilitychange", () => { if (document.hidden) pause(); });
document.querySelectorAll("[data-view]").forEach((button) => {
  button.addEventListener("click", () => {
    pause();
    document.querySelectorAll("[data-view]").forEach((node) => { const active = node === button; node.classList.toggle("active", active); node.setAttribute("aria-pressed", active); });
    $("visualizer-view").hidden = button.dataset.view !== "visualizer";
    $("benchmark-view").hidden = button.dataset.view !== "benchmark";
    if (button.dataset.view === "benchmark") renderBenchmark();
  });
});
document.querySelectorAll("[data-group]").forEach((button) => {
  button.addEventListener("click", () => {
    benchmarkGroup = button.dataset.group;
    document.querySelectorAll("[data-group]").forEach((node) => { const active = node === button; node.classList.toggle("active", active); node.setAttribute("aria-pressed", active); });
    showError("benchmark-error", ""); renderBenchmark();
  });
});
$("case").addEventListener("change", renderBenchmark);
$("run-benchmark").addEventListener("click", benchmark);
$("export-csv").addEventListener("click", () => {
  const result = benchmarkCache[benchmarkGroup]; if (!result) return;
  const lines = ["algorithm,case,input_size,median_ms,mean_value_comparisons"];
  result.rows.forEach((row) => lines.push([row.algorithm, row.case, row.n, row.ms, row.comparisons].join(",")));
  const url = URL.createObjectURL(new Blob([lines.join("\n")], {type: "text/csv;charset=utf-8"}));
  const link = document.createElement("a"); link.href = url; link.download = `algorithm-benchmark-${benchmarkGroup}.csv`; document.body.append(link); link.click(); link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
});

setAlgorithmInfo();
loadTrace();
