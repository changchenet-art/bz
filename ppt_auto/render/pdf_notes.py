"""슬라이드 노트 → PDF 설명자료.

각 페이지 구성(사용자 요청 형식):
    [ 슬라이드 미리보기 그림 (PPT 화면) ]
    ■ 핵심 요약
    ■ 꼭 알아야 할 것
    ■ 발표 스크립트

슬라이드 미리보기는 스킨 색으로 16:9 축소 화면을 그려 넣는다.
reportlab 내장 한글 CID 폰트를 써서 별도 TTF 없이 한글 출력.
"""
from __future__ import annotations

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import (
    Flowable, HRFlowable, ListFlowable, ListItem, PageBreak, Paragraph,
    SimpleDocTemplate, Spacer,
)

from ..layouts import spec
from ..schema import Deck, Layout, Slide
from ..skins.registry import Skin, get as get_skin

_SERIF = "HYSMyeongJo-Medium"
_GOTHIC = "HYGothic-Medium"
_registered = False

_ICON = {"earth": "지구", "leaf": "환경", "sun": "에너지", "water": "물",
         "chart": "성장", "shield": "안전", "check": "확인", "people": "사람",
         "target": "목표", "trophy": "성과", "bell": "알림", "clock": "시간"}


def _ensure_fonts() -> None:
    global _registered
    if not _registered:
        pdfmetrics.registerFont(UnicodeCIDFont(_SERIF))
        pdfmetrics.registerFont(UnicodeCIDFont(_GOTHIC))
        _registered = True


def _c(hex_str: str):
    return colors.HexColor(hex_str)


def _fit(canv, text, font, size, max_w):
    """max_w에 맞게 글자수 자르기."""
    if not text:
        return ""
    while text and pdfmetrics.stringWidth(text, font, size) > max_w:
        text = text[:-1]
    return text


class SlidePreview(Flowable):
    """스킨 색으로 그리는 16:9 슬라이드 축소 화면."""

    def __init__(self, slide: Slide, sk: Skin, width: float):
        super().__init__()
        self.s = slide
        self.sk = sk
        self.w = width
        self.h = width * 9.0 / 16.0

    def wrap(self, aw, ah):
        return (self.w, self.h)

    def draw(self):
        c = self.canv
        s, sk, p = self.s, self.sk, self.sk.palette
        W, H = self.w, self.h
        _ensure_fonts()

        # 배경 + 테두리
        c.setFillColor(_c(p.bg))
        c.setStrokeColor(_c("#D9D9D9"))
        c.setLineWidth(0.7)
        c.roundRect(0, 0, W, H, 4, stroke=1, fill=1)

        pad = W * 0.06
        title = s.title or spec(s.layout).ko_name

        if s.layout == Layout.COVER:
            c.setFillColor(_c(p.accent))
            c.rect(0, H * 0.44, W, H * 0.015, stroke=0, fill=1)
            c.setFillColor(_c(p.secondary))
            c.setFont(_GOTHIC, 5)
            c.drawString(pad, H - pad - 4, "CHANGCHENET")
            c.setFillColor(_c(p.primary))
            c.setFont(_GOTHIC, 15)
            c.drawString(pad, H * 0.5, _fit(c, title, _GOTHIC, 15, W - 2 * pad))
            if s.subtitle:
                c.setFillColor(_c(p.secondary))
                c.setFont(_SERIF, 8)
                c.drawString(pad, H * 0.5 - 14, _fit(c, s.subtitle, _SERIF, 8, W - 2 * pad))
            return

        if s.layout == Layout.CLOSING:
            c.setFillColor(_c(p.primary))
            c.setFont(_GOTHIC, 16)
            c.drawCentredString(W / 2, H / 2, title)
            c.setFillColor(_c(p.accent))
            c.rect(W / 2 - 20, H / 2 - 10, 40, 2, stroke=0, fill=1)
            return

        # 공통 상단: 번호칩 + 제목 + 언더라인
        num = {Layout.PHOTO_FOCUS: "1", Layout.SPLIT: "2", Layout.ICON_TRIPLE: "3",
               Layout.TIMELINE: "4", Layout.CHART_FOCUS: "5", Layout.CARD_GRID: "6",
               Layout.TOC: ""}.get(s.layout, "")
        cy = H - pad - 6
        if num:
            c.setFillColor(_c(p.accent))
            c.circle(pad + 5, cy + 3, 6, stroke=0, fill=1)
            c.setFillColor(_c(p.on_primary))
            c.setFont(_GOTHIC, 6)
            c.drawCentredString(pad + 5, cy + 1, num)
            tx = pad + 16
        else:
            tx = pad
        c.setFillColor(_c(p.primary))
        c.setFont(_GOTHIC, 11)
        c.drawString(tx, cy, _fit(c, title, _GOTHIC, 11, W - tx - pad))
        c.setFillColor(_c(p.accent))
        c.rect(tx, cy - 5, W * 0.18, 1.6, stroke=0, fill=1)

        body_top = cy - 14

        def chips(items, cols, box_h):
            n = min(len(items), cols)
            if n == 0:
                return
            gap = W * 0.02
            cw = (W - 2 * pad - (n - 1) * gap) / n
            for i in range(n):
                it = items[i]
                x = pad + i * (cw + gap)
                y = body_top - box_h
                c.setFillColor(_c(p.card))
                c.roundRect(x, y, cw, box_h, 3, stroke=0, fill=1)
                c.setFillColor(_c(p.on_primary))
                c.setFont(_GOTHIC, 6.5)
                c.drawCentredString(x + cw / 2, y + box_h - 12,
                                    _fit(c, it.heading, _GOTHIC, 6.5, cw - 6))
                if it.body:
                    c.setFont(_SERIF, 5.5)
                    c.drawCentredString(x + cw / 2, y + box_h - 20,
                                        _fit(c, it.body, _SERIF, 5.5, cw - 6))

        if s.layout in (Layout.ICON_TRIPLE, Layout.CARD_GRID, Layout.TOC):
            chips(s.items, 4 if len(s.items) <= 4 else 3, H * 0.42)
        elif s.layout == Layout.TIMELINE:
            chips(s.items, min(len(s.items), 5), H * 0.30)
        elif s.layout in (Layout.PHOTO_FOCUS, Layout.SPLIT, Layout.CHART_FOCUS):
            # 사진/그래프 자리표 박스
            bx, by = pad, body_top - H * 0.42
            bw = W * 0.44 if s.layout != Layout.PHOTO_FOCUS else W - 2 * pad
            c.setFillColor(_c(p.card))
            c.roundRect(bx, by, bw, H * 0.42, 3, stroke=0, fill=1)
            c.setFillColor(_c(p.on_primary))
            c.setFont(_GOTHIC, 7)
            label = "그래프" if s.layout == Layout.CHART_FOCUS else "사진"
            c.drawCentredString(bx + bw / 2, by + H * 0.21, label)
            if s.layout != Layout.PHOTO_FOCUS and s.body:
                c.setFillColor(_c(p.ink))
                c.setFont(_SERIF, 6.5)
                c.drawString(bx + bw + 8, by + H * 0.34,
                             _fit(c, s.body, _SERIF, 6.5, W - bx - bw - pad - 8))


def _styles():
    _ensure_fonts()
    ss = getSampleStyleSheet()
    base = ss["Normal"]
    return {
        "doc_title": ParagraphStyle("doc_title", parent=base, fontName=_GOTHIC,
                                    fontSize=20, leading=26, spaceAfter=3),
        "doc_sub": ParagraphStyle("doc_sub", parent=base, fontName=_SERIF,
                                  fontSize=11, leading=15, textColor=_c("#555")),
        "slide_no": ParagraphStyle("slide_no", parent=base, fontName=_GOTHIC,
                                   fontSize=9, leading=12, textColor=_c("#1F4E8C"),
                                   spaceBefore=2, spaceAfter=4),
        "label": ParagraphStyle("label", parent=base, fontName=_GOTHIC, fontSize=10,
                                leading=14, textColor=_c("#1F4E8C"),
                                spaceBefore=7, spaceAfter=2),
        "body": ParagraphStyle("body", parent=base, fontName=_SERIF, fontSize=10.5,
                               leading=16, alignment=TA_LEFT),
        "script": ParagraphStyle("script", parent=base, fontName=_SERIF, fontSize=10.5,
                                 leading=17, backColor=_c("#F5F3EE"),
                                 borderPadding=(6, 8, 6, 8)),
        "bullet": ParagraphStyle("bullet", parent=base, fontName=_SERIF, fontSize=10.5,
                                 leading=15),
    }


def build(deck: Deck, out_path: str, *, skin: str | None = None) -> str:
    st = _styles()
    sk = get_skin(skin or deck.skin)
    doc = SimpleDocTemplate(
        out_path, pagesize=A4,
        leftMargin=18 * mm, rightMargin=18 * mm,
        topMargin=16 * mm, bottomMargin=16 * mm,
        title=f"{deck.title} — 설명자료",
    )
    prev_w = (A4[0] - 36 * mm) * 0.66  # 미리보기 폭
    flow = []
    flow.append(Paragraph(deck.title, st["doc_title"]))
    if deck.subtitle:
        flow.append(Paragraph(deck.subtitle, st["doc_sub"]))
    flow.append(Paragraph("발표 설명자료 · 슬라이드별 화면 + 스크립트", st["doc_sub"]))
    flow.append(Spacer(1, 4))
    flow.append(HRFlowable(width="100%", thickness=1.2, color=_c("#1F4E8C")))

    for i, s in enumerate(deck.slides, start=1):
        block = [
            Spacer(1, 6),
            Paragraph(f"슬라이드 {i} · {spec(s.layout).ko_name}", st["slide_no"]),
            SlidePreview(s, sk, prev_w),
            Spacer(1, 4),
        ]
        if s.note.summary:
            block += [Paragraph("■ 핵심 요약", st["label"]),
                      Paragraph(s.note.summary, st["body"])]
        if s.note.must_know:
            block += [Paragraph("■ 꼭 알아야 할 것", st["label"]),
                      ListFlowable([ListItem(Paragraph(x, st["bullet"]), leftIndent=10)
                                    for x in s.note.must_know],
                                   bulletType="bullet", start="•", leftIndent=12)]
        if s.note.script:
            block += [Paragraph("■ 발표 스크립트", st["label"]),
                      Paragraph(s.note.script.replace("\n", "<br/>"), st["script"])]
        block.append(PageBreak())
        # 한 슬라이드는 되도록 한 페이지에 유지
        from reportlab.platypus import KeepTogether
        flow.append(KeepTogether(block[:-1]))
        flow.append(PageBreak())

    doc.build(flow)
    return out_path
