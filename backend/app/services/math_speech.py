"""LaTeX 数式を「音声で読める日本語」に変換する(VOICEVOX用)。

最重要の不変条件: 出力にバックスラッシュ・中括弧・$ を残さない。
よく出る構文(分数/累乗/根号/ギリシャ文字/演算子)を自然な読みにし、
未知のコマンドは名前だけ読む(バックスラッシュ除去)安全側のフォールバックに倒す。

表示(KaTeX)と同じ数式区切りを共有する: $$ $ \\[ \\] \\( \\) {\\displaystyle ...}。
"""

from __future__ import annotations

import re

# \command(英字)の読み。ここに無いものは名前のまま読む(フォールバック)。
_CMD: dict[str, str] = {
    # ギリシャ文字
    "alpha": "アルファ", "beta": "ベータ", "gamma": "ガンマ", "delta": "デルタ",
    "epsilon": "イプシロン", "varepsilon": "イプシロン", "zeta": "ゼータ",
    "eta": "イータ", "theta": "シータ", "vartheta": "シータ", "iota": "イオタ",
    "kappa": "カッパ", "lambda": "ラムダ", "mu": "ミュー", "nu": "ニュー",
    "xi": "クサイ", "rho": "ロー", "sigma": "シグマ", "tau": "タウ",
    "phi": "ファイ", "varphi": "ファイ", "chi": "カイ", "psi": "プサイ", "omega": "オメガ",
    "Gamma": "ガンマ", "Delta": "デルタ", "Theta": "シータ", "Lambda": "ラムダ",
    "Xi": "クサイ", "Pi": "パイ", "Sigma": "シグマ", "Phi": "ファイ",
    "Psi": "プサイ", "Omega": "オメガ", "pi": "パイ",
    # 演算子・関係
    "times": "かける", "cdot": "かける", "ast": "かける", "div": "わる",
    "pm": "プラスマイナス", "mp": "マイナスプラス",
    "leq": "以下", "le": "以下", "geq": "以上", "ge": "以上",
    "neq": "ノットイコール", "ne": "ノットイコール",
    "approx": "およそ", "sim": "およそ", "equiv": "合同",
    "to": "から", "rightarrow": "から", "Rightarrow": "ならば", "leftarrow": "から",
    "infty": "無限大", "partial": "パーシャル", "nabla": "ナブラ",
    "sum": "総和", "int": "積分", "iint": "二重積分", "oint": "周回積分",
    "prod": "総乗", "lim": "極限", "log": "ログ", "ln": "自然対数ログ",
    "sin": "サイン", "cos": "コサイン", "tan": "タンジェント",
    "exp": "指数関数", "max": "最大", "min": "最小",
    "in": "に含まれる", "subset": "部分集合", "cup": "和集合", "cap": "共通部分",
    "forall": "任意の", "exists": "存在する", "cdots": "など", "dots": "など",
    "ldots": "など", "quad": " ", "qquad": " ",
    # 除去(読まない)
    "left": "", "right": "", "displaystyle": "", "textstyle": "",
    "scriptstyle": "", "mathrm": "", "mathbf": "", "mathbb": "", "mathcal": "",
    "boldsymbol": "", "text": "", "operatorname": "", "limits": "", "nolimits": "",
    "bigl": "", "bigr": "", "Bigl": "", "Bigr": "",
}

# 数式区切り(表示と共通)。display を inline より先に処理する。
_SPAN_PATTERNS = [
    re.compile(r"\$\$([\s\S]*?)\$\$"),
    re.compile(r"\\\[([\s\S]*?)\\\]"),
    re.compile(r"\\\(([\s\S]*?)\\\)"),
    re.compile(r"\$([^$]*)\$"),
]


# 日本語(ひらがな/カタカナ/漢字/全角記号)の連なり。これは数式に含まれない区切り。
_JP_SPLIT = re.compile(r"([぀-ヿ一-鿿　-〿＀-￯]+)")
_JP_CHAR = re.compile(r"[぀-ヿ一-鿿　-〿＀-￯]")
# 数式とみなす「強い手がかり」: バックスラッシュ・上付き・下付き。
_MATH_SIGNAL = re.compile(r"[\\^_]")


def to_speech(text: str) -> str:
    """本文中の数式(区切り有/無)を日本語の読みへ置換し、地の文はそのまま返す。"""
    result = _replace_style_blocks(text)
    for pattern in _SPAN_PATTERNS:
        result = pattern.sub(lambda m: " " + latex_to_speech(m.group(1)) + " ", result)
    # 区切り記号のない地の文中の LaTeX(AI記事に多い)も拾う。
    result = _heuristic(result, latex_to_speech)
    return re.sub(r"[ \t]+", " ", result).strip()


def _heuristic(text: str, convert) -> str:
    """日本語で区切り、非日本語の塊のうち数式の手がかりを含むものを convert する。"""
    out: list[str] = []
    for part in _JP_SPLIT.split(text):
        if not part:
            continue
        if _JP_CHAR.search(part) or not _MATH_SIGNAL.search(part) or not part.strip():
            out.append(part)
        else:
            out.append(" " + convert(part) + " ")
    return "".join(out)


def _replace_style_blocks(text: str) -> str:
    """{\\displaystyle ...} / {\\textstyle ...} を中括弧の対応をとって置換する。"""
    out: list[str] = []
    i = 0
    opener = re.compile(r"\{\\(?:displaystyle|textstyle)\s*")
    while i < len(text):
        m = opener.match(text, i)
        if not m:
            out.append(text[i])
            i += 1
            continue
        depth = 1
        k = m.end()
        while k < len(text) and depth > 0:
            if text[k] == "{":
                depth += 1
            elif text[k] == "}":
                depth -= 1
            k += 1
        inner = text[m.end() : k - 1]
        out.append(" " + latex_to_speech(inner) + " ")
        i = k
    return "".join(out)


def latex_to_speech(tex: str) -> str:
    s = _structural(tex)

    # \command(英字) を読みに。未知はコマンド名のみ(バックスラッシュ除去)。
    s = re.sub(r"\\([a-zA-Z]+)", lambda m: _CMD.get(m.group(1), m.group(1)), s)

    # スペース・整形コマンド(\, \; \! \:)など非英字バックスラッシュを除去
    s = re.sub(r"\\[^a-zA-Z]?", "", s)

    # 直書きの演算子
    for sym, word in (
        ("+", " プラス "),
        ("=", " イコール "),
        ("<", " 小なり "),
        (">", " 大なり "),
        ("*", " かける "),
        ("-", " マイナス "),
        ("/", " わる "),
    ):
        s = s.replace(sym, word)

    # 最終クリーンアップ: 残った TeX 記号を必ず消す(バックスラッシュを残さない)
    s = s.replace("{", "").replace("}", "").replace("$", "").replace("\\", "")
    s = re.sub(r"[()\[\]]", "", s)
    return re.sub(r"\s+", " ", s).strip()


def _structural(s: str) -> str:
    """分数・根号・累乗・添字を内側から解決する。中括弧が減るまでループ。"""
    prev = None
    while prev != s:
        prev = s
        s = re.sub(r"\\hat\{([^{}]*)\}", r"\1ハット", s)
        s = re.sub(r"\\bar\{([^{}]*)\}", r"\1バー", s)
        s = re.sub(r"\\vec\{([^{}]*)\}", r"\1ベクトル", s)
        s = re.sub(r"\\tilde\{([^{}]*)\}", r"\1チルダ", s)
        s = re.sub(r"\\sqrt\[([^\[\]{}]*)\]\{([^{}]*)\}", r"\1乗根\2", s)
        s = re.sub(r"\\sqrt\{([^{}]*)\}", r"ルート\1", s)
        s = re.sub(r"\\frac\{([^{}]*)\}\{([^{}]*)\}", r"\2ぶんの\1", s)
        s = re.sub(r"\^\{([^{}]*)\}", r"の\1乗", s)
        s = re.sub(r"_\{([^{}]*)\}", r"の\1", s)
        s = re.sub(r"\^([A-Za-z0-9])", r"の\1乗", s)
        s = re.sub(r"_([A-Za-z0-9])", r"の\1", s)
    return s
