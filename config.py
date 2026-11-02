# -*- coding: utf-8 -*-
"""路径与运行配置。可用环境变量覆盖。"""
import os
import sys

if getattr(sys, "frozen", False):
    APP_DIR = os.path.dirname(sys.executable)
else:
    APP_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = APP_DIR


def _resolve(sub):
    """
    资源目录解析：打包(--onefile)后附加数据在 _MEIPASS 临时目录；
    优先用 _MEIPASS 内已打包的，找不到再退回 exe 同目录（便于运行时下载/用户覆盖）。
    """
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        p = os.path.join(sys._MEIPASS, sub)
        if os.path.exists(p):
            return p
    return os.path.join(APP_DIR, sub)


# THUOCL 词库目录（含 THUOCL_*.txt）。指向集中存放开源词库的 githubMIT/THUOCL，
# 使 exe 自包含且署名清晰（LICENSE / README 见 githubMIT/）。
THUOCL_DATA_DIR = os.environ.get("THUOCL_DATA", _resolve("githubMIT/THUOCL"))

# 开源拼音词库根目录（mozillazg pinyin-data / phrase-pinyin-data），
# 实际文件在 githubMIT/pinyin-data/kMandarin.txt 与 githubMIT/phrase-pinyin-data/phrase.txt。
# 由 build_exe.bat 下载并打包；若缺失，首次联网运行会自动下载到 exe 同目录。
DICTS_DIR = os.environ.get("IME_DICTS", _resolve("githubMIT"))

# 拼音索引缓存目录（首次构建后复用，离线也能完整运行）
CACHE_DIR = os.environ.get("IME_CACHE", os.path.join(APP_DIR, "cache"))

# 缓存结构版本：词库加载逻辑变更时 +1，强制重建缓存。
CACHE_VERSION = 4

# Deepseek / llama-server 本地接口（OpenAI 兼容）。未启动则自动降级为词典模式。
DEEPSEEK_URL = os.environ.get("DEEPSEEK_URL", "http://localhost:8080/v1")
DEEPSEEK_MODEL = os.environ.get("DEEPSEEK_MODEL", "local-model")

# 解码参数
TOP_K = 8            # 返回候选数
BEAM_WIDTH = 400     # beam search 宽度（词库变大后适当放宽）
MAX_WORD_SYL = 8     # 一个词最多匹配的音节数
LAMBDA_BI = 0.6      # bigram 语言模型权重
WORD_BONUS = 2.0     # 成词奖励（让词优先于拆字）
CHAR_PENALTY = 0.8   # 单字惩罚

# 词库量级护栏（Google 级）：
#   ESSAY_CAP: RIME essay 收录词条上限（按词频降序截取），0 = 全部收录（默认）。
#   PHRASE_BUCKET_CAP: 每个拼音音节同音词上限，护栏内存/性能，不影响拼音覆盖，0 = 不限制。
#   DECODE_CAND_CAP: 解码时每个切分位置最多考虑的候选词数（按词频优先），护栏长句解码耗时。
ESSAY_CAP = int(os.environ.get("IME_ESSAY_CAP", "0") or 0)
PHRASE_BUCKET_CAP = int(os.environ.get("IME_BUCKET_CAP", "2000") or 0)
DECODE_CAND_CAP = int(os.environ.get("IME_DECODE_CAP", "600") or 0)

# 模糊音（讯飞式容错输入）。开启后 z/zh、c/ch、s/sh、an/ang、en/eng、in/ing、n/l、f/h、r/l 互通。
FUZZY = os.environ.get("IME_FUZZY", "1") not in ("0", "false", "False")

# 首次联网自动下载开源词库（双击即用）。设 IME_FETCH=0 可关闭，仅离线词典。
AUTO_FETCH = os.environ.get("IME_FETCH", "1") not in ("0", "false", "False")
