#!/usr/bin/env python3
"""パチパチパニック リニューアル提案 — SVG ジェネレーター

キャラクター・ロゴ・パッケージを 1 つのソースから生成する。
フレーバーはパレットを差し替えるだけで展開できる構造にしてある
（採用後の 5 フレーバー × 6 パターン展開を想定）。

    python3 tools/build.py
"""
from __future__ import annotations

import math
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "design"

INK = "#2B0B3F"  # 共通の主線色（全フレーバー共通のブランド要素）

# ---------------------------------------------------------------------------
# フレーバーパレット
# ---------------------------------------------------------------------------
FLAVORS = {
    "grape": dict(
        name="グレープ味", en="GRAPE",
        body="#9046E0", light="#C08BFF", dark="#5E1FA6", ink=INK,
        bg1="#7A1FD1", bg2="#3A0870", ray="#9C3CF0", accent="#FF5CC8",
        crown="#FFE347", crown_dark="#FF9F1C", badge="#4B0F8C",
    ),
    "soda": dict(
        name="ソーダ味", en="SODA",
        body="#2FB4F5", light="#8FDCFF", dark="#1379C2", ink="#0B2A4A",
        bg1="#1C9BE8", bg2="#0A3F8F", ray="#3AB8FF", accent="#FFFFFF",
        crown="#FFE347", crown_dark="#FF9F1C", badge="#0A4FA0",
    ),
    "cola": dict(
        name="コーラ味", en="COLA",
        body="#9A5230", light="#D08A5E", dark="#5C2A14", ink="#2A0E05",
        bg1="#D8232F", bg2="#6E0B12", ray="#EE3E46", accent="#FFE347",
        crown="#FFE347", crown_dark="#FF9F1C", badge="#6E0B12",
    ),
    "melon": dict(
        name="メロンソーダ味", en="MELON SODA",
        body="#39CF6A", light="#9BF0B0", dark="#1C8A3F", ink="#0B3319",
        bg1="#20B85A", bg2="#0A5A2A", ray="#43D774", accent="#FF3F5E",
        crown="#FFE347", crown_dark="#FF9F1C", badge="#0A5A2A",
    ),
    "lemon": dict(
        name="レモンスカッシュ味", en="LEMON SQUASH",
        body="#FFD836", light="#FFF08F", dark="#E0A800", ink="#4A3000",
        bg1="#FFC21A", bg2="#E07A00", ray="#FFD84A", accent="#FFFFFF",
        crown="#FFFFFF", crown_dark="#7FE3FF", badge="#C25E00",
    ),
}

FONT_FACE = """
@font-face{font-family:'Dela';src:url('{p}DelaGothicOne-Regular.ttf')}
@font-face{font-family:'MRound';font-weight:500;src:url('{p}MPLUSRounded1c-Medium.ttf')}
@font-face{font-family:'MRound';font-weight:800;src:url('{p}MPLUSRounded1c-ExtraBold.ttf')}
@font-face{font-family:'Baloo';font-weight:800;src:url('{p}Baloo2-ExtraBold.ttf')}
"""


def font_style(prefix: str) -> str:
    return "<style>" + FONT_FACE.replace("{p}", prefix) + "</style>"


def svg_doc(body: str, vb: str, w: str, h: str, font_prefix="../assets/fonts/") -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb}" width="{w}" height="{h}">'
        f"{font_style(font_prefix)}{body}</svg>\n"
    )


# ---------------------------------------------------------------------------
# パーツ
# ---------------------------------------------------------------------------
def star4(x, y, r, fill, rot=0, stroke=None, sw=0):
    """4 方向に尖ったキラキラ。"""
    k = r * 0.28
    d = (f"M{x},{y-r} Q{x+k*0.35},{y-k*0.35} {x+r},{y} Q{x+k*0.35},{y+k*0.35} {x},{y+r} "
         f"Q{x-k*0.35},{y+k*0.35} {x-r},{y} Q{x-k*0.35},{y-k*0.35} {x},{y-r}Z")
    s = f' stroke="{stroke}" stroke-width="{sw}" stroke-linejoin="round"' if stroke else ""
    return f'<path d="{d}" fill="{fill}"{s} transform="rotate({rot} {x} {y})"/>'


def crackle(x, y, r, color, sw=7, n=5, rot=0):
    """パチッと弾ける放射線。"""
    out = []
    for i in range(n):
        a = math.radians(rot + i * 360 / n)
        x1, y1 = x + math.cos(a) * r * 0.45, y + math.sin(a) * r * 0.45
        x2, y2 = x + math.cos(a) * r, y + math.sin(a) * r
        out.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                   f'stroke="{color}" stroke-width="{sw}" stroke-linecap="round"/>')
    return "".join(out)


BOLT = "M-14,0 L20,0 L6,-44 L28,-44 L-20,-122 L-6,-66 L-28,-66 Z"


def bolt(tx, ty, rot, scale, fill, shade, ink, sw, mirror=False):
    sx = -scale if mirror else scale
    return (f'<g transform="translate({tx},{ty}) rotate({rot}) scale({sx} {scale})">'
            f'<path d="{BOLT}" fill="{fill}" stroke="{ink}" stroke-width="{sw/scale:.1f}" stroke-linejoin="round"/>'
            f'<path d="M6,-44 L28,-44 L-20,-122 L-6,-66 L-2,-66 L14,-50 L2,-50 L12,0 L20,0 Z" fill="{shade}" opacity=".5"/>'
            f'<path d="M-24,-64 L-8,-64 L-14,-40" fill="none" stroke="#fff" stroke-width="{5/scale:.1f}" stroke-linecap="round" stroke-linejoin="round" opacity=".9"/>'
            f"</g>")


BODY = ("M0,-165 C112,-165 188,-98 188,8 C188,122 106,188 0,188 "
        "C-106,188 -188,122 -188,8 C-188,-98 -112,-165 0,-165Z")


def pacchin(f: dict, pose="cheer", mouth="open", eyes="normal", sparks=True, accessory=True, uid="p") -> str:
    """主人公「パッチン」。原点 = 体の中心。おおよそ幅 520 / 高さ 520。

    pose: cheer（ばんざい）/ wave（手をふる）
    mouth: open（パチパチ口）/ smile / o（びっくり）
    eyes: normal / happy（ニコッ）/ wink / wide（びっくり）
    """
    ink, sw = f["ink"], 11
    g = []
    gid = f"{uid}{f['en'].replace(' ', '')}"
    g.append(
        f'<defs><radialGradient id="{gid}b" cx=".38" cy=".3" r=".85">'
        f'<stop offset="0" stop-color="{f["light"]}"/><stop offset=".55" stop-color="{f["body"]}"/>'
        f'<stop offset="1" stop-color="{f["dark"]}"/></radialGradient>'
        f'<clipPath id="{gid}c"><path d="{BODY}"/></clipPath></defs>'
    )
    # はじけクラウン（全フレーバー共通のアイコン）
    crown = [(-84, -120, -26, 1.05), (4, -148, 0, 1.3), (88, -120, 26, 1.05)]
    g.append('<g class="crown">')
    for tx, ty, rot, sc in crown:
        g.append(bolt(tx, ty, rot, sc, f["crown"], f["crown_dark"], ink, sw, mirror=tx > 0))
    g.append("</g>")
    if sparks:
        g.append('<g class="sparks">')
        g.append(star4(-150, -250, 26, f["crown"], 10, ink, 5))
        g.append(star4(158, -262, 32, f["crown"], -8, ink, 5))
        g.append(star4(-205, -150, 16, "#fff"))
        g.append(star4(215, -170, 18, "#fff"))
        g.append(crackle(0, -300, 40, f["crown"], 8, 5, -90))
        g.append("</g>")

    # 腕（体の後ろ側）
    def arm(x1, y1, x2, y2):
        return (f'<path d="M{x1},{y1} Q{(x1+x2)/2 + (8 if x2>0 else -8)},{(y1+y2)/2+20} {x2},{y2}" fill="none" '
                f'stroke="{ink}" stroke-width="{48+sw*2}" stroke-linecap="round"/>'
                f'<path d="M{x1},{y1} Q{(x1+x2)/2 + (8 if x2>0 else -8)},{(y1+y2)/2+20} {x2},{y2}" fill="none" '
                f'stroke="{f["body"]}" stroke-width="48" stroke-linecap="round"/>')

    if pose == "cheer":
        g.append(f'<g class="arm-l">{arm(-150, 10, -238, -92)}</g>')
        g.append(f'<g class="arm-r">{arm(150, 10, 238, -92)}</g>')
    else:
        g.append(f'<g class="arm-l">{arm(-160, 40, -232, 110)}</g>')
        g.append(f'<g class="arm-r">{arm(150, 10, 238, -92)}</g>')

    # 足
    for x in (-72, 72):
        g.append(f'<ellipse cx="{x}" cy="190" rx="52" ry="32" fill="{f["dark"]}" stroke="{ink}" stroke-width="{sw}"/>')

    # ボディ（キャンディの結晶）
    g.append(f'<path d="{BODY}" fill="url(#{gid}b)"/>')
    g.append(f'<g clip-path="url(#{gid}c)">'
             # 結晶のファセット
             f'<path d="M-188,-40 L-95,-150 L-40,-60 Z" fill="#fff" opacity=".22"/>'
             f'<path d="M-40,-60 L-95,-150 L20,-170 Z" fill="#fff" opacity=".12"/>'
             f'<path d="M120,190 L188,40 L60,120 Z" fill="{f["dark"]}" opacity=".45"/>'
             f'<path d="M-188,60 L-120,190 L-60,150 Z" fill="{f["dark"]}" opacity=".3"/>'
             # 中に閉じ込められたパチパチ粒
             f'<circle cx="-120" cy="120" r="9" fill="#fff" opacity=".5"/>'
             f'<circle cx="-95" cy="150" r="5" fill="#fff" opacity=".5"/>'
             f'<circle cx="130" cy="-60" r="7" fill="#fff" opacity=".45"/>'
             f"</g>")
    g.append(f'<path d="{BODY}" fill="none" stroke="{ink}" stroke-width="{sw}"/>')
    # ハイライト
    g.append('<path d="M-128,-92 Q-100,-132 -52,-146" fill="none" stroke="#fff" stroke-width="16" '
             'stroke-linecap="round" opacity=".9"/>')
    g.append('<circle cx="-150" cy="-50" r="9" fill="#fff" opacity=".9"/>')

    # 顔
    face = ['<g class="face">']
    face.append(f'<ellipse cx="-118" cy="60" rx="30" ry="18" fill="{f["accent"] if f["accent"]!="#FFFFFF" else "#FF7FB0"}" opacity=".55"/>')
    face.append(f'<ellipse cx="118" cy="60" rx="30" ry="18" fill="{f["accent"] if f["accent"]!="#FFFFFF" else "#FF7FB0"}" opacity=".55"/>')
    face.append('<g class="eyes">')
    for ex in (-62, 62):
        closed = eyes == "happy" or (eyes == "wink" and ex > 0)
        if closed:
            face.append(f'<path d="M{ex-34},-4 Q{ex},-50 {ex+34},-4" fill="none" stroke="{ink}" stroke-width="13" stroke-linecap="round"/>')
            continue
        face.append(f'<ellipse cx="{ex}" cy="-12" rx="42" ry="52" fill="#fff" stroke="{ink}" stroke-width="9"/>')
        if eyes == "wide":
            face.append(f'<ellipse cx="{ex}" cy="-12" rx="15" ry="19" fill="{ink}"/>')
            face.append(f'<circle cx="{ex+5}" cy="-18" r="5" fill="#fff"/>')
            continue
        face.append(f'<ellipse cx="{ex+4}" cy="-20" rx="27" ry="35" fill="{ink}"/>')
        face.append(star4(ex + 12, -34, 14, "#fff", 0))
        face.append(f'<circle cx="{ex-6}" cy="-2" r="6" fill="#fff"/>')
    face.append("</g>")
    face.append(f'<path d="M-88,-86 Q-62,-104 -36,-88" fill="none" stroke="{ink}" stroke-width="9" stroke-linecap="round"/>')
    face.append(f'<path d="M36,-88 Q62,-104 88,-86" fill="none" stroke="{ink}" stroke-width="9" stroke-linecap="round"/>')
    if mouth == "open":
        face.append(f'<path d="M-58,48 Q0,62 58,48 Q50,128 0,130 Q-50,128 -58,48Z" fill="#6A0F2E" '
                    f'stroke="{ink}" stroke-width="9" stroke-linejoin="round"/>')
        face.append('<path d="M-34,110 Q0,86 34,110 Q20,128 0,128 Q-20,128 -34,110Z" fill="#FF6F91"/>')
        # 口の中でパチパチ
        face.append(star4(-18, 84, 11, "#FFE347"))
        face.append(star4(20, 78, 8, "#fff"))
        face.append(star4(4, 100, 6, "#FFE347"))
    elif mouth == "o":
        face.append(f'<ellipse cx="0" cy="84" rx="30" ry="36" fill="#6A0F2E" stroke="{ink}" stroke-width="9"/>')
        face.append(star4(0, 84, 12, "#FFE347"))
    else:
        face.append(f'<path d="M-46,54 Q0,104 46,54" fill="#6A0F2E" stroke="{ink}" stroke-width="9" '
                    f'stroke-linejoin="round" stroke-linecap="round"/>')
    face.append("</g>")
    g.extend(face)

    # フレーバーアクセサリー
    if accessory:
        g.append(f'<g class="acc">{accessory_for(f)}</g>')
    return "".join(g)


def accessory_for(f: dict) -> str:
    ink = f["ink"]
    en = f["en"]
    if en == "GRAPE":
        # ぶどうの葉っぱ＋つるのヘアピン
        return (f'<g transform="translate(128,-118) rotate(28)">'
                f'<path d="M0,0 C-10,-30 10,-55 30,-60 C28,-40 50,-38 62,-50 C66,-26 54,-6 30,4 C20,8 8,6 0,0Z" '
                f'fill="#4CC94F" stroke="{ink}" stroke-width="8" stroke-linejoin="round"/>'
                f'<path d="M4,-4 Q24,-24 44,-36" fill="none" stroke="#2E8C31" stroke-width="5" stroke-linecap="round"/>'
                f'<path d="M-6,4 C-26,8 -30,-14 -16,-18 C-6,-20 -4,-8 -12,-6" fill="none" stroke="{ink}" '
                f'stroke-width="5" stroke-linecap="round"/>'
                f'<circle cx="-4" cy="26" r="17" fill="#B57BFF" stroke="{ink}" stroke-width="7"/>'
                f'<circle cx="26" cy="22" r="17" fill="#9046E0" stroke="{ink}" stroke-width="7"/>'
                f'<circle cx="12" cy="48" r="17" fill="#7A2FD0" stroke="{ink}" stroke-width="7"/>'
                f'<circle cx="-9" cy="20" r="5" fill="#fff"/><circle cx="21" cy="16" r="5" fill="#fff"/>'
                f"</g>")
    if en == "SODA":
        return (f'<g transform="translate(140,-110)">'
                + "".join(f'<circle cx="{x}" cy="{y}" r="{r}" fill="#fff" fill-opacity=".85" stroke="{ink}" stroke-width="6"/>'
                          for x, y, r in ((0, 0, 22), (34, -26, 14), (8, -44, 10)))
                + "</g>")
    if en == "COLA":
        # 王冠キャップ
        pts = " ".join(f"{math.cos(math.radians(a))*(40 if i%2 else 33):.1f},{math.sin(math.radians(a))*(40 if i%2 else 33):.1f}"
                       for i, a in enumerate(range(0, 360, 20)))
        return (f'<g transform="translate(140,-112) rotate(20)"><polygon points="{pts}" fill="#E8303A" '
                f'stroke="{ink}" stroke-width="7" stroke-linejoin="round"/>'
                f'<circle r="20" fill="#fff" stroke="{ink}" stroke-width="5"/></g>')
    if en == "MELON SODA":
        # さくらんぼ
        return (f'<g transform="translate(130,-120)"><path d="M0,40 Q10,0 40,-20 M30,44 Q34,10 40,-20" fill="none" '
                f'stroke="{ink}" stroke-width="6" stroke-linecap="round"/>'
                f'<circle cx="0" cy="48" r="20" fill="#FF3F5E" stroke="{ink}" stroke-width="7"/>'
                f'<circle cx="32" cy="52" r="20" fill="#E8203F" stroke="{ink}" stroke-width="7"/>'
                f'<circle cx="-6" cy="42" r="5" fill="#fff"/></g>')
    if en == "LEMON SQUASH":
        return (f'<g transform="translate(140,-110) rotate(-15)"><circle r="36" fill="#FFF3A0" stroke="{ink}" stroke-width="7"/>'
                f'<circle r="26" fill="#FFE347"/>'
                + "".join(f'<line x1="0" y1="0" x2="{math.cos(math.radians(a))*26:.1f}" y2="{math.sin(math.radians(a))*26:.1f}" stroke="#FFF8C8" stroke-width="4"/>'
                          for a in range(0, 360, 45))
                + "</g>")
    return ""


def shuwarin(ink=INK, uid="s") -> str:
    """相棒「シュワリン」（ソーダ味のラムネ）。原点中心、直径 ~200。"""
    return (
        f'<defs><radialGradient id="{uid}r" cx=".4" cy=".35" r=".8"><stop offset="0" stop-color="#FFFFFF"/>'
        f'<stop offset=".7" stop-color="#DDF4FF"/><stop offset="1" stop-color="#9FD8F5"/></radialGradient></defs>'
        f'<ellipse cx="0" cy="8" rx="100" ry="92" fill="#7CC6EC" stroke="{ink}" stroke-width="9"/>'
        f'<ellipse cx="0" cy="0" rx="100" ry="88" fill="url(#{uid}r)" stroke="{ink}" stroke-width="9"/>'
        f'<path d="M-62,-58 Q0,-86 62,-58" fill="none" stroke="#B9E3F7" stroke-width="7" stroke-linecap="round"/>'
        f'<path d="M-60,-40 Q-70,-10 -60,20" fill="none" stroke="#fff" stroke-width="10" stroke-linecap="round"/>'
        # ねむそうな目
        f'<g class="s-eyes"><path d="M-48,0 Q-32,14 -16,0" fill="none" stroke="{ink}" stroke-width="8" stroke-linecap="round"/>'
        f'<path d="M16,0 Q32,14 48,0" fill="none" stroke="{ink}" stroke-width="8" stroke-linecap="round"/></g>'
        f'<path d="M-10,32 Q0,40 10,32" fill="none" stroke="{ink}" stroke-width="7" stroke-linecap="round"/>'
        f'<ellipse cx="-62" cy="24" rx="16" ry="9" fill="#8FD0FF" opacity=".8"/>'
        f'<ellipse cx="62" cy="24" rx="16" ry="9" fill="#8FD0FF" opacity=".8"/>'
        # シュワシュワの泡
        f'<g class="bubbles">'
        f'<circle cx="92" cy="-86" r="13" fill="#fff" fill-opacity=".7" stroke="{ink}" stroke-width="5"/>'
        f'<circle cx="118" cy="-120" r="8" fill="#fff" fill-opacity=".7" stroke="{ink}" stroke-width="4"/>'
        f'<circle cx="96" cy="-146" r="5" fill="#fff" fill-opacity=".7" stroke="{ink}" stroke-width="3"/></g>'
    )


# ---------------------------------------------------------------------------
# ロゴ
# ---------------------------------------------------------------------------
LOGO_LINE1 = [("パ", 150, -7, 0), ("チ", 150, 5, 10), ("パ", 150, -5, -4), ("チ", 150, 7, 8)]
LOGO_LINE2 = [("パ", 176, -4, 0), ("ニ", 176, 3, 6), ("ッ", 122, -6, 30), ("ク", 176, 6, 0)]


def logo(f: dict, uid="lg", with_tag=True, fill1="#FFE347", fill2="#FF8A1C") -> str:
    """ロゴ。原点 = 上段中央のベースライン付近。幅 ~680 / 高さ ~420。"""
    ink = f["ink"]
    parts = [
        f'<defs><linearGradient id="{uid}g" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="#FFFBD0"/><stop offset=".38" stop-color="{fill1}"/>'
        f'<stop offset="1" stop-color="{fill2}"/></linearGradient></defs>'
    ]

    def line(chars, y, tracking):
        total = sum(sz * adv for (_, sz, _, _), adv in zip(chars, tracking))
        x = -total / 2
        layers = ([], [], [], [])
        for (ch, sz, rot, dy), adv in zip(chars, tracking):
            cx = x + sz * adv / 2
            t = f'transform="translate({cx:.1f},{y+dy}) rotate({rot})"'
            base = f'font-family="Dela" font-size="{sz}" text-anchor="middle" {t}'
            layers[0].append(f'<text {base} dy=".36em" fill="#fff" stroke="#fff" stroke-width="44" stroke-linejoin="round">{ch}</text>')
            layers[1].append(f'<text {base} dy=".36em" fill="{ink}" stroke="{ink}" stroke-width="24" stroke-linejoin="round" transform-origin="0 0">{ch}</text>')
            layers[2].append(f'<text {base} dy=".36em" dx="6" fill="{ink}" stroke="{ink}" stroke-width="24" stroke-linejoin="round">{ch}</text>')
            layers[3].append(f'<text {base} dy=".36em" fill="url(#{uid}g)">{ch}</text>')
            x += sz * adv
        return layers

    l1 = line(LOGO_LINE1, 0, [0.98, 0.98, 0.98, 0.98])
    l2 = line(LOGO_LINE2, 176, [0.98, 0.98, 0.8, 0.98])
    # 背面のバースト（はじける形）
    burst = []
    rnd = random.Random(7)
    for i in range(28):
        a = i * 360 / 28
        r = 330 if i % 2 == 0 else 260 + rnd.randint(-12, 12)
        burst.append(f"{math.cos(math.radians(a))*r:.1f},{math.sin(math.radians(a))*r*0.5+88:.1f}")
    parts.append(f'<polygon points="{" ".join(burst)}" fill="{f["accent"] if f["en"]=="GRAPE" else "#FF5CC8"}" '
                 f'stroke="{ink}" stroke-width="10" stroke-linejoin="round"/>')
    for layer in (l1[0] + l2[0], l1[2] + l2[2], l1[1] + l2[1], l1[3] + l2[3]):
        parts.extend(layer)
    # 文字のハイライトとパチッ
    parts.append(star4(-292, -62, 30, "#fff", 12, ink, 6))
    parts.append(star4(300, 150, 26, "#fff", -10, ink, 6))
    parts.append(crackle(310, -70, 46, "#FFE347", 9, 4, -60))
    parts.append(crackle(-310, 210, 40, "#FFE347", 9, 4, 120))
    if with_tag:
        parts.append(popping_tag(ink, 0, 300))
    return "".join(parts)


def popping_tag(ink, x, y, scale=1.0):
    return (f'<g transform="translate({x},{y}) rotate(-4) scale({scale})">'
            f'<path d="M-255,-36 L255,-36 L235,0 L255,36 L-255,36 L-235,0Z" fill="{ink}" transform="translate(6,7)"/>'
            f'<path d="M-255,-36 L255,-36 L235,0 L255,36 L-255,36 L-235,0Z" fill="#FFFFFF" stroke="{ink}" stroke-width="8" stroke-linejoin="round"/>'
            f'<text x="0" y="17" font-family="Baloo" font-weight="800" font-size="54" text-anchor="middle" '
            f'fill="{ink}" letter-spacing="2">Popping Panic</text>'
            f"</g>")


# ---------------------------------------------------------------------------
# パッケージ（縦 110 × 横 77mm → viewBox 770 × 1100、1unit = 0.1mm）
# ---------------------------------------------------------------------------
def candy_pile(f, x, y, s=1.0):
    rnd = random.Random(3)
    shards = []
    cols = [f["light"], f["body"], f["dark"], f["body"], f["light"]]
    for i in range(11):
        cx = rnd.uniform(-70, 70)
        cy = rnd.uniform(-18, 22) - (40 - abs(cx)) * 0.35
        r = rnd.uniform(16, 26)
        n = rnd.choice((4, 5, 6))
        rot = rnd.uniform(0, 360)
        pts = " ".join(f"{cx+math.cos(math.radians(rot+k*360/n))*r*rnd.uniform(.7,1.1):.1f},"
                       f"{cy+math.sin(math.radians(rot+k*360/n))*r*rnd.uniform(.7,1.1):.1f}" for k in range(n))
        shards.append(f'<polygon points="{pts}" fill="{cols[i % 5]}" stroke="{f["ink"]}" stroke-width="5" stroke-linejoin="round"/>')
    sparks = (star4(-74, -52, 14, "#FFE347", 0, f["ink"], 4) + star4(80, -44, 11, "#FFE347", 15, f["ink"], 4)
              + crackle(0, -58, 26, "#FFE347", 5, 5, -90))
    return f'<g transform="translate({x},{y}) scale({s})">{"".join(shards)}{sparks}</g>'


def ramune_pile(ink, x, y, s=1.0):
    out = []
    for cx, cy in ((-48, 10), (48, 10), (0, 18), (-24, -22), (26, -20)):
        out.append(f'<ellipse cx="{cx}" cy="{cy+7}" rx="36" ry="30" fill="#8CCCEE" stroke="{ink}" stroke-width="5"/>'
                   f'<ellipse cx="{cx}" cy="{cy}" rx="36" ry="30" fill="#F3FBFF" stroke="{ink}" stroke-width="5"/>'
                   f'<path d="M{cx-18},{cy-10} Q{cx},{cy-18} {cx+18},{cy-10}" fill="none" stroke="#BFE6F8" stroke-width="4" stroke-linecap="round"/>')
    out.append(f'<circle cx="70" cy="-44" r="9" fill="#fff" stroke="{ink}" stroke-width="4"/>'
               f'<circle cx="86" cy="-66" r="6" fill="#fff" stroke="{ink}" stroke-width="3"/>')
    return f'<g transform="translate({x},{y}) scale({s})">{"".join(out)}</g>'


# 1 フレーバーにつき 6 パターン（ポーズ・表情・フキダシを替える“集めたくなる”仕掛け）
VARIANTS = [
    dict(pose="cheer", eyes="normal", mouth="open", say=("パッ", "チーン!")),
    dict(pose="wave", eyes="wink", mouth="smile", say=("パチッ", "とね☆")),
    dict(pose="cheer", eyes="wide", mouth="o", say=("ビック", "リ!?")),
    dict(pose="wave", eyes="happy", mouth="open", say=("ワク", "ワク!")),
    dict(pose="cheer", eyes="happy", mouth="smile", say=("シュ", "ワ〜♪")),
    dict(pose="cheer", eyes="wink", mouth="open", say=("はじけ", "ろー!")),
]


def package(f: dict, uid="pk", variant=0) -> str:
    v = VARIANTS[variant]
    ink = f["ink"]
    W, H = 770, 1100
    p = [f'<defs><radialGradient id="{uid}bg" cx=".5" cy=".5" r=".75">'
         f'<stop offset="0" stop-color="{f["bg1"]}"/><stop offset="1" stop-color="{f["bg2"]}"/></radialGradient>'
         f'<pattern id="{uid}dot" width="22" height="22" patternUnits="userSpaceOnUse">'
         f'<circle cx="11" cy="11" r="3.2" fill="#fff" opacity=".13"/></pattern>'
         f'<clipPath id="{uid}clip"><rect width="{W}" height="{H}"/></clipPath></defs>']
    p.append(f'<g clip-path="url(#{uid}clip)">')
    p.append(f'<rect width="{W}" height="{H}" fill="url(#{uid}bg)"/>')
    # 集中線（サンバースト）
    cx, cy = 385, 600
    rays = []
    for i in range(24):
        a0, a1 = math.radians(i * 15), math.radians(i * 15 + 7.5)
        rays.append(f"M{cx},{cy} L{cx+math.cos(a0)*1400:.0f},{cy+math.sin(a0)*1400:.0f} "
                    f"L{cx+math.cos(a1)*1400:.0f},{cy+math.sin(a1)*1400:.0f}Z")
    p.append(f'<path d="{" ".join(rays)}" fill="{f["ray"]}" opacity=".55"/>')
    p.append(f'<rect width="{W}" height="{H}" fill="url(#{uid}dot)"/>')
    # 背景のパチパチ粒
    rnd = random.Random(11)
    for _ in range(26):
        x, y = rnd.uniform(20, 750), rnd.uniform(380, 860)
        if 170 < x < 600 and 420 < y < 840:
            continue
        p.append(star4(round(x), round(y), rnd.uniform(7, 16), rnd.choice(["#fff", "#FFE347", f["accent"]]), rnd.uniform(0, 45)))
    # キャラクター
    p.append(f'<g transform="translate(398,660) scale(.8)">{pacchin(f, pose=v["pose"], eyes=v["eyes"], mouth=v["mouth"], uid=uid+"c")}</g>')
    # シュワリン（ひょっこり）
    sw_t = "translate(150,770) scale(.72) rotate(-8)" if v["say"][0] == "シュ" else "translate(112,800) scale(.52) rotate(-12)"
    p.append(f'<g transform="{sw_t}">{shuwarin(ink, uid+"s")}</g>')
    # フキダシ「パッチーン!」
    p.append(f'<g transform="translate(652,530) rotate(10)">'
             f'<path d="M-92,-40 L-60,-62 L-20,-52 L10,-74 L40,-50 L84,-60 L92,-18 L110,10 L80,36 L70,70 L30,52 '
             f'L-6,74 L-40,50 L-84,58 L-88,20 L-112,-6Z" fill="#fff" stroke="{ink}" stroke-width="7" stroke-linejoin="round"/>'
             f'<text y="-6" font-family="Dela" font-size="40" text-anchor="middle" fill="{f["badge"]}">{v["say"][0]}</text>'
             f'<text y="38" font-family="Dela" font-size="40" text-anchor="middle" fill="{f["badge"]}">{v["say"][1]}</text></g>')

    # ロゴ
    p.append(f'<g transform="translate(385,104) scale(.86)">{logo(f, uid=uid+"l")}</g>')

    # フレーバー表記
    p.append(f'<g transform="translate(385,905)">'
             f'<rect x="-230" y="-52" width="460" height="100" rx="50" fill="{ink}" transform="translate(6,8)"/>'
             f'<rect x="-230" y="-52" width="460" height="100" rx="50" fill="{f["badge"]}" stroke="#fff" stroke-width="8"/>'
             f'<rect x="-230" y="-52" width="460" height="100" rx="50" fill="none" stroke="{ink}" stroke-width="4" transform="scale(1.04 1.1)"/>'
             f'<text y="{int(22*min(66, 400/len(f["name"]))/66)}" font-family="Dela" font-size="{min(66, 400/len(f["name"])):.0f}" text-anchor="middle" fill="#fff" '
             f'stroke="{ink}" stroke-width="10" paint-order="stroke" letter-spacing="4">{f["name"]}</text>'
             + (f'<g transform="translate(-222,-40) scale(.62)">{accessory_for(f).replace("translate(128,-118)", "translate(0,0)")}</g>'
                if f["en"] == "GRAPE" else "")
             + "</g>")

    # 中身の説明パネル
    p.append(f'<g transform="translate(385,1006)">'
             f'<rect x="-352" y="-46" width="704" height="82" rx="22" fill="#fff" stroke="{ink}" stroke-width="6"/>'
             f"{candy_pile(f, -286, 6, .52)}"
             f'<text x="-116" y="-6" font-family="MRound" font-weight="800" font-size="34" text-anchor="middle" fill="{f["badge"]}">はじける</text>'
             f'<text x="-116" y="28" font-family="MRound" font-weight="800" font-size="34" text-anchor="middle" fill="{f["badge"]}">キャンディ</text>'
             f'<circle cx="0" cy="-4" r="24" fill="{f["accent"] if f["accent"]!="#FFFFFF" else "#FF5CC8"}" stroke="{ink}" stroke-width="5"/>'
             f'<text x="0" y="8" font-family="Dela" font-size="36" text-anchor="middle" fill="#fff">+</text>'
             f'{ramune_pile(ink, 280, 4, .5)}'
             f'<text x="126" y="-6" font-family="MRound" font-weight="800" font-size="34" text-anchor="middle" fill="#1379C2">ソーダ味の</text>'
             f'<text x="126" y="28" font-family="MRound" font-weight="800" font-size="34" text-anchor="middle" fill="#1379C2">ラムネ</text>'
             f"</g>")

    # 下帯：atrion ロゴ（支給データに差し替え）・注意文
    p.append(f'<rect y="1044" width="{W}" height="56" fill="{ink}"/>')
    p.append('<g transform="translate(22,1056)"><rect width="132" height="32" rx="7" fill="#fff"/>'
             f'<text x="66" y="24" font-family="Baloo" font-weight="800" font-size="27" text-anchor="middle" fill="{ink}">atrion</text></g>')
    fs = 18
    note = "※噛まずに、なめながら食べてください。"
    nx = 750 - fs * len(note)
    p.append(f'<text x="{nx}" y="1067" font-family="MRound" font-weight="800" font-size="{fs}" fill="#fff">無果汁 香料使用</text>')
    p.append(f'<text x="{nx}" y="1091" font-family="MRound" font-weight="800" font-size="{fs}" fill="#fff">{note}</text>')
    # 「食(た)べて」はルビ表記
    rx = nx + fs * note.index("食") + fs / 2
    p.append(f'<text x="{rx}" y="1073.5" font-family="MRound" font-weight="800" font-size="9" text-anchor="middle" fill="#fff">た</text>')
    p.append("</g>")
    return "".join(p)


# ---------------------------------------------------------------------------
# 出力
# ---------------------------------------------------------------------------
def write(name: str, content: str):
    path = OUT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print("wrote", path.relative_to(ROOT))


def main():
    g = FLAVORS["grape"]
    write("package_grape.svg", svg_doc(package(g), "0 0 770 1100", "77mm", "110mm"))
    write("logo.svg", svg_doc(f'<g transform="translate(400,190)">{logo(g)}</g>', "0 0 800 580", "800", "580"))
    write("logo_mono.svg", svg_doc(
        f'<g transform="translate(400,190)">{logo(dict(g, accent="#FFFFFF"), uid="m", fill1="#FFFFFF", fill2="#FFFFFF")}</g>',
        "0 0 800 580", "800", "580"))
    write("character_pacchin_grape.svg", svg_doc(
        f'<g transform="translate(300,340)">{pacchin(g)}</g>', "0 0 600 600", "600", "600"))
    write("character_shuwarin.svg", svg_doc(
        f'<g transform="translate(160,170)">{shuwarin()}</g>', "0 0 320 300", "320", "300"))
    write("character_sheet.svg", svg_doc(character_sheet(), "0 0 1800 1100", "1800", "1100"))
    write("proposal_board.svg", svg_doc(proposal_board(), "0 0 2400 1500", "2400", "1500"))
    for i in range(len(VARIANTS)):
        write(f"patterns/package_grape_{i+1}.svg", svg_doc(package(g, uid=f"v{i}", variant=i), "0 0 770 1100", "77mm", "110mm",
                                                         font_prefix="../../assets/fonts/"))
    # 参考：5 フレーバー展開イメージ
    for key, f in FLAVORS.items():
        write(f"flavors/package_{key}.svg", svg_doc(package(f, uid="pk" + key), "0 0 770 1100", "77mm", "110mm",
                                                    font_prefix="../../assets/fonts/"))
        write(f"flavors/pacchin_{key}.svg", svg_doc(
            f'<g transform="translate(300,340)">{pacchin(f, uid="c" + key)}</g>', "0 0 600 600", "600", "600",
            font_prefix="../../assets/fonts/"))


EXPRESSIONS = [
    ("ばんざい", dict(pose="cheer", eyes="normal", mouth="open")),
    ("ウインク", dict(pose="wave", eyes="wink", mouth="smile")),
    ("びっくり", dict(pose="cheer", eyes="wide", mouth="o")),
    ("ニコニコ", dict(pose="wave", eyes="happy", mouth="open")),
]


def character_sheet() -> str:
    g = FLAVORS["grape"]
    ink = INK
    out = [f'<rect width="1800" height="1100" fill="#FFF8EC"/>',
           f'<rect x="0" y="0" width="1800" height="130" fill="{g["badge"]}"/>',
           f'<text x="60" y="88" font-family="Dela" font-size="60" fill="#fff">パッチン</text>',
           f'<text x="330" y="86" font-family="Baloo" font-weight="800" font-size="40" fill="#FFE347">PACCHIN</text>',
           f'<text x="1740" y="84" font-family="MRound" font-weight="800" font-size="30" fill="#fff" text-anchor="end">'
           f'キャラクターシート ／ パチパチパニック</text>']
    for i, (label, kw) in enumerate(EXPRESSIONS):
        x = 230 + i * 360
        out.append(f'<g transform="translate({x},430) scale(.62)">{pacchin(g, uid=f"cs{i}", **kw)}</g>')
        out.append(f'<text x="{x}" y="640" font-family="MRound" font-weight="800" font-size="32" fill="{ink}" text-anchor="middle">{label}</text>')
    out.append(f'<g transform="translate(1610,470) scale(.9)">{shuwarin(uid="css")}</g>')
    out.append(f'<text x="1610" y="640" font-family="MRound" font-weight="800" font-size="32" fill="{ink}" text-anchor="middle">相棒 シュワリン</text>')
    out.append(f'<line x1="60" y1="700" x2="1740" y2="700" stroke="{ink}" stroke-opacity=".15" stroke-width="3"/>')
    out.append(f'<text x="60" y="760" font-family="MRound" font-weight="800" font-size="34" fill="{ink}">パチっと変身 ─ 食べた味の姿になる</text>')
    for i, (key, f) in enumerate(FLAVORS.items()):
        x = 200 + i * 350
        out.append(f'<g transform="translate({x},930) scale(.4)">{pacchin(f, uid=f"csf{key}", sparks=False)}</g>')
        out.append(f'<text x="{x}" y="1060" font-family="MRound" font-weight="800" font-size="28" fill="{f["badge"]}" text-anchor="middle">{f["name"]}</text>')
    return "".join(out)


def proposal_board() -> str:
    """A 系横長のプレゼンボード（2400×1500）。"""
    g = FLAVORS["grape"]
    ink = INK
    o = [f'<rect width="2400" height="1500" fill="#FFF8EC"/>',
         f'<rect width="2400" height="150" fill="{ink}"/>',
         f'<text x="70" y="100" font-family="Dela" font-size="62" fill="#FFE347">パチっと、おどろけ！</text>',
         f'<text x="720" y="98" font-family="MRound" font-weight="800" font-size="34" fill="#fff">'
         f'パチパチパニック 新キャラクター・ロゴ・パッケージ提案 ／ グレープ味</text>',
         # パッケージ
         f'<g transform="translate(70,210) scale(1.1)">'
         f'<rect x="14" y="18" width="770" height="1100" rx="10" fill="{ink}" opacity=".25"/>{package(g, uid="bd")}</g>',
         f'<text x="493" y="1470" font-family="MRound" font-weight="500" font-size="26" fill="{ink}" text-anchor="middle">'
         f'パッケージ（縦110 × 横77mm）</text>']
    # 中央：キャラクター
    cx = 1310
    o.append(f'<g transform="translate({cx},560) scale(.78)">{pacchin(g, uid="bdc")}</g>')
    o.append(f'<g transform="translate({cx-270},700) scale(.5) rotate(-10)">{shuwarin(uid="bds")}</g>')
    o.append(f'<text x="{cx}" y="830" font-family="Dela" font-size="84" fill="{g["badge"]}" text-anchor="middle">パッチン</text>')
    lines = [
        ("パチパチ星からやってきた、はじけるキャンディの子。", 800),
        ("頭の「はじけクラウン」は、ワクワクするとパチパチ鳴る。", 500),
        ("食べた味の色と姿に “パチっと変身” する。", 500),
        ("相棒はソーダ味のラムネ「シュワリン」。", 500),
        ("目的は、地球の “いつもどおり” をおどろかせること！", 800),
    ]
    for i, (t, w) in enumerate(lines):
        o.append(f'<text x="{cx}" y="{910 + i*46}" font-family="MRound" font-weight="{w}" font-size="27" fill="{ink}" text-anchor="middle">{t}</text>')
    # 右：ロゴとフレーバー展開
    o.append(f'<g transform="translate(2040,380) scale(.62)">{logo(g, uid="bdl")}</g>')
    o.append(f'<text x="1760" y="1020" font-family="MRound" font-weight="800" font-size="30" fill="{ink}">5 フレーバー展開イメージ</text>')
    for i, (key, f) in enumerate(FLAVORS.items()):
        x = 1760 + i * 118
        o.append(f'<g transform="translate({x},1050) scale(.14)"><rect x="10" y="14" width="770" height="1100" fill="{ink}" opacity=".25"/>{package(f, uid="bdf"+key)}</g>')
    o.append(f'<text x="1760" y="1290" font-family="MRound" font-weight="500" font-size="24" fill="{ink}">'
             f'各フレーバー × 6パターン（ポーズ・表情・セリフ違い）</text>')
    o.append(f'<text x="1760" y="1330" font-family="MRound" font-weight="500" font-size="24" fill="{ink}">'
             f'＝ 全30パターン。どれが当たるか集めて楽しい。</text>')
    return "".join(o)


def export_video_parts():
    """動画（video/index.html）用に SVG パーツを JS として書き出す。"""
    import json
    parts = {}
    for key, f in FLAVORS.items():
        parts[f"pacchin_{key}"] = pacchin(f, uid="vc" + key)
    g = FLAVORS["grape"]
    parts["pacchin_happy"] = pacchin(g, eyes="happy", mouth="open", uid="vh")
    parts["pacchin_wide"] = pacchin(g, eyes="wide", mouth="o", uid="vw")
    parts["shuwarin"] = shuwarin(uid="vs")
    parts["logo"] = logo(g, uid="vl")
    parts["package"] = package(g, uid="vp")
    parts["candy"] = candy_pile(g, 0, 0, 1)
    parts["ramune"] = ramune_pile(INK, 0, 0, 1)
    out = ROOT / "video" / "parts.js"
    out.write_text("window.PARTS = " + json.dumps(parts, ensure_ascii=False) + ";\n", encoding="utf-8")
    print("wrote", out.relative_to(ROOT))


if __name__ == "__main__":
    export_video_parts()
    main()
