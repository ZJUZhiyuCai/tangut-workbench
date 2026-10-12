const $ = (s) => document.querySelector(s);
const h = (value) =>
  String(value ?? "").replace(
    /[&<>"']/g,
    (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        c
      ],
  );
const labels = {
  source_checked: "原页已核",
  source_reported: "仅据转录",
  proposed: "拟释待核",
};
const hypothesisLabels = {
  proposed: "未采纳",
  rejected: "已否定",
  withdrawn: "已撤回",
};
let data,
  sources,
  byChar,
  characters,
  missing,
  selected = "U17788",
  limit = 40;

function normalizedQuery(value) {
  let q = value.trim().toLowerCase();
  if (/^l\d{1,4}$/.test(q)) q = `l2008-${q.slice(1).padStart(4, "0")}`;
  if (/^(u\+|u)?[0-9a-f]{5}$/.test(q)) q = `u+${q.replace(/^u\+?/, "")}`;
  return q;
}
function glyph(c, large = false) {
  if (missing.has(c.id))
    return `<span class="${large ? "missing-large" : "missing-small"}">${h(c.codepoint)}</span>`;
  return `<span class="glyph ${large ? "large-glyph" : ""}">${h(c.character)}</span>`;
}
function sourceList(evidence) {
  return evidence
    .map(
      (ev) =>
        `<div class="evidence"><p><a href="${h(sources.get(ev.source_id).url)}" target="_blank" rel="noopener noreferrer">${h(sources.get(ev.source_id).title)} ↗</a></p><p class="locator">${h(ev.locator)}</p><p class="small">${ev.inspection === "direct" ? "直接核对所引页面" : "只核转录页面"} · 核对日期 ${h(ev.accessed)}</p></div>`,
    )
    .join("");
}
function showTab(name) {
  if (!["dictionary", "research", "contribute"].includes(name)) return;
  for (const button of document.querySelectorAll("[data-tab]"))
    button.setAttribute("aria-pressed", String(button.dataset.tab === name));
  for (const panel of document.querySelectorAll(".panel"))
    panel.hidden = panel.id !== name;
}
function results() {
  const query = normalizedQuery($("#query").value),
    scope = $("#scope-filter").value;
  const list = characters.filter(
    (c) =>
      (!query || c.searchText.includes(query)) &&
      (scope === "all" ||
        (scope === "lexical" && c.senses.length) ||
        (scope === "checked" &&
          c.senses.some((s) => s.status === "source_checked"))),
  );
  $("#result-count").textContent =
    `${list.length.toLocaleString("zh-CN")} 个字头`;
  $("#results").innerHTML = list.length
    ? list
        .slice(0, limit)
        .map(
          (c) =>
            `<button type="button" class="result" data-id="${h(c.id)}" aria-current="${selected === c.id}" aria-label="查看 ${h(c.codepoint)} ${h(c.senses[0]?.gloss_zh || "暂无词义记录")}">${glyph(c)}<span class="result-copy"><span class="result-title">${h(c.senses[0]?.gloss_zh || "暂无词义记录")}</span><span class="result-meta">${h(c.codepoint)} · ${h(c.merged_sources)}</span></span>${c.senses.length ? `<span class="result-status">${h(labels[c.senses[0].status])}</span>` : ""}</button>`,
        )
        .join("")
    : '<p class="no-result">没有匹配的字头。可尝试 U+ 编码、L2008 编号，或切换到“全部字头”。</p>';
  $("#more").hidden = list.length <= limit;
}
function detail(id) {
  const c = byChar.get(id);
  if (!c) return;
  selected = id;
  const related = data.hypotheses.filter((hyp) =>
    hyp.related_character_ids.includes(id),
  );
  $("#detail").innerHTML =
    `<div class="detail-inner"><div class="glyph-heading">${glyph(c, true)}<div><div class="codepoint">${h(c.codepoint)}</div><div class="meta">字书源编号 ${h(c.merged_sources)}</div><div class="meta">部首笔画索引 ${h(c.radical_strokes)}</div><div class="id-label">Unicode ${h(data.project.unicode_version)} · ${h(c.id)}</div></div></div>
  ${missing.has(id) ? '<p class="note">随附字体暂未覆盖此字，现显示码位。可通过 Unicode 来源记录继续查找字形。</p>' : ""}
  <h2 class="rule-heading">词义与证据</h2>
  ${c.senses.length ? c.senses.map((s) => `<article class="sense"><div class="sense-title"><h3>${h(s.gloss_zh)}</h3><span class="status">${h(labels[s.status])}</span></div><p class="english">${h(s.gloss_en)}</p>${sourceList(s.evidence)}<p class="note">${h(s.note)}</p><div class="review-state">独立复核记录：${s.independent_reviews.length} · ${s.independent_reviews.length ? "请查数据中的署名记录" : "尚无人类专家独立复核"}</div><div class="id-label">义项 ID ${h(s.id)}</div></article>`).join("") : '<p class="empty-sense">该字已列入编码索引，尚未整理词义。可以贡献一条带原页出处的释义。</p>'}
  ${related.length ? `<div class="related"><h2 class="rule-heading">关联校读 · 均为待验证假说</h2>${related.map((hyp) => `<a href="#hypothesis=${encodeURIComponent(hyp.id)}">${h(hyp.id.split("-").at(-1))} / ${h(hyp.claim)} →</a>`).join("")}</div>` : ""}
  <p class="small">字书源编号来自 <a href="https://www.unicode.org/Public/17.0.0/ucd/TangutSources.txt">Unicode TangutSources</a>。检索中的 L4267 简写按 L2008-4267 解释，不自动等同其他版本编号。</p></div>`;
  for (const button of document.querySelectorAll(".result"))
    button.setAttribute("aria-current", String(button.dataset.id === id));
}
function research() {
  const s = data.stats,
    doc = data.documents[0];
  $("#research").innerHTML =
    `<div class="section-heading"><span class="eyebrow">MANUSCRIPT / ${h(doc.shelfmark)}</span><h2>《${h(doc.title)}》持续校读</h2><p>${h(doc.description)}</p></div><div class="research-counts"><span><strong>${s.open_hypotheses}</strong> 项待验证假说</span><span><strong>${s.unread_regions}</strong> 处未释区域</span><span><strong>${s.new_translated_passages}</strong> 段新增完整译文</span></div>
  ${data.hypotheses.map((hyp) => `<details class="hypothesis" id="${h(hyp.id)}"><summary><span class="hyp-title">${h(hyp.id.split("-").at(-1))} · ${h(hyp.claim)}</span><span>${h(hypothesisLabels[hyp.status])}</span></summary><div class="hyp-body"><p>${h(hyp.level)}</p><h4>支持线索</h4><ul>${hyp.rationale.map((item) => `<li>${h(item)}</li>`).join("")}</ul><h4>尚待解决</h4><ul>${hyp.unresolved.map((item) => `<li>${h(item)}</li>`).join("")}</ul><h4>可定位来源</h4>${sourceList(hyp.evidence)}<p class="small">没有据此改动写本基线。此记录不构成首次发现或已完成翻译的声明。</p></div></details>`).join("")}
  <h3>未释区域与下一步检验</h3><div class="table-scroll"><table class="gap-table"><thead><tr><th>编号</th><th>位置</th><th>当前证据与下一步</th></tr></thead><tbody>${data.gaps.map((g) => `<tr><td>${h(g.id.split("-").at(-1))}</td><td>${h(g.locus)}</td><td><p>${h(g.observation)}</p><p class="small">${h(g.next_test)}</p></td></tr>`).join("")}</tbody></table></div>
  <h3>已刊字序的定位记录</h3><p class="small">以下 ${s.alignment_windows} 个窗口对齐的是前人已刊字序。中文仅为定位说明；不计为新字、新释读或整句译文。重文展开不等于写本中有两个等距字形。</p><div class="table-scroll"><table class="alignment-table"><thead><tr><th>记录</th><th>字序</th><th>定位说明</th></tr></thead><tbody>${data.passages.map((p) => `<tr><td class="id-label">${h(p.id.replace("inv5875-", ""))}</td><td class="glyph">${h(p.transcription)}</td><td>${h(p.note)}</td></tr>`).join("")}</tbody></table></div><p class="small" style="margin-top:18px">扫描图不随项目分发。坐标只适用于记录中指定的图像尺寸与提取版本，不能直接套到其他图片。</p>
  <p><a href="https://github.com/ZJUZhiyuCai/tangut-workbench/blob/main/docs/research/inv5875.md">阅读完整研究说明与证据限制 ↗</a></p>`;
}
function route() {
  const params = new URLSearchParams(location.hash.slice(1));
  const id = params.get("char"),
    hypothesis = params.get("hypothesis");
  if (id && byChar.has(id)) {
    showTab("dictionary");
    detail(id);
  } else if (hypothesis && data.hypotheses.some((h) => h.id === hypothesis)) {
    showTab("research");
    const el = document.getElementById(hypothesis);
    el.open = true;
    el.scrollIntoView({ block: "start" });
  } else if (params.has("tab")) showTab(params.get("tab"));
}
async function init() {
  const [datasetResponse, fontResponse] = await Promise.all([
    fetch("dataset.json"),
    fetch("font-coverage.json"),
  ]);
  if (!datasetResponse.ok || !fontResponse.ok)
    throw new Error("无法读取项目数据");
  data = await datasetResponse.json();
  missing = new Set((await fontResponse.json()).missing_character_ids);
  sources = new Map(data.sources.map((s) => [s.id, s]));
  const entryMap = new Map(data.entries.map((e) => [e.id, e]));
  characters = data.characters
    .map((c) => {
      const senses = data.senses.filter((s) =>
        entryMap.get(s.entry_id).character_ids.includes(c.id),
      );
      return {
        ...c,
        senses,
        searchText: [
          c.character,
          c.codepoint,
          c.merged_sources,
          ...senses.map(
            (s) =>
              `${entryMap.get(s.entry_id).headword} ${s.gloss_zh} ${s.gloss_en}`,
          ),
        ]
          .join(" ")
          .toLowerCase(),
      };
    })
    .sort(
      (a, b) =>
        Number(Boolean(b.senses.length)) - Number(Boolean(a.senses.length)) ||
        a.id.localeCompare(b.id),
    );
  byChar = new Map(characters.map((c) => [c.id, c]));
  const metrics = [
    [data.stats.unicode_characters, "Unicode 字头"],
    [data.stats.lexical_entries, "词条已建档"],
    [data.stats.senses_source_checked, "义项原页已核"],
    [data.stats.senses_with_independent_review, "义项获独立复核"],
  ];
  $("#counters").innerHTML = metrics
    .map(
      ([n, label]) =>
        `<div class="metric"><strong>${n.toLocaleString("zh-CN")}</strong><span>${label}</span></div>`,
    )
    .join("");
  document.querySelectorAll("[data-tab]").forEach((button) =>
    button.addEventListener("click", () => {
      showTab(button.dataset.tab);
      history.replaceState(null, "", `#tab=${button.dataset.tab}`);
    }),
  );
  $("#query").addEventListener("input", () => {
    limit = 40;
    results();
  });
  $("#scope-filter").addEventListener("change", () => {
    limit = 40;
    results();
  });
  $("#clear-search").addEventListener("click", () => {
    $("#query").value = "";
    limit = 40;
    results();
    $("#query").focus();
  });
  $("#more").addEventListener("click", () => {
    limit += 40;
    results();
  });
  $("#results").addEventListener("click", (event) => {
    const button = event.target.closest("[data-id]");
    if (button) {
      detail(button.dataset.id);
      history.replaceState(null, "", `#char=${button.dataset.id}`);
      if (matchMedia("(max-width:720px)").matches)
        $("#detail").scrollIntoView({ block: "start" });
    }
  });
  window.addEventListener("hashchange", route);
  $("#loading").hidden = true;
  research();
  showTab("dictionary");
  results();
  detail(selected);
  route();
}
init().catch((error) => {
  $("#loading").textContent =
    `加载失败：${error.message}。请刷新，或从 GitHub 下载数据。`;
  console.error(error);
});
