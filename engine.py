# -*- coding: utf-8 -*-
"""
中文拼音输入法核心引擎（讯飞级词库 + 智能整句 + 模糊音 + 简拼）。

词库来源（全部可选，缺了也能跑）：
  1) THUOCL 领域词库（githubMIT/THUOCL/THUOCL_*.txt，词\t词频）
  2) 内置 common_words.txt（补齐日常通用词，高优先级）
  3) 开源单字拼音库 githubMIT/pinyin-data/kMandarin.txt —— 提供全量汉字拼音，使 THUOCL 全词可索引（无需 pypinyin）
  4) 开源词组拼音库 githubMIT/phrase-pinyin-data/phrase.txt —— 数十万通用词组（mozillazg phrase-pinyin-data）

能力：
  - decode(): 拼音串 -> top-k 候选。整句 beam search，词优先；支持模糊音(z/zh 等)与简拼(首字母)。
  - associate(): 上下文联想（PHRASE_FIRST 加速）。
  - 首次构建后缓存到 cache/，之后纯离线运行。
"""
import os
import re
import json
import math
import glob
import threading
import sys

import config
from pinyin_util import HAS_PINYIN, word_pinyin, _split_syllables

_PURE = re.compile(r"^[a-z]+$")
_lock = threading.Lock()
_TONE = re.compile(r"[\d]")  # 拼音库用数字标调（yi1），去掉

# 资源可写目录（exe 同目录，用于运行时下载词库/写缓存）
if getattr(sys, "frozen", False):
    _APP_DIR = os.path.dirname(sys.executable)
else:
    _APP_DIR = config.BASE_DIR


def _ext_path(name):
    """外部词库文件实际路径：优先已打包(_MEIPASS)或 exe 同目录已存在的，否则指向 exe 同目录（可写）。
    name 形如 'pinyin-data/kMandarin.txt'。"""
    in_bundled = os.path.join(config.DICTS_DIR, name)
    if os.path.exists(in_bundled):
        return in_bundled
    return os.path.join(_APP_DIR, "githubMIT", name)


_DICT_SOURCES = [
    ("pinyin-data/kMandarin.txt", "https://raw.githubusercontent.com/mozillazg/pinyin-data/master/kMandarin.txt"),
    ("phrase-pinyin-data/phrase.txt", "https://raw.githubusercontent.com/mozillazg/phrase-pinyin-data/master/phrase.txt"),
]


def _ensure_external_dicts():
    """首次联网时自动下载开源词库到 exe 同目录 githubMIT/；失败则静默降级（仅用 THUOCL+内置表）。"""
    if not config.AUTO_FETCH:
        return
    missing = [n for n, _ in _DICT_SOURCES if not os.path.exists(_ext_path(n))]
    if not missing:
        return
    try:
        import urllib.request
    except Exception:
        return
    for n, url in _DICT_SOURCES:
        if n not in missing:
            continue
        try:
            os.makedirs(os.path.join(_APP_DIR, "githubMIT", os.path.dirname(n)), exist_ok=True)
        except Exception:
            return
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=90) as r:
                data = r.read()
            with open(os.path.join(_APP_DIR, "githubMIT", n), "wb") as f:
                f.write(data)
        except Exception:
            pass

# 运行时索引
PHRASE_INDEX = {}      # py(str) -> {word: freq}
CHAR_INDEX = {}        # py(str) -> {char: freq}
PHRASE_FIRST = {}      # 首字 -> {word: freq}（联想加速，载入缓存后重建）
WORD_FREQ = {}
CHAR_FREQ = {}
BIGRAM = {}
CHAR_OCC = {}
TOTAL_FREQ = 0
TOTAL_CHAR_FREQ = 0
VOCAB = 0
STATS = {}

# ---------- 模糊音（声母/韵母层级互换）----------
_INITIALS = ["zh", "ch", "sh", "b", "p", "m", "f", "d", "t", "n", "l",
             "g", "k", "h", "j", "q", "x", "r", "z", "c", "s", "y", "w"]
_INITIAL_GROUPS = {
    "z": {"z", "zh"}, "zh": {"z", "zh"},
    "c": {"c", "ch"}, "ch": {"c", "ch"},
    "s": {"s", "sh"}, "sh": {"s", "sh"},
    "n": {"n", "l"}, "l": {"n", "l", "r"}, "r": {"r", "l"},
    "f": {"f", "h"}, "h": {"f", "h"},
}
_FINALS = ["iang", "ian", "uang", "uan", "ang", "eng", "ing", "an", "en", "in"]
_FINAL_GROUPS = {
    "an": {"an", "ang"}, "ang": {"an", "ang"},
    "en": {"en", "eng"}, "eng": {"en", "eng"},
    "in": {"in", "ing"}, "ing": {"in", "ing"},
    "ian": {"ian", "iang"}, "iang": {"ian", "iang"},
    "uan": {"uan", "uang"}, "uang": {"uan", "uang"},
}
FUZZY_CAP = 24  # 单片段模糊展开上限，超出则只用原串


def _fuzzy_variants(s):
    if not config.FUZZY:
        return {s}
    res = {s}
    for init in _INITIALS:
        if s.startswith(init):
            body = s[len(init):]
            for alt in _INITIAL_GROUPS.get(init, {init}):
                res.add(alt + body)
            break
    newres = set()
    for v in res:
        newres.add(v)
        for fin in _FINALS:
            if v.endswith(fin):
                body2 = v[:-len(fin)]
                for alt in _FINAL_GROUPS.get(fin, {fin}):
                    newres.add(body2 + alt)
                break
    return newres


# 带调拼音 -> 无调 ASCII（同时把 ü 归一为 v）。
_TONE_MAP = {
    'ā': 'a', 'á': 'a', 'ǎ': 'a', 'à': 'a',
    'ē': 'e', 'é': 'e', 'ě': 'e', 'è': 'e',
    'ī': 'i', 'í': 'i', 'ǐ': 'i', 'ì': 'i',
    'ō': 'o', 'ó': 'o', 'ǒ': 'o', 'ò': 'o',
    'ū': 'u', 'ú': 'u', 'ǔ': 'u', 'ù': 'u',
    'ǖ': 'v', 'ǘ': 'v', 'ǚ': 'v', 'ǜ': 'v', 'ü': 'v',
    'ń': 'n', 'ň': 'n', 'ǹ': 'n',
    'ḿ': 'm',
}


def _strip_tone(s: str) -> str:
    s = s.lower()
    s = _TONE.sub("", s)  # 去掉数字标调（yi1）
    return "".join(_TONE_MAP.get(c, c) for c in s)


def _char_pinyin_ext(ch: str):
    """外部单字拼音库里的拼音（无调）。"""
    return CHAR_PINYIN_EXT.get(ch, "")


# 由外部单字库填充（build 时）
CHAR_PINYIN_EXT = {}


# ---------- 外部词库解析 ----------
def _load_external_char_dict(path):
    """mozillazg pinyin-data 格式：每行 `U+XXXX: pinyin # 汉字`（如 `U+3447: zhòu  # 㑇`）。
    也兼容 `汉字 拼音`。解析后填充 CHAR_PINYIN_EXT（汉字 -> 无调拼音）。"""
    n = 0
    try:
        with open(path, encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                ch = None
                py = None
                if line.startswith("U+"):
                    # 形如 "U+3447: zhòu  # 㑇"
                    parts = line.split("#", 1)
                    if len(parts) >= 2:
                        ch = parts[1].strip()
                    head = parts[0].split(":", 1)
                    if len(head) >= 2:
                        py = head[1].strip()
                else:
                    toks = line.split()
                    if len(toks) >= 2:
                        ch = toks[0]
                        py = toks[1]
                if not ch or not py:
                    continue
                if len(ch) != 1 or not ('\u4e00' <= ch <= '\u9fff'):
                    continue
                py = _strip_tone(py)
                if py and _PURE.match(py):
                    CHAR_PINYIN_EXT[ch] = py
                    n += 1
    except FileNotFoundError:
        pass
    return n


def _load_external_phrase_dict(path):
    """mozillazg phrase-pinyin-data 格式：每行 `词组 拼音1 拼音2 ...`。返回 {py_key: {word: freq}}。"""
    out = {}
    try:
        with open(path, encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                toks = line.split()
                if len(toks) < 2:
                    continue
                word = toks[0].rstrip(":")  # 上游格式为 `词组: pīn yīn`，去掉词后冒号
                if not word:
                    continue
                syls = [_strip_tone(t) for t in toks[1:] if _strip_tone(t)]
                py_key = "".join(syls)
                if not py_key or not _PURE.match(py_key):
                    continue
                d = out.setdefault(py_key, {})
                d[word] = d.get(word, 0) + 20000  # 无词频，给中等权重
    except FileNotFoundError:
        pass
    return out


# ---------- 缓存 ----------
def _dict_sig():
    has_chars = os.path.exists(_ext_path("pinyin-data/kMandarin.txt"))
    has_phrases = os.path.exists(_ext_path("phrase-pinyin-data/phrase.txt"))
    return (config.CACHE_VERSION, HAS_PINYIN, has_chars, has_phrases)


def _load_cache():
    meta_path = os.path.join(config.CACHE_DIR, "meta.json")
    if not os.path.exists(meta_path):
        return False
    try:
        with open(meta_path, encoding="utf-8") as f:
            meta = json.load(f)
        if meta.get("dict_sig") != list(_dict_sig()):
            return False
        with open(os.path.join(config.CACHE_DIR, "phrase_index.json"), encoding="utf-8") as f:
            PHRASE_INDEX.update(json.load(f))
        with open(os.path.join(config.CACHE_DIR, "char_index.json"), encoding="utf-8") as f:
            CHAR_INDEX.update(json.load(f))
        global TOTAL_FREQ, TOTAL_CHAR_FREQ, VOCAB, WORD_FREQ, CHAR_FREQ, BIGRAM, CHAR_OCC, STATS
        TOTAL_FREQ = meta["total_freq"]
        TOTAL_CHAR_FREQ = meta["total_char_freq"]
        VOCAB = meta["vocab"]
        WORD_FREQ = meta.get("word_freq", {})
        CHAR_FREQ = meta.get("char_freq", {})
        CHAR_OCC = meta.get("char_occ", {})
        BIGRAM = meta.get("bigram", {})
        STATS = meta.get("stats", {})
        _rebuild_derived()
        return True
    except Exception:
        return False


def _save_cache():
    os.makedirs(config.CACHE_DIR, exist_ok=True)
    with open(os.path.join(config.CACHE_DIR, "phrase_index.json"), "w", encoding="utf-8") as f:
        json.dump(PHRASE_INDEX, f, ensure_ascii=False)
    with open(os.path.join(config.CACHE_DIR, "char_index.json"), "w", encoding="utf-8") as f:
        json.dump(CHAR_INDEX, f, ensure_ascii=False)
    meta = {
        "dict_sig": list(_dict_sig()),
        "total_freq": TOTAL_FREQ,
        "total_char_freq": TOTAL_CHAR_FREQ,
        "vocab": VOCAB,
        "word_freq": WORD_FREQ,
        "char_freq": CHAR_FREQ,
        "char_occ": CHAR_OCC,
        "bigram": BIGRAM,
        "stats": STATS,
    }
    with open(os.path.join(config.CACHE_DIR, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False)


def _rebuild_derived():
    """由 PHRASE_INDEX 重建联想/首字母索引（不进缓存，载入即算）。"""
    PHRASE_FIRST.clear()
    INITIALS_INDEX.clear()
    for py_key, d in PHRASE_INDEX.items():
        syls = _split_syllables(py_key)
        initials = "".join(s[0] for s in syls) if syls else ""
        for w, f in d.items():
            if not w:
                continue
            first = w[0]
            if '\u4e00' <= first <= '\u9fff':
                fd = PHRASE_FIRST.setdefault(first, {})
                fd[w] = fd.get(w, 0) + f
            if initials:
                id_ = INITIALS_INDEX.setdefault(initials, {})
                id_[w] = id_.get(w, 0) + f


INITIALS_INDEX = {}  # 首字母串 -> {word: freq}（简拼）


# ---------- 构建 ----------
def build(force=False):
    global PHRASE_INDEX, CHAR_INDEX, TOTAL_FREQ, TOTAL_CHAR_FREQ, VOCAB, WORD_FREQ, CHAR_FREQ, BIGRAM, CHAR_OCC, STATS, CHAR_PINYIN_EXT
    with _lock:
        if not force and _load_cache():
            return STATS

        # 0) 首次联网自动补齐开源词库（缺失时才下载）
        _ensure_external_dicts()

        # 1) THUOCL
        data_dir = config.THUOCL_DATA_DIR
        files = sorted(glob.glob(os.path.join(data_dir, "*.txt")))
        if not files:
            raise FileNotFoundError(
                "未找到 THUOCL 词库文件（%s）。请检查 config.THUOCL_DATA_DIR 或设置环境变量 THUOCL_DATA。" % data_dir
            )

        word_freq = {}
        for fp in files:
            with open(fp, encoding="utf-8", errors="ignore") as fh:
                for line in fh:
                    line = line.rstrip("\n")
                    if not line.strip():
                        continue
                    parts = [p for p in line.split("\t") if p != ""]
                    w = parts[0].strip()
                    if not w:
                        continue
                    try:
                        freq = int(parts[1].strip()) if len(parts) > 1 else 1
                    except ValueError:
                        freq = 1
                    word_freq[w] = word_freq.get(w, 0) + freq

        # 2) 内置常用词（高优先级）
        _cw_candidates = [os.path.join(config.BASE_DIR, "common_words.txt")]
        if getattr(sys, "frozen", False):
            _cw_candidates.append(os.path.join(os.path.dirname(sys.executable), "common_words.txt"))
        if hasattr(sys, "_MEIPASS"):
            _cw_candidates.append(os.path.join(sys._MEIPASS, "common_words.txt"))
        cw_path = next((p for p in _cw_candidates if os.path.exists(p)), _cw_candidates[0])
        if os.path.exists(cw_path):
            with open(cw_path, encoding="utf-8") as _fh:
                for _line in _fh:
                    for _w in _line.split():
                        if _w:
                            word_freq[_w] = word_freq.get(_w, 0) + 300000

        # 3) 外部单字拼音库（全量汉字拼音，使 THUOCL 全词可索引）
        n_chars_dict = _load_external_char_dict(_ext_path("pinyin-data/kMandarin.txt"))

        # 4) 外部词组拼音库（直接带拼音，跳过注音）
        ext_phrases = _load_external_phrase_dict(_ext_path("phrase-pinyin-data/phrase.txt"))

        # 汉字拼音表：外部库 > pypinyin > 内置 fallback
        def char2py(ch):
            p = CHAR_PINYIN_EXT.get(ch)
            if p:
                return p
            if HAS_PINYIN:
                from pypinyin import pinyin as _pp, Style as _St
                try:
                    return _pp(ch, style=_St.NORMAL, heteronym=False)[0][0].lower().replace("ü", "v")
                except Exception:
                    pass
            from pinyin_fallback import CHAR_PINYIN
            return CHAR_PINYIN.get(ch, "")

        # 为 THUOCL + common 批量注音
        chars_set = set()
        for w in word_freq:
            for ch in w:
                if '\u4e00' <= ch <= '\u9fff':
                    chars_set.add(ch)
        cmap = {c: char2py(c) for c in chars_set}

        phrase_index = {}   # py -> {word: freq}
        char_index = {}     # py -> {char: freq}
        char_freq = {}
        char_occ = {}
        bigram = {}
        total_freq = 0
        skipped = 0

        def add_phrase(w, freq):
            nonlocal total_freq, skipped
            py = _word_py(w, cmap)
            if py is None:
                skipped += 1
                return
            d = phrase_index.setdefault(py, {})
            d[w] = d.get(w, 0) + freq
            prev = None
            for ch in w:
                if '\u4e00' <= ch <= '\u9fff':
                    cp = cmap.get(ch, "")
                    if not cp:
                        continue
                    cd = char_index.setdefault(cp, {})
                    cd[ch] = cd.get(ch, 0) + freq
                    char_freq[ch] = char_freq.get(ch, 0) + freq
                    char_occ[ch] = char_occ.get(ch, 0) + freq
                    if prev is not None:
                        key = prev + "\t" + ch
                        bigram[key] = bigram.get(key, 0) + freq
                    prev = ch

        for w, freq in word_freq.items():
            add_phrase(w, freq)

        # 并入外部词组库（已带拼音）
        for py_key, d in ext_phrases.items():
            for w, f in d.items():
                pd = phrase_index.setdefault(py_key, {})
                pd[w] = pd.get(w, 0) + f
                total_freq += f
                prev = None
                for ch in w:
                    if '\u4e00' <= ch <= '\u9fff':
                        cp = cmap.get(ch, "")
                        if not cp:
                            cp = _char_pinyin_ext(ch) or (CHAR_PINYIN_EXT.get(ch, ""))
                        if not cp:
                            continue
                        cd = char_index.setdefault(cp, {})
                        cd[ch] = cd.get(ch, 0) + f
                        char_freq[ch] = char_freq.get(ch, 0) + f
                        char_occ[ch] = char_occ.get(ch, 0) + f
                        if prev is not None:
                            key = prev + "\t" + ch
                            bigram[key] = bigram.get(key, 0) + f
                        prev = ch

        total_freq = sum(sum(d.values()) for d in phrase_index.values())
        total_char_freq = sum(char_freq.values())
        vocab = len(char_freq)

        PHRASE_INDEX.clear(); PHRASE_INDEX.update(phrase_index)
        CHAR_INDEX.clear(); CHAR_INDEX.update(char_index)
        TOTAL_FREQ = total_freq
        TOTAL_CHAR_FREQ = total_char_freq
        VOCAB = vocab
        WORD_FREQ = word_freq
        CHAR_FREQ = char_freq
        BIGRAM = bigram
        CHAR_OCC = char_occ
        STATS = {
            "files": len(files),
            "words": len(word_freq) + len(ext_phrases),
            "indexed_phrases": len(phrase_index),
            "indexed_chars": len(char_index),
            "skipped_words": skipped,
            "chars_dict": n_chars_dict,
            "has_pinyin": HAS_PINYIN,
            "total_freq": total_freq,
        }
        _rebuild_derived()
        _save_cache()
        return STATS


def _word_py(word, cmap):
    out = []
    for ch in word:
        if '\u4e00' <= ch <= '\u9fff':
            p = cmap.get(ch, "")
            if not p:
                return None
            out.append(p)
        else:
            out.append(ch)
    return "".join(out)


# ---------- 模糊音展开 ----------
def _seg_keys(syls, i, L):
    orig = "".join(syls[i:i + L])
    if not config.FUZZY:
        return [orig]
    variants = []
    for s in syls[i:i + L]:
        vs = _fuzzy_variants(s)
        variants.append(list(vs))
    keys = {orig}
    _product(variants, 0, "", keys)
    if len(keys) > FUZZY_CAP:
        return [orig]
    return list(keys)


def _product(variants, idx, acc, out):
    if len(out) > FUZZY_CAP:
        return
    if idx == len(variants):
        out.add(acc)
        return
    for v in variants[idx]:
        _product(variants, idx + 1, acc + v, out)


# ---------- 解码 ----------
def _logp_word(w):
    return math.log(WORD_FREQ.get(w, 1) + 1) - math.log(TOTAL_FREQ + 1)


def _logp_char(c):
    return math.log(CHAR_FREQ.get(c, 1) + 1) - math.log(TOTAL_CHAR_FREQ + 1)


def _logp_bi(a, b):
    key = a + "\t" + b
    num = BIGRAM.get(key, 0) + 1
    den = CHAR_OCC.get(a, 0) + VOCAB + 1
    return math.log(num) - math.log(den)


def decode(pinyin_str, topk=None):
    """拼音串 -> top-k 候选 [{text, score}]。支持整句、模糊音、简拼。"""
    if topk is None:
        topk = config.TOP_K
    if pinyin_str is None:
        return []

    raw = pinyin_str.lower()
    letters = re.sub(r"[^a-z]", "", raw)

    # 简拼：纯辅音串（无元音），按首字母匹配词组
    if letters and len(letters) >= 2 and not re.search(r"[aeiouv]", letters):
        cands = INITIALS_INDEX.get(letters)
        if cands:
            ranked = sorted(cands.items(), key=lambda x: -x[1])[:topk]
            return [{"text": t, "score": round(math.log(f + 1), 3)} for t, f in ranked]
        # 无匹配则退回空（正常 beam 对纯辅音也难产出有效结果）

    syls = [s for s in _split_user(raw) if _PURE.match(s)]
    n = len(syls)
    if n == 0:
        return []

    words_at = {}
    for i in range(n):
        for L in range(1, min(config.MAX_WORD_SYL, n - i) + 1):
            combined = []
            for k in _seg_keys(syls, i, L):
                lst = PHRASE_INDEX.get(k)
                if lst:
                    combined.extend(lst.items())
            if combined:
                words_at[(i, L)] = combined

    beam_width = config.BEAM_WIDTH
    lam = config.LAMBDA_BI
    dp = [[] for _ in range(n + 1)]
    dp[0] = [(0.0, "", None)]

    for pos in range(n):
        states = sorted(dp[pos], key=lambda x: -x[0])[:beam_width]
        for sc, path, last in states:
            for L in range(1, min(config.MAX_WORD_SYL, n - pos) + 1):
                cand = words_at.get((pos, L))
                if not cand:
                    continue
                for w, f in cand:
                    nsc = sc + _logp_word(w) + config.WORD_BONUS
                    if last is not None:
                        nsc += lam * _logp_bi(last, w[0])
                    dp[pos + L].append((nsc, path + w, w[-1]))
            cands = []
            for s in _fuzzy_variants(syls[pos]):
                lst = CHAR_INDEX.get(s)
                if lst:
                    cands.extend(lst.items())
            for c, f in cands:
                nsc = sc + _logp_char(c) - config.CHAR_PENALTY
                if last is not None:
                    nsc += lam * _logp_bi(last, c)
                dp[pos + 1].append((nsc, path + c, c))

    best = {}
    for sc, path, last in dp[n]:
        if path not in best or sc > best[path]:
            best[path] = sc
    ranked = sorted(best.items(), key=lambda x: -x[1])
    return [{"text": t, "score": round(s, 3)} for t, s in ranked[:topk]]


def _split_user(s):
    """复用 pinyin_util 的切分（空格/撇号/标点处理）。"""
    from pinyin_util import split_pinyin
    return split_pinyin(s)


def associate(context, topk=None):
    """上下文联想：以末尾汉字开头的词（PHRASE_FIRST）+ bigram 后继字。"""
    if topk is None:
        topk = config.TOP_K
    if not context:
        return []
    last = None
    for ch in reversed(context):
        if '\u4e00' <= ch <= '\u9fff':
            last = ch
            break
    if last is None:
        return []

    res = []
    fd = PHRASE_FIRST.get(last)
    if fd:
        for w, f in fd.items():
            if len(w) > 1:
                res.append((w, math.log(f + 1), "phrase"))
    prefix = last + "\t"
    succ = {}
    for key, cnt in BIGRAM.items():
        if key.startswith(prefix):
            succ[key.split("\t")[1]] = succ.get(key.split("\t")[1], 0) + cnt
    for c, cnt in succ.items():
        res.append((c, math.log(cnt + 1), "char"))

    res.sort(key=lambda x: -x[1])
    seen = set()
    out = []
    for t, s, k in res:
        if t in seen:
            continue
        seen.add(t)
        out.append({"text": t, "score": round(s, 3), "kind": k})
        if len(out) >= topk:
            break
    return out


def info():
    return STATS


if __name__ == "__main__":
    s = build(force=True)
    print("STATS:", s)
    for q in ["nihao", "woai", "zhongguo", "zhongguogongchandang", "beijingtiananmen", "nh", "wg", "zhognquo"]:
        print(q, "->", [c["text"] for c in decode(q)][:8])
    print("assoc(中国):", [c["text"] for c in associate("中国")][:8])
