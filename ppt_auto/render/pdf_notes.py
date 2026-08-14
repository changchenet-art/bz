"""슬라이드 노트 → PDF 설명자료.

각 슬라이드마다: 번호·제목 / 핵심 요약 / 꼭 알아야 할 것 / 발표 스크립트.
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
    HRFlowable, ListFlowable, ListItem, PageBreak, Paragraph,
    SimpleDocTemplate, Spacer,
)

from ..layouts import spec
from ..schema import Deck, Layout

_SERIF = "HYSMyeongJo-Medium"
_GOTHIC = "HYGothic-Medium"
_registered = False


def _ensure_fonts() -> None:
    global _registered
    if not _registered:
        pdfmetrics.registerFont(UnicodeCIDFont(_SERIF))
        pdfmetrics.registerFont(UnicodeCIDFont(_GOTHIC))
        _registered = True


def _styles():
    _ensure_fonts()
    ss = getSampleStyleSheet()
    base = ss["Normal"]
    return {
        "doc_title": ParagraphStyle("doc_title", parent=base, fontName=_GOTHIC,
                                    fontSize=22, leading=28, spaceAfter=4),
        "doc_sub": ParagraphStyle("doc_sub", parent=base, fontName=_SERIF,
                                  fontSize=12, leading=16, textColor=colors.HexColor("#555")),
        "slide_no": ParagraphStyle("slide_no", parent=base, fontName=_GOTHIC,
                                   fontSize=9, leading=12, textColor=colors.HexColor("#8A6D00")),
        "slide_title": ParagraphStyle("slide_title", parent=base, fontName=_GOTHIC,
                                      fontSize=15, leading=20, spaceBefore=2, spaceAfter=6),
        "label": ParagraphStyle("label", parent=base, fontName=_GOTHIC, fontSize=10,
                                leading=14, textColor=colors.HexColor("#1F4E8C"),
                                spaceBefore=8, spaceAfter=2),
        "body": ParagraphStyle("body", parent=base, fontName=_SERIF, fontSize=11,
                               leading=17, alignment=TA_LEFT),
        "script": ParagraphStyle("script", parent=base, fontName=_SERIF, fontSize=11,
                                 leading=18, backColor=colors.HexColor("#F5F3EE"),
                                 borderPadding=(6, 8, 6, 8), leftIndent=2, rightIndent=2),
        "bullet": ParagraphStyle("bullet", parent=base, fontName=_SERIF, fontSize=11,
                                 leading=16),
    }


def build(deck: Deck, out_path: str) -> str:
    st = _styles()
    doc = SimpleDocTemplate(
        out_path, pagesize=A4,
        leftMargin=20 * mm, rightMargin=20 * mm,
        topMargin=18 * mm, bottomMargin=18 * mm,
        title=f"{deck.title} — 설명자료",
    )
    flow = []
    # 표지
    flow.append(Paragraph(deck.title, st["doc_title"]))
    if deck.subtitle:
        flow.append(Paragraph(deck.subtitle, st["doc_sub"]))
    flow.append(Paragraph("발표 설명자료 (슬라이드 노트)", st["doc_sub"]))
    if deck.author:
        flow.append(Paragraph(f"작성자: {deck.author}", st["doc_sub"]))
    flow.append(Spacer(1, 6))
    flow.append(HRFlowable(width="100%", thickness=1.2,
                           color=colors.HexColor("#1F4E8C")))
    flow.append(Spacer(1, 4))

    for i, s in enumerate(deck.slides, start=1):
        ko = spec(s.layout).ko_name
        flow.append(Paragraph(f"슬라이드 {i} · {ko}", st["slide_no"]))
        flow.append(Paragraph(s.title or ko, st["slide_title"]))

        if s.note.summary:
            flow.append(Paragraph("■ 핵심 요약", st["label"]))
            flow.append(Paragraph(s.note.summary, st["body"]))

        if s.note.must_know:
            flow.append(Paragraph("■ 꼭 알아야 할 것", st["label"]))
            flow.append(ListFlowable(
                [ListItem(Paragraph(x, st["bullet"]), leftIndent=10)
                 for x in s.note.must_know],
                bulletType="bullet", start="•", leftIndent=12))

        if s.note.script:
            flow.append(Paragraph("■ 발표 스크립트", st["label"]))
            flow.append(Paragraph(s.note.script.replace("\n", "<br/>"), st["script"]))

        flow.append(Spacer(1, 6))
        flow.append(HRFlowable(width="100%", thickness=0.4,
                               color=colors.HexColor("#DDD")))
        flow.append(Spacer(1, 4))

    doc.build(flow)
    return out_path
