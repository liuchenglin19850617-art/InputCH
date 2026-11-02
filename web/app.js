// 爱托皮利卡中文拼音输入法 - 前端逻辑
(function () {
  const $ = (id) => document.getElementById(id);
  const pyInput = $("pinyin");
  const candsEl = $("cands");
  const assocEl = $("assoc");
  const aiEl = $("ai");
  const ctxEl = $("context");
  const statusEl = $("status");

  let curCands = [];   // 当前拼音候选，供数字键选择
  let timer = null;

  function renderCands(list) {
    curCands = list || [];
    candsEl.innerHTML = "";
    if (!curCands.length) {
      candsEl.innerHTML = '<div class="empty">输入拼音查看候选；清空拼音查看联想</div>';
      return;
    }
    curCands.forEach((c, i) => {
      const el = document.createElement("div");
      el.className = "cand";
      const idx = i < 9 ? String(i + 1) : "";
      el.innerHTML =
        (idx ? '<span class="idx">' + idx + "</span>" : "") +
        '<span class="txt">' + c.text + "</span>";
      el.onclick = () => pick(c.text);
      candsEl.appendChild(el);
    });
  }

  function renderList(el, list, kind) {
    el.innerHTML = "";
    if (!list || !list.length) {
      el.innerHTML = '<div class="empty">暂无</div>';
      return;
    }
    list.forEach((item) => {
      const text = typeof item === "string" ? item : item.text;
      const tag = typeof item === "string" ? "" :
        (item.kind === "phrase" ? '<span class="tag ph">词</span>' : "");
      const node = document.createElement("div");
      node.className = "cand";
      node.innerHTML = '<span class="txt">' + text + "</span>" + tag;
      node.onclick = () => pick(text);
      el.appendChild(node);
    });
  }

  function pick(text) {
    if (!text) return;
    ctxEl.value = ctxEl.value + text;
    ctxEl.focus();
    pyInput.value = "";
    refresh();
  }

  function refresh() {
    const pinyin = pyInput.value.trim();
    const context = ctxEl.value;
    if (timer) clearTimeout(timer);
    timer = setTimeout(() => {
      fetch("/api/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ pinyin: pinyin, context: context }),
      })
        .then((r) => r.json())
        .then((d) => {
          renderCands(d.candidates);
          renderList(assocEl, d.associate, "assoc");
          renderList(aiEl, d.llm, "ai");
          if (d.llm_available) {
            $("aiHint").style.display = "none";
            $("aiTag").textContent = "Deepseek-R1 已接入";
          } else {
            $("aiHint").style.display = "block";
            $("aiTag").textContent = "未启用";
          }
        })
        .catch(() => renderCands([]));
    }, 220);
  }

  // 键盘选择
  pyInput.addEventListener("keydown", (e) => {
    if (e.key >= "1" && e.key <= "9") {
      const i = parseInt(e.key, 10) - 1;
      if (curCands[i]) { e.preventDefault(); pick(curCands[i].text); }
    } else if (e.key === " " || e.key === "Enter") {
      if (curCands[0]) { e.preventDefault(); pick(curCands[0].text); }
    } else if (e.key === "Escape") {
      pyInput.value = ""; refresh();
    } else if (e.key === "Backspace" && pyInput.value === "") {
      e.preventDefault();
      ctxEl.value = ctxEl.value.slice(0, -1);
      refresh();
    }
  });

  pyInput.addEventListener("input", refresh);
  ctxEl.addEventListener("input", refresh);

  $("copyBtn").onclick = () => {
    const t = ctxEl.value;
    if (!t) return;
    navigator.clipboard.writeText(t).then(() => {
      const b = $("copyBtn"); const o = b.textContent;
      b.textContent = "已复制"; setTimeout(() => (b.textContent = o), 1200);
    }).catch(() => alert("复制失败，请手动选择文本复制"));
  };
  $("clearCtx").onclick = () => { ctxEl.value = ""; refresh(); };
  $("clearPy").onclick = () => { pyInput.value = ""; pyInput.focus(); refresh(); };

  // 初始化状态
  function loadStatus() {
    fetch("/api/info").then((r) => r.json()).then((s) => {
      const py = s.has_pinyin
        ? '<span class="dot ok"></span>拼音后端：pypinyin（全字覆盖）'
        : '<span class="dot warn"></span>拼音后端：内嵌常用字表（建议 pip install pypinyin）';
      statusEl.innerHTML =
        py +
        ' &nbsp;·&nbsp; <b>词条</b> ' + (s.words || "-") +
        ' &nbsp;·&nbsp; <b>已索引</b> ' + (s.indexed_words || "-") +
        ' &nbsp;·&nbsp; <b>汉字</b> ' + (s.chars || "-") +
        ' &nbsp;·&nbsp; <b>bigram</b> ' + (s.bigrams || "-");
    }).catch(() => {});
    fetch("/api/llm_status").then((r) => r.json()).then((d) => {
      if (d.available) {
        $("aiHint").style.display = "none";
        $("aiTag").textContent = "Deepseek-R1 已接入";
      }
    }).catch(() => {});
  }

  renderCands([]);
  loadStatus();
  refresh();
  pyInput.focus();
})();
