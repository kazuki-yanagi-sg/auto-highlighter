"""M1: LaTeX → 日本語の読み(音声用)のテスト。

最重要の不変条件: 出力に バックスラッシュ / $ / 中括弧 を絶対に残さない
(VOICEVOX に「バックスラッシュ…」と読ませない)。
"""

from app.services.math_speech import latex_to_speech, to_speech


def _no_tex_residue(s: str) -> bool:
    return all(ch not in s for ch in ["\\", "$", "{", "}"])


# --- latex_to_speech: 個別構文 ---
def test_fraction():
    assert latex_to_speech(r"\frac{a}{b}") == "bぶんのa"


def test_power():
    assert "2乗" in latex_to_speech("x^2")
    assert "2乗" in latex_to_speech("x^{2}")


def test_sqrt():
    assert latex_to_speech(r"\sqrt{x}") == "ルートx"


def test_greek_and_symbols():
    assert latex_to_speech(r"\alpha") == "アルファ"
    assert latex_to_speech(r"\pi") == "パイ"
    assert "無限大" in latex_to_speech(r"\infty")


def test_operators():
    assert "プラス" in latex_to_speech("a + b")
    assert "イコール" in latex_to_speech("a = b")
    assert "かける" in latex_to_speech(r"a \times b")
    assert "総和" in latex_to_speech(r"\sum")


def test_unknown_command_falls_back_without_backslash():
    out = latex_to_speech(r"\foobar x")
    assert _no_tex_residue(out)
    assert "foobar" in out  # コマンド名は読む(バックスラッシュは消す)


def test_never_leaves_backslash_or_braces():
    for tex in [r"\frac{\alpha}{\beta_0}", r"\left( x^2 + 1 \right)", r"\displaystyle\int_0^1 f(x)\,dx"]:
        assert _no_tex_residue(latex_to_speech(tex))


# --- to_speech: 本文中の数式スパンを置換、地の文は保持 ---
def test_to_speech_replaces_inline_dollar():
    out = to_speech("質量は $E = mc^2$ で表される。")
    assert "イコール" in out
    assert "2乗" in out
    assert "で表される。" in out
    assert _no_tex_residue(out)


def test_to_speech_replaces_displaystyle_block():
    out = to_speech(r"確率は {\displaystyle P(A) = \frac{1}{2}} である。")
    assert "ぶんの" in out
    assert "である。" in out
    assert _no_tex_residue(out)


def test_to_speech_handles_paren_delimiters():
    out = to_speech(r"値は \(x^2\) と \[y = a + b\] です。")
    assert "2乗" in out
    assert "プラス" in out
    assert _no_tex_residue(out)


def test_to_speech_plain_text_unchanged():
    assert to_speech("これは普通の文です。") == "これは普通の文です。"


# --- 区切り記号なしの地の文中LaTeX(AI記事に多い) ---
def test_bare_latex_command_in_prose():
    out = to_speech("ここで\\etaは学習率です。")
    assert "イータ" in out
    assert "学習率です。" in out
    assert _no_tex_residue(out)


def test_bare_fraction_in_prose():
    out = to_speech("勾配は \\frac{\\partial u}{\\partial w} = x となります。")
    assert "ぶんの" in out
    assert "パーシャル" in out
    assert "となります。" in out
    assert _no_tex_residue(out)


def test_bare_superscript_and_cdot_in_prose():
    out = to_speech("入力総和は w \\cdot x + b で、y^{(i)} は予測値です。")
    assert "かける" in out
    assert "プラス" in out
    assert "予測値です。" in out
    assert _no_tex_residue(out)


def test_bare_hat_reads_as_hat():
    out = to_speech("\\hat{y} は予測値。")
    assert "ハット" in out
    assert _no_tex_residue(out)


def test_plain_ascii_without_signal_not_mangled():
    # \^_ を含まない英字は数式扱いしない(そのまま)
    out = to_speech("これは DL の話で Chain Rule とも言う。")
    assert "DL" in out
    assert "Chain Rule" in out
