# -*- coding: utf-8 -*-
"""
可选的 Deepseek 增强：调用本地 llama-server（OpenAI 兼容接口）。

前置：按 Deepseek-R1-qwen1.5B 项目说明，把 GGUF 放进 llamacpp/model，
并启动 `llama-server.exe -m model/xxx.gguf -c 15000 -ngl 999`，
默认服务在 http://localhost:8080/v1。

未启动 / 不可达时自动降级（返回空列表），不影响词典输入法正常使用。
"""
import json
import urllib.request
import urllib.error

import config

_available = None  # 缓存探测结果
TIMEOUT = 8


def is_available(force=False):
    global _available
    if not force and _available is not None:
        return _available
    try:
        req = urllib.request.Request(config.DEEPSEEK_URL + "/models")
        with urllib.request.urlopen(req, timeout=2) as r:
            _available = (r.status == 200)
    except Exception:
        _available = False
    return _available


def suggest(context, topk=5):
    """给定已上屏上下文，返回 AI 续写/润色建议列表（字符串）。"""
    if not context or not is_available():
        return []
    prompt = (
        "你是一个中文输入法的智能联想引擎。下面是一段用户已经输入的中文：\n"
        "【" + context + "】\n"
        "请直接给出 " + str(topk) + " 条自然通顺的中文后续补全或整句建议，"
        "每条不超过 24 个字，按最可能优先。只输出建议本身，每行一条，不要编号、不要解释。"
    )
    payload = {
        "model": config.DEEPSEEK_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.4,
        "max_tokens": 200,
        "stream": False,
    }
    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            config.DEEPSEEK_URL + "/chat/completions",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            resp = json.loads(r.read().decode("utf-8"))
        content = resp["choices"][0]["message"]["content"]
        lines = [ln.strip(" 0123456789.、-") for ln in content.splitlines() if ln.strip()]
        out = []
        for ln in lines:
            if ln:
                out.append(ln)
            if len(out) >= topk:
                break
        return out[:topk]
    except Exception:
        return []


if __name__ == "__main__":
    print("available:", is_available(force=True))
    print(suggest("今天天气"))
