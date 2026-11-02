# -*- coding: utf-8 -*-
"""
拼音工具：无声调拼音生成 + 连写拼音音节切分。

主路径：若环境安装了 pypinyin，用它生成准确拼音（含多音字处理）。
Fallback：未安装 pypinyin 时，使用 pinyin_fallback.CHAR_PINYIN 覆盖常用字。
"""
import re

# 尝试导入 pypinyin（推荐，覆盖全部汉字与多音字）
try:
    from pypinyin import pinyin as _pypinyin, Style as _Style
    HAS_PINYIN = True
except Exception:
    HAS_PINYIN = False

from pinyin_fallback import CHAR_PINYIN

# 合法无声调拼音音节表（用于切分用户连写的拼音）
_SYL_STR = (
    "a ai an ang ao "
    "ba bai ban bang bao bei ben beng bi bian biao bie bin bing bo bu "
    "ca cai can cang cao ce cen ceng ci cong cou cu cuan cui cun cuo "
    "cha chai chan chang chao che chen cheng chi chong chou chu chuai chuan chuang chui chun chuo "
    "da dai dan dang dao de dei den deng di dia dian diao die ding diu dong dou du duan dui dun duo "
    "e ei en eng er "
    "fa fan fang fei fen feng fo fou fu "
    "ga gai gan gang gao ge gei gen geng gong gou gu gua guai guan guang gui gun guo "
    "ha hai han hang hao he hei hen heng hong hou hu hua huai huan huang hui hun huo "
    "ji jia jian jiang jiao jie jin jing jiong jiu ju juan jue jun "
    "ka kai kan kang kao ke ken keng kong kou ku kua kuai kuan kuang kui kun kuo "
    "la lai lan lang lao le lei leng li lia lian liang liao lie lin ling liu long lou lu lv luan lue lun luo "
    "ma mai man mang mao me mei men meng mi mian miao mie min ming miu mo mou mu "
    "na nai nan nang nao ne nei nen neng ni nian niang niao nie nin ning niu nong nou nu nv nuan nue nuo "
    "o ou "
    "pa pai pan pang pao pei pen peng pi pian piao pie pin ping po pou pu "
    "qi qia qian qiang qiao qie qin qing qiong qiu qu quan que qun "
    "ra ran rang rao re ren reng ri rong rou ru ruan rui run ruo "
    "sa sai san sang sao se sen seng si song sou su suan sui sun suo "
    "sha shai shan shang shao she shen sheng shi shou shu shua shuai shuan shuang shui shun shuo "
    "ta tai tan tang tao te teng ti tian tiao tie ting tong tou tu tuan tui tun tuo "
    "wa wai wan wang wei wen weng wo wu "
    "xi xia xian xiang xiao xie xin xing xiong xiu xu xuan xue xun "
    "ya yan yang yao ye yi yin ying yo yong you yu yuan yue yun "
    "za zai zan zang zao ze zei zen zeng zi zong zou zu zuan zui zun zuo "
    "zha zhai zhan zhang zhao zhe zhen zheng zhi zhong zhou zhu zhua zhuai zhuan zhuang zhui zhun zhuo "
)
SYLLABLES = set(_SYL_STR.split())
_MAX_SYL = max(len(s) for s in SYLLABLES)

# j/q/x/y 后的 u 实为 ü，但在无声调输入中用户通常打 u；l/n 后的 ü 用户常打 v。
# pypinyin 返回的 ü 统一转成 v，便于与用户输入匹配。
_RE_UMLAUT = re.compile(r"[üǔǖǘǚǜ]")


def _to_ascii_py(s: str) -> str:
    s = _RE_UMLAUT.sub("v", s)
    return s.lower()


def char_pinyin(ch: str) -> str:
    """返回单个汉字的无声调拼音（小写，ü 记作 v）。未知返回空串。"""
    if not ch:
        return ""
    if HAS_PINYIN:
        try:
            py = _pypinyin(ch, style=_Style.NORMAL, heteronym=False)[0][0]
            return _to_ascii_py(py)
        except Exception:
            pass
    return CHAR_PINYIN.get(ch, "")


def word_pinyin(word: str):
    """
    返回词/字的无声调连写拼音。
    若任一字无拼音（仅 fallback 缺失时），返回 None，调用方应跳过该词建索引。
    """
    out = []
    for ch in word:
        if '\u4e00' <= ch <= '\u9fff':
            p = char_pinyin(ch)
            if not p:
                return None
            out.append(p)
        else:
            # 非汉字（字母/数字/标点）原样保留
            out.append(ch)
    return "".join(out)


def _split_syllables(token: str):
    """最长匹配把一段字母切分成合法音节列表。"""
    i = 0
    n = len(token)
    res = []
    while i < n:
        matched = False
        for L in range(min(_MAX_SYL, n - i), 0, -1):
            sub = token[i:i + L]
            if sub in SYLLABLES:
                res.append(sub)
                i += L
                matched = True
                break
        if not matched:
            res.append(token[i])
            i += 1
    return res


def split_pinyin(s: str):
    """
    把用户输入（可能带空格、撇号、混有标点）切分为音节列表。
    例：'ni hao' -> ['ni','hao']；'nihao' -> ['ni','hao']；'zhongguo,' -> ['zhong','guo',',']
    """
    if s is None:
        return []
    s = s.lower().strip()
    # 按空白/撇号拆分，字母段做音节切分，其余（标点等）原样保留
    parts = re.split(r"(\s+|')", s)
    res = []
    for p in parts:
        if not p:
            continue
        if re.fullmatch(r"[\s']+", p):
            continue
        if re.fullmatch(r"[a-z]+", p):
            res.extend(_split_syllables(p))
        else:
            # 含非字母（如标点、汉字），逐字符：字母聚集成段切分，其余原样
            buf = ""
            for ch in p:
                if ch.isalpha():
                    buf += ch
                else:
                    if buf:
                        res.extend(_split_syllables(buf))
                        buf = ""
                    res.append(ch)
            if buf:
                res.extend(_split_syllables(buf))
    return res


if __name__ == "__main__":
    print("HAS_PINYIN =", HAS_PINYIN)
    for w in ["你好", "中国", "爱托皮利卡", "人工智能", "nihao", "zhongguo"]:
        print(w, "->", word_pinyin(w), "| split:", split_pinyin(w))
