"""로컬 PPTX 렌더러 — python-pptx로 9개 레이아웃을 직접 그린다.

디자인 언어(발표노트 예시 톤):
  · 밝은 회색 페이지 배경 + '흰 카드(옅은 그림자·둥근 모서리)'
  · 네이비는 헤더 배지·타이틀·번호에만, 포인트는 얇은 컬러 바/골드 언더라인
  · 사진·그래프 자리표는 어두운 블록이 아니라 '점선 테두리의 밝은 카드'
  · 항목형은 '클릭 시 하나씩 등장'(단계적 표현) 지원
"""
from __future__ import annotations

import math

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml import parse_xml
from pptx.oxml.ns import qn
from pptx.util import Emu, Inches, Pt

from ..layouts import spec
from ..schema import ChartSpec, Deck, Layout, Slide
from ..skins.registry import Skin, get as get_skin

# 16:9
EMU_W = Inches(13.333)
EMU_H = Inches(7.5)

_ICONS = {"earth": "🌍", "leaf": "🌿", "sun": "☀️", "water": "💧", "chart": "📈",
          "shield": "🛡️", "check": "✔", "people": "👥", "target": "◎",
          "trophy": "★", "bell": "◆", "clock": "◷", "star": "★", "flag": "▲"}


def _rgb(hex_str: str) -> RGBColor:
    return RGBColor.from_string(hex_str.lstrip("#").upper())


# ── 텍스트 ────────────────────────────────────────────────────
def _set_run_font(run, *, size=None, bold=None, color=None, font=None,
                  highlight=None):
    if size is not None:
        run.font.size = Pt(size)
    if bold is not None:
        run.font.bold = bold
    if color is not None:
        run.font.color.rgb = _rgb(color)
    rPr = run._r.get_or_add_rPr()
    if font is not None:
        run.font.name = font
        for tag in ("a:latin", "a:ea", "a:cs"):
            el = rPr.find(qn(tag))
            if el is None:
                el = rPr.makeelement(qn(tag), {})
                rPr.append(el)
            el.set("typeface", font)
    if highlight is not None:
        for old in rPr.findall(qn("a:highlight")):
            rPr.remove(old)
        hl = parse_xml(
            '<a:highlight xmlns:a="http://schemas.openxmlformats.org/'
            f'drawingml/2006/main"><a:srgbClr val="{highlight.lstrip("#").upper()}"/>'
            "</a:highlight>")
        rPr.append(hl)


def _text(slide, l, t, w, h, text, *, size=18, bold=False, color="#000000",
          align=PP_ALIGN.LEFT, font=None, anchor=MSO_ANCHOR.TOP, wrap=True,
          line_spacing=None, space_after=None):
    box = slide.shapes.add_textbox(l, t, w, h)
    tf = box.text_frame
    tf.word_wrap = wrap
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = Pt(2)
    tf.margin_top = tf.margin_bottom = Pt(2)
    for i, ln in enumerate(str(text).split("\n")):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        if line_spacing:
            p.line_spacing = line_spacing
        if space_after is not None:
            p.space_after = Pt(space_after)
        run = p.add_run()
        run.text = ln
        _set_run_font(run, size=size, bold=bold, color=color, font=font)
    return box


# ── 도형 ──────────────────────────────────────────────────────
def _soft_shadow(sp, *, blur=0.055, dist=0.028, alpha_pct=13, color="1F2A37"):
    """흰 카드에 아주 옅은 부드러운 그림자."""
    spPr = sp._element.spPr
    old = spPr.find(qn("a:effectLst"))
    if old is not None:
        spPr.remove(old)
    xml = (
        '<a:effectLst xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">'
        f'<a:outerShdw blurRad="{int(Inches(blur))}" dist="{int(Inches(dist))}" '
        'dir="5400000" rotWithShape="0">'
        f'<a:srgbClr val="{color}"><a:alpha val="{int(alpha_pct * 1000)}"/></a:srgbClr>'
        "</a:outerShdw></a:effectLst>")
    spPr.append(parse_xml(xml))


def _rect(slide, l, t, w, h, *, fill=None, line=None, line_w=1.0, dash=None,
          shape=MSO_SHAPE.RECTANGLE, radius=None, shadow=False):
    sp = slide.shapes.add_shape(shape, l, t, w, h)
    if fill is None:
        sp.fill.background()
    else:
        sp.fill.solid()
        sp.fill.fore_color.rgb = _rgb(fill)
    if line is None:
        sp.line.fill.background()
    else:
        sp.line.color.rgb = _rgb(line)
        sp.line.width = Pt(line_w)
        if dash:
            ln = sp.line._get_or_add_ln()
            d = ln.find(qn("a:prstDash"))
            if d is None:
                d = ln.makeelement(qn("a:prstDash"), {})
                ln.append(d)
            d.set("val", dash)
    sp.shadow.inherit = False
    if radius is not None and shape == MSO_SHAPE.ROUNDED_RECTANGLE:
        try:
            sp.adjustments[0] = radius
        except Exception:
            pass
    if shadow:
        _soft_shadow(sp)
    return sp


def _card(slide, l, t, w, h, *, fill="#FFFFFF", line="#E7ECF0"):
    return _rect(slide, l, t, w, h, fill=fill, line=line, line_w=0.75,
                 shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.045, shadow=True)


def _shape_text(sp, text, *, size=14, bold=False, color="#000000",
                align=PP_ALIGN.CENTER, font=None, anchor=MSO_ANCHOR.MIDDLE):
    tf = sp.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    _set_run_font(run, size=size, bold=bold, color=color, font=font)
    return sp


def _chip(slide, l, t, text, sk: Skin, *, w=None):
    p = sk.palette
    w = w or Inches(0.2 + 0.09 * len(text))
    c = _rect(slide, l, t, w, Inches(0.32), fill=p.soft,
              shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.5)
    _shape_text(c, text, size=11, bold=True, color=p.soft_ink, font=sk.body_font)
    return w


# ── 단계적 표현: 클릭 시 하나씩 등장 ─────────────────────────────
def _apply_click_reveal(slide, shape_ids: list[int]) -> None:
    if not shape_ids:
        return
    cid = [100]

    def nid():
        cid[0] += 1
        return cid[0]

    blocks = []
    for sid in shape_ids:
        a, b, c, d = nid(), nid(), nid(), nid()
        blocks.append(f"""
          <p:par><p:cTn id="{a}" fill="hold">
            <p:stCondLst><p:cond delay="indefinite"/></p:stCondLst>
            <p:childTnLst>
              <p:par><p:cTn id="{b}" fill="hold">
                <p:stCondLst><p:cond delay="0"/></p:stCondLst>
                <p:childTnLst>
                  <p:par><p:cTn id="{c}" presetClass="entr" presetID="1" fill="hold" grpId="0" nodeType="clickEffect">
                    <p:stCondLst><p:cond delay="0"/></p:stCondLst>
                    <p:childTnLst>
                      <p:set><p:cBhvr>
                        <p:cTn id="{d}" dur="1" fill="hold"><p:stCondLst><p:cond delay="0"/></p:stCondLst></p:cTn>
                        <p:tgtEl><p:spTgt spid="{sid}"/></p:tgtEl>
                        <p:attrNameLst><p:attrName>style.visibility</p:attrName></p:attrNameLst>
                      </p:cBhvr><p:to><p:strVal val="visible"/></p:to></p:set>
                    </p:childTnLst>
                  </p:cTn></p:par>
                </p:childTnLst>
              </p:cTn></p:par>
            </p:childTnLst>
          </p:cTn></p:par>""")

    xml = f"""<p:timing xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
        xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
      <p:tnLst><p:par><p:cTn id="1" dur="indefinite" restart="never" nodeType="tmRoot">
        <p:childTnLst>
          <p:seq concurrent="1" nextAc="seek">
            <p:cTn id="2" dur="indefinite" nodeType="mainSeq"><p:childTnLst>
              {''.join(blocks)}
            </p:childTnLst></p:cTn>
            <p:prevCondLst><p:cond evt="onPrev" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:prevCondLst>
            <p:nextCondLst><p:cond evt="onNext" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:nextCondLst>
          </p:seq>
        </p:childTnLst>
      </p:cTn></p:par></p:tnLst>
    </p:timing>"""
    slide._element.append(parse_xml(xml))


# ── 공통 헤더 ─────────────────────────────────────────────────
def _bg(slide, sk: Skin):
    _rect(slide, 0, 0, EMU_W, EMU_H, fill=sk.palette.bg)


def _eyebrow(slide, sk: Skin, num_text: str, title: str, *, kicker: str = ""):
    """상단: 네이비 번호 배지 + 제목 + 골드 언더라인."""
    p = sk.palette
    y = Inches(0.5)
    badge = _rect(slide, Inches(0.62), y, Inches(0.5), Inches(0.5),
                  fill=p.primary, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.22)
    _shape_text(badge, num_text, size=17, bold=True, color=p.on_primary,
                font=sk.heading_font)
    tx = Inches(1.28)
    if kicker:
        _text(slide, tx, Inches(0.42), Inches(11), Inches(0.3), kicker,
              size=11, bold=True, color=p.secondary, font=sk.heading_font)
        _text(slide, tx, Inches(0.68), Inches(11), Inches(0.55), title,
              size=23, bold=True, color=p.primary, font=sk.heading_font,
              anchor=MSO_ANCHOR.MIDDLE)
    else:
        _text(slide, tx, y, Inches(11.4), Inches(0.5), title,
              size=24, bold=True, color=p.primary, font=sk.heading_font,
              anchor=MSO_ANCHOR.MIDDLE)
    _rect(slide, Inches(0.64), Inches(1.16), Inches(0.62), Inches(0.055),
          fill=p.accent)


def _usage_bar(slide, sk: Skin, usage: str):
    if not usage:
        return
    p = sk.palette
    _rect(slide, Inches(0.62), Inches(6.92), Inches(0.16), Inches(0.34), fill=p.accent)
    _text(slide, Inches(0.92), Inches(6.9), Inches(1.4), Inches(0.4), "활용 상황",
          size=10.5, bold=True, color=p.secondary, font=sk.heading_font,
          anchor=MSO_ANCHOR.MIDDLE)
    _text(slide, Inches(2.05), Inches(6.9), Inches(10.6), Inches(0.4), usage,
          size=10.5, color=p.muted, font=sk.body_font, anchor=MSO_ANCHOR.MIDDLE)


def _placeholder(slide, sk: Skin, l, t, w, h, label):
    """점선 테두리의 밝은 사진/그래프 자리표."""
    p = sk.palette
    box = _rect(slide, l, t, w, h, fill="#FBFCFD", line="#C7D4DD", line_w=1.25,
                dash="dash", shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.03)
    _shape_text(box, label, size=13, bold=False, color=p.muted, font=sk.body_font)
    return box


# ── 레이아웃 ──────────────────────────────────────────────────
def draw_cover(slide, sk: Skin, s: Slide, deck: Deck):
    p = sk.palette
    _bg(slide, sk)
    # 좌측 얇은 네이비 강조 기둥
    _rect(slide, 0, 0, Inches(0.28), EMU_H, fill=p.primary)
    _rect(slide, Inches(0.28), 0, Inches(0.06), EMU_H, fill=p.accent)
    _text(slide, Inches(1.0), Inches(1.15), Inches(11), Inches(0.4),
          (deck.author or "CHANGCHENET").upper(), size=12.5, bold=True,
          color=p.secondary, font=sk.heading_font)
    _text(slide, Inches(0.98), Inches(2.35), Inches(11.4), Inches(2.2), s.title,
          size=46, bold=True, color=p.primary, font=sk.heading_font,
          line_spacing=1.06)
    _rect(slide, Inches(1.02), Inches(4.55), Inches(1.5), Inches(0.07), fill=p.accent)
    if s.subtitle:
        _text(slide, Inches(1.02), Inches(4.85), Inches(11.2), Inches(0.7),
              s.subtitle, size=19, color=p.secondary, font=sk.body_font)
    # 메타 pill
    x = Inches(1.02)
    for m in [x for x in [deck.author, deck.date] if x]:
        w = _chip(slide, x, Inches(6.35), m, sk)
        x += w + Inches(0.15)


def draw_toc(slide, sk: Skin, s: Slide, deck: Deck):
    p = sk.palette
    _bg(slide, sk)
    _eyebrow(slide, sk, "•", s.title or "목차")
    items = s.items[:6]
    cols = 3
    cw, ch = Inches(3.78), Inches(1.95)
    gx, gy = Inches(0.24), Inches(0.3)
    x0, y0 = Inches(0.64), Inches(1.65)
    for i, it in enumerate(items):
        r, c = divmod(i, cols)
        x = x0 + c * (cw + gx)
        y = y0 + r * (ch + gy)
        _card(slide, x, y, cw, ch)
        num = _rect(slide, x + Inches(0.28), y + Inches(0.28), Inches(0.52),
                    Inches(0.52), fill=p.soft, shape=MSO_SHAPE.OVAL)
        _shape_text(num, str(i + 1), size=17, bold=True, color=p.primary,
                    font=sk.heading_font)
        _text(slide, x + Inches(0.98), y + Inches(0.26), cw - Inches(1.2),
              Inches(0.6), it.heading, size=15, bold=True, color=p.ink,
              font=sk.heading_font, anchor=MSO_ANCHOR.MIDDLE)
        if it.body:
            _text(slide, x + Inches(0.3), y + Inches(0.98), cw - Inches(0.6),
                  Inches(0.85), it.body, size=11, color=p.muted,
                  font=sk.body_font, line_spacing=1.25)


def draw_photo(slide, sk: Skin, s: Slide, deck: Deck):
    p = sk.palette
    _bg(slide, sk)
    _eyebrow(slide, sk, "1", s.title or "사진 중심형")
    _placeholder(slide, sk, Inches(3.4), Inches(1.6), Inches(6.5), Inches(3.65),
                 "📷  고화질 이미지 삽입 영역")
    if s.body:
        _text(slide, Inches(2.2), Inches(5.5), Inches(8.9), Inches(1.1), s.body,
              size=14.5, color=p.ink, font=sk.body_font, align=PP_ALIGN.CENTER,
              line_spacing=1.35)
    _usage_bar(slide, sk, s.usage or spec(Layout.PHOTO_FOCUS).usage)


def draw_split(slide, sk: Skin, s: Slide, deck: Deck):
    p = sk.palette
    _bg(slide, sk)
    _eyebrow(slide, sk, "2", s.title or "좌우 분할형")
    _placeholder(slide, sk, Inches(0.64), Inches(1.6), Inches(5.5), Inches(4.55),
                 "📷  사진 영역")
    rx = Inches(6.5)
    if s.subtitle:
        _rect(slide, rx, Inches(1.72), Inches(0.14), Inches(0.62), fill=p.accent)
        _text(slide, rx + Inches(0.28), Inches(1.66), Inches(6.0), Inches(0.8),
              s.subtitle, size=21, bold=True, color=p.primary, font=sk.heading_font,
              anchor=MSO_ANCHOR.MIDDLE)
    _text(slide, rx, Inches(2.7), Inches(6.2), Inches(3.4),
          s.body or "설명 문장을 작성해주세요.", size=14.5, color=p.ink,
          font=sk.body_font, line_spacing=1.5)
    _usage_bar(slide, sk, s.usage or spec(Layout.SPLIT).usage)


def _feature_cards(slide, sk: Skin, items, *, y, cw, ch, cols, with_icon):
    """흰 카드: (아이콘 원) + 제목(네이비) + 본문(회색)."""
    p = sk.palette
    n = min(len(items), cols)
    total = n * cw + (n - 1) * Inches(0.28)
    x0 = (EMU_W - total) // 2
    ids = []
    for i in range(n):
        it = items[i]
        x = x0 + i * (cw + Inches(0.28))
        card = _card(slide, x, y, cw, ch)
        ids.append(card.shape_id)
        _rect(slide, x, y, cw, Inches(0.1), fill=p.accent,
              shape=MSO_SHAPE.ROUND_2_SAME_RECTANGLE, radius=0.5)
        iy = y + Inches(0.34)
        if with_icon:
            circ = _rect(slide, x + (cw - Inches(0.78)) // 2, iy, Inches(0.78),
                         Inches(0.78), fill=p.soft, shape=MSO_SHAPE.OVAL)
            _shape_text(circ, _ICONS.get(it.icon, "●"), size=26, color=p.primary,
                        font=sk.body_font)
            hy = iy + Inches(1.0)
        else:
            hy = iy + Inches(0.1)
        _text(slide, x + Inches(0.2), hy, cw - Inches(0.4), Inches(0.5),
              it.heading, size=15.5, bold=True, color=p.primary,
              font=sk.heading_font, align=PP_ALIGN.CENTER,
              anchor=MSO_ANCHOR.MIDDLE)
        if it.body:
            _text(slide, x + Inches(0.24), hy + Inches(0.5), cw - Inches(0.48),
                  ch - (hy - y) - Inches(0.6), it.body, size=11.5, color=p.muted,
                  font=sk.body_font, align=PP_ALIGN.CENTER, line_spacing=1.3)
    return ids


def draw_icons(slide, sk: Skin, s: Slide, deck: Deck):
    _bg(slide, sk)
    _eyebrow(slide, sk, "3", s.title or "아이콘 분할형")
    n = min(len(s.items), 4) or 3
    ids = _feature_cards(slide, sk, s.items, y=Inches(1.75),
                         cw=Inches(2.9) if n >= 4 else Inches(3.6),
                         ch=Inches(3.55), cols=4, with_icon=True)
    _usage_bar(slide, sk, s.usage or spec(Layout.ICON_TRIPLE).usage)
    if s.reveal:
        _apply_click_reveal(slide, ids)


def draw_cards(slide, sk: Skin, s: Slide, deck: Deck):
    p = sk.palette
    _bg(slide, sk)
    _eyebrow(slide, sk, "6", s.title or "카드 / 그리드형")
    items = s.items[:6]
    ids = []
    if len(items) <= 3:
        ids = _feature_cards(slide, sk, items, y=Inches(2.0), cw=Inches(3.7),
                             ch=Inches(3.0), cols=3, with_icon=True)
    else:
        cols = 3
        rows = math.ceil(len(items) / cols)
        cw, ch = Inches(3.78), Inches(1.9)
        total_w = cols * cw + (cols - 1) * Inches(0.24)
        x0 = (EMU_W - total_w) // 2
        y0 = Inches(1.7)
        for i, it in enumerate(items):
            r, c = divmod(i, cols)
            x = x0 + c * (cw + Inches(0.24))
            y = y0 + r * (ch + Inches(0.26))
            card = _card(slide, x, y, cw, ch)
            ids.append(card.shape_id)
            _rect(slide, x + Inches(0.24), y + Inches(0.26), Inches(0.14),
                  Inches(ch.inches - 0.52) if hasattr(ch, "inches") else Inches(1.4),
                  fill=p.accent)
            _text(slide, x + Inches(0.56), y + Inches(0.22), cw - Inches(0.8),
                  Inches(0.5), it.heading, size=14.5, bold=True, color=p.primary,
                  font=sk.heading_font, anchor=MSO_ANCHOR.MIDDLE)
            if it.body:
                _text(slide, x + Inches(0.56), y + Inches(0.78), cw - Inches(0.82),
                      ch - Inches(0.95), it.body, size=11.5, color=p.muted,
                      font=sk.body_font, line_spacing=1.28)
    _usage_bar(slide, sk, s.usage or spec(Layout.CARD_GRID).usage)
    if s.reveal:
        _apply_click_reveal(slide, ids)


def draw_timeline(slide, sk: Skin, s: Slide, deck: Deck):
    p = sk.palette
    _bg(slide, sk)
    _eyebrow(slide, sk, "4", s.title or "타임라인 / 단계형")
    items = s.items[:5]
    n = len(items) or 1
    cw = Inches(2.34)
    gap = Inches(0.2)
    total = n * cw + (n - 1) * gap
    x0 = (EMU_W - total) // 2
    y = Inches(2.15)
    # 연결선
    _rect(slide, x0 + Inches(0.35), y + Inches(0.34), total - Inches(0.7),
          Inches(0.04), fill=p.card_line)
    ids = []
    for i, it in enumerate(items):
        x = x0 + i * (cw + gap)
        circ = _rect(slide, x + (cw - Inches(0.72)) // 2, y, Inches(0.72),
                     Inches(0.72), fill=p.primary, shape=MSO_SHAPE.OVAL)
        _shape_text(circ, str(i + 1), size=20, bold=True, color=p.on_primary,
                    font=sk.heading_font)
        ids.append(circ.shape_id)
        card = _card(slide, x, y + Inches(1.05), cw, Inches(2.7))
        if it.step_label:
            _text(slide, x + Inches(0.2), y + Inches(1.25), cw - Inches(0.4),
                  Inches(0.3), it.step_label, size=10.5, bold=True,
                  color=p.accent_ink if hasattr(p, "accent_ink") else p.secondary,
                  font=sk.heading_font, align=PP_ALIGN.CENTER)
        _text(slide, x + Inches(0.2), y + Inches(1.58), cw - Inches(0.4),
              Inches(0.55), it.heading, size=14, bold=True, color=p.primary,
              font=sk.heading_font, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        if it.body:
            _text(slide, x + Inches(0.24), y + Inches(2.18), cw - Inches(0.48),
                  Inches(1.35), it.body, size=11, color=p.muted, font=sk.body_font,
                  align=PP_ALIGN.CENTER, line_spacing=1.28)
    _usage_bar(slide, sk, s.usage or spec(Layout.TIMELINE).usage)
    if s.reveal:
        _apply_click_reveal(slide, ids)


def draw_chart(slide, sk: Skin, s: Slide, deck: Deck):
    p = sk.palette
    _bg(slide, sk)
    _eyebrow(slide, sk, "5", s.title or "그래프 / 비주얼 중심형")
    card = _card(slide, Inches(0.64), Inches(1.6), Inches(6.7), Inches(4.55))
    if s.chart and s.chart.series:
        _add_chart(slide, sk, s.chart, Inches(0.9), Inches(1.85), Inches(6.2),
                   Inches(4.05))
    else:
        _placeholder(slide, sk, Inches(0.9), Inches(1.85), Inches(6.2),
                     Inches(4.05), "📊  그래프 영역")
    rx = Inches(7.7)
    if s.subtitle:
        _rect(slide, rx, Inches(1.82), Inches(0.14), Inches(0.6), fill=p.accent)
        _text(slide, rx + Inches(0.28), Inches(1.76), Inches(4.9), Inches(0.75),
              s.subtitle, size=18, bold=True, color=p.primary, font=sk.heading_font,
              anchor=MSO_ANCHOR.MIDDLE)
    _text(slide, rx, Inches(2.75), Inches(5.0), Inches(3.3),
          s.body or "그래프를 설명하는 문장을 작성해주세요.", size=13.5,
          color=p.ink, font=sk.body_font, line_spacing=1.5)
    _usage_bar(slide, sk, s.usage or spec(Layout.CHART_FOCUS).usage)


def _add_chart(slide, sk: Skin, cs: ChartSpec, l, t, w, h):
    from pptx.chart.data import CategoryChartData
    from pptx.enum.chart import XL_CHART_TYPE
    kind_map = {"bar": XL_CHART_TYPE.COLUMN_CLUSTERED,
                "line": XL_CHART_TYPE.LINE_MARKERS,
                "pie": XL_CHART_TYPE.PIE, "radar": XL_CHART_TYPE.RADAR}
    ctype = kind_map.get(cs.kind, XL_CHART_TYPE.COLUMN_CLUSTERED)
    data = CategoryChartData()
    data.categories = cs.categories or [
        str(i + 1) for i in range(len(next(iter(cs.series.values()))))]
    for name, vals in cs.series.items():
        data.add_series(name, vals)
    gf = slide.shapes.add_chart(ctype, l, t, w, h, data)
    chart = gf.chart
    chart.has_title = False
    try:
        chart.has_legend = len(cs.series) > 1
    except Exception:
        pass
    # 시리즈 색을 스킨 primary/accent로
    try:
        colors = [sk.palette.primary, sk.palette.accent, sk.palette.secondary]
        for i, plot in enumerate(chart.plots):
            for j, ser in enumerate(plot.series):
                ser.format.fill.solid()
                ser.format.fill.fore_color.rgb = _rgb(colors[j % len(colors)])
    except Exception:
        pass


def draw_closing(slide, sk: Skin, s: Slide, deck: Deck):
    p = sk.palette
    _bg(slide, sk)
    _rect(slide, 0, Inches(2.35), Inches(0.28), Inches(2.8), fill=p.primary)
    _text(slide, 0, Inches(2.55), EMU_W, Inches(1.2), s.title or "감사합니다",
          size=44, bold=True, color=p.primary, font=sk.heading_font,
          align=PP_ALIGN.CENTER)
    _rect(slide, (EMU_W - Inches(1.6)) // 2, Inches(3.8), Inches(1.6),
          Inches(0.07), fill=p.accent)
    if s.subtitle:
        _text(slide, 0, Inches(4.1), EMU_W, Inches(0.7), s.subtitle, size=16,
              color=p.secondary, font=sk.body_font, align=PP_ALIGN.CENTER)
    meta = "   ·   ".join(x for x in [deck.author, deck.date] if x)
    if meta:
        _text(slide, 0, Inches(5.0), EMU_W, Inches(0.5), meta, size=12.5,
              color=p.muted, font=sk.body_font, align=PP_ALIGN.CENTER)


_DISPATCH = {
    Layout.COVER: draw_cover,
    Layout.TOC: draw_toc,
    Layout.PHOTO_FOCUS: draw_photo,
    Layout.SPLIT: draw_split,
    Layout.ICON_TRIPLE: draw_icons,
    Layout.TIMELINE: draw_timeline,
    Layout.CHART_FOCUS: draw_chart,
    Layout.CARD_GRID: draw_cards,
    Layout.CLOSING: draw_closing,
}


def build(deck: Deck, out_path: str, *, skin: str | None = None) -> str:
    sk = get_skin(skin or deck.skin)
    prs = Presentation()
    prs.slide_width = EMU_W
    prs.slide_height = EMU_H
    blank = prs.slide_layouts[6]
    for s in deck.slides:
        slide = prs.slides.add_slide(blank)
        _DISPATCH.get(s.layout, draw_split)(slide, sk, s, deck)
        notes = slide.notes_slide
        parts = []
        if s.note.summary:
            parts.append(f"[핵심 요약] {s.note.summary}")
        if s.note.must_know:
            parts.append("[꼭 알아야 할 것]\n" + "\n".join(f"- {x}" for x in s.note.must_know))
        if s.note.script:
            parts.append(f"[발표 스크립트]\n{s.note.script}")
        notes.notes_text_frame.text = "\n\n".join(parts)
    prs.save(out_path)
    return out_path
