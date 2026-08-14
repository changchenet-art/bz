"""로컬 PPTX 렌더러 — python-pptx로 9개 레이아웃을 직접 그린다.

- 스킨(색·폰트)에 따라 옷을 바꿔 입힌다.
- 각 슬라이드에 발표자 노트를 넣는다.
- 항목형 레이아웃은 '클릭 시 하나씩 등장'(단계적 표현)을 지원한다.
- 한글은 latin/ea 글꼴을 함께 지정해 안전하게 표시한다.
"""
from __future__ import annotations

from copy import deepcopy

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Inches, Pt

from ..layouts import spec
from ..schema import ChartSpec, Deck, Layout, Slide
from ..skins.registry import Skin, get as get_skin

# 16:9
EMU_W = Inches(13.333)
EMU_H = Inches(7.5)


def _rgb(hex_str: str) -> RGBColor:
    return RGBColor.from_string(hex_str.lstrip("#").upper())


def _set_run_font(run, *, size=None, bold=None, color=None, font=None):
    if size is not None:
        run.font.size = Pt(size)
    if bold is not None:
        run.font.bold = bold
    if color is not None:
        run.font.color.rgb = _rgb(color)
    if font is not None:
        run.font.name = font
        rPr = run._r.get_or_add_rPr()
        for tag in ("a:latin", "a:ea", "a:cs"):
            el = rPr.find(qn(tag))
            if el is None:
                el = rPr.makeelement(qn(tag), {})
                rPr.append(el)
            el.set("typeface", font)


def _text(slide, l, t, w, h, text, *, size=18, bold=False, color="#000000",
          align=PP_ALIGN.LEFT, font=None, anchor=MSO_ANCHOR.TOP, wrap=True,
          line_spacing=None):
    box = slide.shapes.add_textbox(l, t, w, h)
    tf = box.text_frame
    tf.word_wrap = wrap
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = Pt(2)
    tf.margin_top = tf.margin_bottom = Pt(2)
    lines = str(text).split("\n")
    for i, ln in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        if line_spacing:
            p.line_spacing = line_spacing
        run = p.add_run()
        run.text = ln
        _set_run_font(run, size=size, bold=bold, color=color, font=font)
    return box


def _rect(slide, l, t, w, h, *, fill=None, line=None, line_w=1.0,
          shape=MSO_SHAPE.RECTANGLE):
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
    sp.shadow.inherit = False
    return sp


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


# ── 단계적 표현: 클릭 시 하나씩 등장 ─────────────────────────────
def _apply_click_reveal(slide, shape_ids: list[int]) -> None:
    """지정한 도형들을 클릭할 때마다 하나씩 나타나게 하는 timing XML 주입."""
    if not shape_ids:
        return
    cid = [100]

    def nid():
        cid[0] += 1
        return cid[0]

    click_blocks = []
    for sid in shape_ids:
        a, b, c, d = nid(), nid(), nid(), nid()
        click_blocks.append(f"""
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
              {''.join(click_blocks)}
            </p:childTnLst></p:cTn>
            <p:prevCondLst><p:cond evt="onPrev" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:prevCondLst>
            <p:nextCondLst><p:cond evt="onNext" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:nextCondLst>
          </p:seq>
        </p:childTnLst>
      </p:cTn></p:par></p:tnLst>
    </p:timing>"""
    from pptx.oxml import parse_xml
    slide._element.append(parse_xml(xml))


# ── 레이아웃 그리기 ───────────────────────────────────────────
def _bg(slide, sk: Skin):
    _rect(slide, 0, 0, EMU_W, EMU_H, fill=sk.palette.bg)


def _eyebrow(slide, sk: Skin, num_text: str, title: str):
    """상단 좌측 번호칩 + 제목."""
    p = sk.palette
    chip = _rect(slide, Inches(0.6), Inches(0.45), Inches(0.42), Inches(0.42),
                 fill=p.accent, shape=MSO_SHAPE.OVAL)
    _shape_text(chip, num_text, size=13, bold=True, color=p.on_primary, font=sk.heading_font)
    _text(slide, Inches(1.15), Inches(0.4), Inches(11), Inches(0.6), title,
          size=26, bold=True, color=p.primary, font=sk.heading_font,
          anchor=MSO_ANCHOR.MIDDLE)
    _rect(slide, Inches(1.18), Inches(1.02), Inches(2.2), Inches(0.05), fill=p.accent)


def _usage_bar(slide, sk: Skin, usage: str):
    if not usage:
        return
    p = sk.palette
    _rect(slide, Inches(0.6), Inches(6.75), Inches(1.5), Inches(0.42),
          fill=p.secondary, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
    _text(slide, Inches(0.7), Inches(6.75), Inches(1.4), Inches(0.42), "활용 상황",
          size=11, bold=True, color=p.on_primary, font=sk.heading_font,
          align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    _text(slide, Inches(2.2), Inches(6.75), Inches(10.4), Inches(0.42), usage,
          size=11, color=p.muted, font=sk.body_font, anchor=MSO_ANCHOR.MIDDLE)


def draw_cover(slide, sk: Skin, s: Slide, deck: Deck):
    p = sk.palette
    _bg(slide, sk)
    _rect(slide, 0, Inches(2.55), EMU_W, Inches(0.06), fill=p.accent)
    _text(slide, Inches(1.0), Inches(0.7), Inches(11.3), Inches(0.5),
          "CHANGCHENET", size=12, bold=True, color=p.secondary, font=sk.heading_font)
    _text(slide, Inches(1.0), Inches(2.7), Inches(11.3), Inches(2.0), s.title,
          size=48, bold=True, color=p.primary, font=sk.heading_font,
          line_spacing=1.05)
    if s.subtitle:
        _text(slide, Inches(1.02), Inches(4.7), Inches(11.3), Inches(0.7), s.subtitle,
              size=20, color=p.secondary, font=sk.body_font)
    meta = "  ·  ".join(x for x in [deck.author, deck.date] if x)
    if meta:
        _text(slide, Inches(1.02), Inches(6.6), Inches(11.3), Inches(0.5), meta,
              size=13, color=p.muted, font=sk.body_font)


def draw_toc(slide, sk: Skin, s: Slide, deck: Deck):
    p = sk.palette
    _bg(slide, sk)
    _text(slide, Inches(0.9), Inches(0.55), Inches(11), Inches(0.8), s.title or "목차",
          size=32, bold=True, color=p.primary, font=sk.heading_font)
    items = s.items[:6]
    cols, rows = 3, 2
    cw, ch = Inches(3.7), Inches(1.9)
    x0, y0 = Inches(0.9), Inches(1.9)
    gx, gy = Inches(0.15), Inches(0.35)
    reveal_ids = []
    for i, it in enumerate(items):
        r, c = divmod(i, cols)
        x = x0 + c * (cw + gx)
        y = y0 + r * (ch + gy)
        num = _rect(slide, x, y, Inches(0.5), Inches(0.5), fill=p.card,
                    shape=MSO_SHAPE.OVAL)
        _shape_text(num, str(i + 1), size=14, bold=True, color=p.on_primary,
                    font=sk.heading_font)
        _text(slide, x + Inches(0.65), y, cw - Inches(0.65), Inches(0.9),
              it.heading, size=15, bold=True, color=p.ink, font=sk.heading_font,
              anchor=MSO_ANCHOR.MIDDLE)
        if it.body:
            _text(slide, x, y + Inches(0.6), cw, Inches(1.2), it.body,
                  size=11, color=p.muted, font=sk.body_font)


def draw_photo(slide, sk: Skin, s: Slide, deck: Deck):
    p = sk.palette
    _bg(slide, sk)
    _eyebrow(slide, sk, "1", s.title or "사진 중심형")
    # 대형 사진 자리표(가운데)
    box = _rect(slide, Inches(3.9), Inches(1.5), Inches(5.5), Inches(3.6),
                fill=p.card)
    _shape_text(box, "📷  사진 영역\n(고화질 이미지 삽입)", size=14,
                color=p.on_primary, font=sk.body_font)
    if s.body:
        _text(slide, Inches(2.5), Inches(5.3), Inches(8.3), Inches(1.2), s.body,
              size=14, color=p.ink, font=sk.body_font, align=PP_ALIGN.CENTER,
              line_spacing=1.3)
    _usage_bar(slide, sk, s.usage or spec(Layout.PHOTO_FOCUS).usage)


def draw_split(slide, sk: Skin, s: Slide, deck: Deck):
    p = sk.palette
    _bg(slide, sk)
    _eyebrow(slide, sk, "2", s.title or "좌우 분할형")
    # 좌: 사진 자리표
    box = _rect(slide, Inches(0.9), Inches(1.6), Inches(5.0), Inches(4.4),
                fill=p.card)
    _shape_text(box, "📷  사진 영역", size=14, color=p.on_primary, font=sk.body_font)
    # 우: 부제 + 설명
    if s.subtitle:
        _text(slide, Inches(6.3), Inches(1.7), Inches(6.2), Inches(0.7), s.subtitle,
              size=20, bold=True, color=p.secondary, font=sk.heading_font)
    _text(slide, Inches(6.3), Inches(2.5), Inches(6.2), Inches(3.6),
          s.body or "설명 문장을 작성해주세요.", size=14, color=p.ink,
          font=sk.body_font, line_spacing=1.4)
    _usage_bar(slide, sk, s.usage or spec(Layout.SPLIT).usage)


def _cards(slide, sk: Skin, items, *, y, cw, ch, cols, with_icon):
    p = sk.palette
    n = min(len(items), cols)
    total = n * cw + (n - 1) * Inches(0.3)
    x0 = (EMU_W - total) // 2
    reveal_ids = []
    for i in range(n):
        it = items[i]
        x = x0 + i * (cw + Inches(0.3))
        card = _rect(slide, x, y, cw, ch, fill=p.card,
                     shape=MSO_SHAPE.ROUNDED_RECTANGLE)
        reveal_ids.append(card.shape_id)
        tf = card.text_frame
        tf.word_wrap = True
        tf.vertical_anchor = MSO_ANCHOR.TOP
        tf.margin_left = tf.margin_right = Pt(10)
        tf.margin_top = Pt(12)
        p0 = tf.paragraphs[0]
        p0.alignment = PP_ALIGN.CENTER
        if with_icon:
            r = p0.add_run(); r.text = {"earth": "🌍", "leaf": "🌿", "sun": "☀️",
                "water": "💧", "chart": "📈", "shield": "🛡️", "check": "✔️",
                "people": "👥", "target": "🎯", "trophy": "🏆", "bell": "🔔",
                "clock": "⏰"}.get(it.icon, "●")
            _set_run_font(r, size=24, color=p.on_primary, font=sk.body_font)
            p0 = tf.add_paragraph(); p0.alignment = PP_ALIGN.CENTER
        r = p0.add_run(); r.text = it.heading
        _set_run_font(r, size=15, bold=True, color=p.on_primary, font=sk.heading_font)
        if it.body:
            pb = tf.add_paragraph(); pb.alignment = PP_ALIGN.CENTER
            rb = pb.add_run(); rb.text = it.body
            _set_run_font(rb, size=11, color=p.on_primary, font=sk.body_font)
    return reveal_ids


def draw_icons(slide, sk: Skin, s: Slide, deck: Deck):
    _bg(slide, sk)
    _eyebrow(slide, sk, "3", s.title or "아이콘 3분할형")
    ids = _cards(slide, sk, s.items, y=Inches(2.1), cw=Inches(3.5),
                 ch=Inches(3.2), cols=4, with_icon=True)
    _usage_bar(slide, sk, s.usage or spec(Layout.ICON_TRIPLE).usage)
    if s.reveal:
        _apply_click_reveal(slide, ids)


def draw_cards(slide, sk: Skin, s: Slide, deck: Deck):
    _bg(slide, sk)
    _eyebrow(slide, sk, "6", s.title or "카드/그리드형")
    items = s.items[:6]
    if len(items) <= 3:
        ids = _cards(slide, sk, items, y=Inches(2.3), cw=Inches(3.7),
                     ch=Inches(2.8), cols=3, with_icon=True)
    else:
        # 4~6개: 2행
        p = sk.palette
        ids = []
        cols = 3 if len(items) > 4 else 2
        import math
        rows = math.ceil(len(items) / cols)
        cw, ch = Inches(3.7), Inches(1.9)
        total_w = cols * cw + (cols - 1) * Inches(0.3)
        x0 = (EMU_W - total_w) // 2
        y0 = Inches(2.0)
        for i, it in enumerate(items):
            r, c = divmod(i, cols)
            x = x0 + c * (cw + Inches(0.3))
            y = y0 + r * (ch + Inches(0.3))
            card = _rect(slide, x, y, cw, ch, fill=p.card,
                         shape=MSO_SHAPE.ROUNDED_RECTANGLE)
            ids.append(card.shape_id)
            _shape_text(card, f"{it.heading}\n{it.body}", size=12, bold=False,
                        color=p.on_primary, font=sk.body_font,
                        anchor=MSO_ANCHOR.MIDDLE)
    _usage_bar(slide, sk, s.usage or spec(Layout.CARD_GRID).usage)
    if s.reveal:
        _apply_click_reveal(slide, ids)


def draw_timeline(slide, sk: Skin, s: Slide, deck: Deck):
    p = sk.palette
    _bg(slide, sk)
    _eyebrow(slide, sk, "4", s.title or "타임라인 / 단계형")
    items = s.items[:5]
    n = len(items) or 1
    cw = Inches(2.5)
    gap = Inches(0.35)
    total = n * cw + (n - 1) * gap
    x0 = (EMU_W - total) // 2
    y = Inches(2.4)
    ids = []
    for i, it in enumerate(items):
        x = x0 + i * (cw + gap)
        chev = _rect(slide, x, y, cw, Inches(0.9), fill=p.card,
                     shape=MSO_SHAPE.CHEVRON)
        _shape_text(chev, it.step_label or f"Step {i+1}", size=14, bold=True,
                    color=p.on_primary, font=sk.heading_font)
        ids.append(chev.shape_id)
        _text(slide, x, y + Inches(1.1), cw, Inches(0.5), it.heading,
              size=13, bold=True, color=p.secondary, font=sk.heading_font,
              align=PP_ALIGN.CENTER)
        if it.body:
            _text(slide, x, y + Inches(1.6), cw, Inches(1.4), it.body,
                  size=11, color=p.ink, font=sk.body_font, align=PP_ALIGN.CENTER)
    _usage_bar(slide, sk, s.usage or spec(Layout.TIMELINE).usage)
    if s.reveal:
        _apply_click_reveal(slide, ids)


def draw_chart(slide, sk: Skin, s: Slide, deck: Deck):
    p = sk.palette
    _bg(slide, sk)
    _eyebrow(slide, sk, "5", s.title or "그래프/비주얼 중심형")
    # 좌: 차트
    if s.chart and s.chart.series:
        _add_chart(slide, sk, s.chart, Inches(0.9), Inches(1.6),
                   Inches(6.4), Inches(4.4))
    else:
        box = _rect(slide, Inches(0.9), Inches(1.6), Inches(6.4), Inches(4.4),
                    fill=p.card)
        _shape_text(box, "📊  그래프 영역", size=14, color=p.on_primary,
                    font=sk.body_font)
    # 우: 설명
    if s.subtitle:
        _text(slide, Inches(7.7), Inches(1.9), Inches(4.9), Inches(0.7), s.subtitle,
              size=18, bold=True, color=p.secondary, font=sk.heading_font)
    _text(slide, Inches(7.7), Inches(2.7), Inches(4.9), Inches(3.2),
          s.body or "그래프를 설명하는 문장을 작성해주세요.", size=14,
          color=p.ink, font=sk.body_font, line_spacing=1.4)
    _usage_bar(slide, sk, s.usage or spec(Layout.CHART_FOCUS).usage)


def _add_chart(slide, sk: Skin, cs: ChartSpec, l, t, w, h):
    from pptx.chart.data import CategoryChartData
    from pptx.enum.chart import XL_CHART_TYPE
    kind_map = {
        "bar": XL_CHART_TYPE.COLUMN_CLUSTERED,
        "line": XL_CHART_TYPE.LINE_MARKERS,
        "pie": XL_CHART_TYPE.PIE,
        "radar": XL_CHART_TYPE.RADAR,
    }
    ctype = kind_map.get(cs.kind, XL_CHART_TYPE.COLUMN_CLUSTERED)
    data = CategoryChartData()
    data.categories = cs.categories or [str(i + 1) for i in
                                        range(len(next(iter(cs.series.values()))))]
    for name, vals in cs.series.items():
        data.add_series(name, vals)
    gf = slide.shapes.add_chart(ctype, l, t, w, h, data)
    chart = gf.chart
    chart.has_title = False
    try:
        chart.legend.position  # noqa
        chart.has_legend = len(cs.series) > 1
    except Exception:
        pass


def draw_closing(slide, sk: Skin, s: Slide, deck: Deck):
    p = sk.palette
    _bg(slide, sk)
    _text(slide, 0, Inches(2.6), EMU_W, Inches(1.2), s.title or "감사합니다",
          size=44, bold=True, color=p.primary, font=sk.heading_font,
          align=PP_ALIGN.CENTER)
    if s.subtitle:
        _text(slide, 0, Inches(4.0), EMU_W, Inches(0.7), s.subtitle,
              size=16, color=p.secondary, font=sk.body_font, align=PP_ALIGN.CENTER)
    _rect(slide, (EMU_W - Inches(2.0)) // 2, Inches(3.75), Inches(2.0),
          Inches(0.05), fill=p.accent)


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
        # 발표자 노트
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
