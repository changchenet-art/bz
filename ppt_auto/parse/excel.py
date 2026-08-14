"""엑셀(.xlsx) 양식 → Deck. 슬라이드 1행 = 1슬라이드 (가장 정확한 제어).

열:
  layout | title | subtitle | body | items | image |
  chart_kind | chart_categories | chart_series |
  note_summary | note_must | note_script | reveal

  items         : "키워드1: 설명1 | 키워드2: 설명2 | ..."  (파이프로 항목 구분)
  chart_categories : "2023,2024,2025"
  chart_series  : "매출=100,120,150; 이익=20,25,30"
  note_must     : "핵심1 | 핵심2 | 핵심3"
"""
from __future__ import annotations

from openpyxl import Workbook, load_workbook

from ..schema import ChartSpec, Deck, Item, Layout, SlideNote, Slide
from ..skins.registry import DEFAULT_SKIN
from .common import guess_icon

COLUMNS = ["layout", "title", "subtitle", "body", "items", "image",
           "chart_kind", "chart_categories", "chart_series",
           "note_summary", "note_must", "note_script", "reveal"]

_LAYOUT_ALIASES = {
    "표지": Layout.COVER, "cover": Layout.COVER,
    "목차": Layout.TOC, "toc": Layout.TOC,
    "사진": Layout.PHOTO_FOCUS, "사진중심": Layout.PHOTO_FOCUS, "photo_focus": Layout.PHOTO_FOCUS,
    "좌우": Layout.SPLIT, "좌우분할": Layout.SPLIT, "split": Layout.SPLIT,
    "아이콘": Layout.ICON_TRIPLE, "icon_triple": Layout.ICON_TRIPLE,
    "단계": Layout.TIMELINE, "타임라인": Layout.TIMELINE, "timeline": Layout.TIMELINE,
    "그래프": Layout.CHART_FOCUS, "차트": Layout.CHART_FOCUS, "chart_focus": Layout.CHART_FOCUS,
    "카드": Layout.CARD_GRID, "그리드": Layout.CARD_GRID, "card_grid": Layout.CARD_GRID,
    "마무리": Layout.CLOSING, "closing": Layout.CLOSING,
}


def _layout(val: str) -> Layout:
    key = (val or "").strip().lower()
    return _LAYOUT_ALIASES.get(val.strip() if val else "", _LAYOUT_ALIASES.get(key, Layout.SPLIT))


def _items(val: str) -> list[Item]:
    out: list[Item] = []
    for chunk in (val or "").split("|"):
        chunk = chunk.strip()
        if not chunk:
            continue
        if ":" in chunk or "：" in chunk:
            h, _, b = chunk.replace("：", ":").partition(":")
            it = Item(heading=h.strip(), body=b.strip())
        else:
            it = Item(heading=chunk)
        it.icon = guess_icon(it.heading + it.body)
        out.append(it)
    for i, it in enumerate(out):
        it.step_label = f"Step {i + 1}"
    return out


def _chart(kind: str, cats: str, series: str) -> ChartSpec | None:
    if not kind and not series:
        return None
    spec = ChartSpec(kind=(kind or "bar").strip())
    spec.categories = [c.strip() for c in (cats or "").split(",") if c.strip()]
    for grp in (series or "").split(";"):
        grp = grp.strip()
        if not grp or "=" not in grp:
            continue
        name, _, vals = grp.partition("=")
        try:
            spec.series[name.strip()] = [float(v) for v in vals.split(",") if v.strip()]
        except ValueError:
            continue
    return spec if spec.series else None


def parse_file(path: str) -> Deck:
    wb = load_workbook(path, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        return Deck()
    header = [str(c).strip().lower() if c else "" for c in rows[0]]
    idx = {name: header.index(name) for name in COLUMNS if name in header}

    def cell(row, name):
        i = idx.get(name)
        if i is None or i >= len(row) or row[i] is None:
            return ""
        return str(row[i]).strip()

    deck = Deck(skin=DEFAULT_SKIN)
    for row in rows[1:]:
        if row is None or all(c is None or str(c).strip() == "" for c in row):
            continue
        layout = _layout(cell(row, "layout"))
        s = Slide(
            layout=layout,
            title=cell(row, "title"),
            subtitle=cell(row, "subtitle"),
            body=cell(row, "body"),
            items=_items(cell(row, "items")),
            image="PLACEHOLDER" if (layout == Layout.PHOTO_FOCUS and not cell(row, "image"))
                  else cell(row, "image"),
            chart=_chart(cell(row, "chart_kind"), cell(row, "chart_categories"),
                         cell(row, "chart_series")),
            reveal=cell(row, "reveal").lower() not in ("no", "false", "0", "off", "아니오"),
        )
        s.note = SlideNote(
            summary=cell(row, "note_summary"),
            must_know=[x.strip() for x in cell(row, "note_must").split("|") if x.strip()],
            script=cell(row, "note_script"),
        )
        # 표지/마무리에서 부제로 작성자 추출
        if layout == Layout.COVER:
            deck.title = s.title or deck.title
            deck.subtitle = s.subtitle
        deck.slides.append(s)
    return deck


def write_template(path: str) -> None:
    """빈칸 채우기용 엑셀 양식 생성 (예시 행 포함)."""
    wb = Workbook()
    ws = wb.active
    ws.title = "슬라이드"
    ws.append(COLUMNS)
    examples = [
        ["표지", "2026 상반기 성과 브리핑", "지속가능 경영 성과", "", "", "",
         "", "", "", "", "", "", ""],
        ["좌우", "추진 배경", "왜 시작했나", "지난해 대비 관심이 크게 늘었습니다. 배경을 설명합니다.",
         "", "PLACEHOLDER", "", "", "", "", "", "", ""],
        ["아이콘", "3대 핵심 방향", "", "", "탄소감축: 배출 30% 절감 | 자원순환: 재활용 확대 | 상생: 지역과 협력",
         "", "", "", "", "", "", "", ""],
        ["단계", "추진 절차", "", "", "1) 진단: 현황 파악 | 2) 설계: 계획 수립 | 3) 실행: 현장 적용",
         "", "", "", "", "", "", "", ""],
        ["그래프", "주요 지표", "전년 대비", "수치가 꾸준히 개선되고 있습니다.", "",
         "", "bar", "2024,2025,2026", "실적=80,110,150", "", "", "", ""],
        ["카드", "적용 사례", "", "", "A사업: 성공적 안착 | B사업: 확대 중 | C사업: 준비 | D사업: 검토",
         "", "", "", "", "", "", "", ""],
        ["마무리", "감사합니다", "문의: hello@changchenet.com", "", "", "",
         "", "", "", "", "", "", ""],
    ]
    for ex in examples:
        ws.append(ex)
    # 열 너비 살짝
    widths = [10, 24, 18, 40, 44, 12, 10, 16, 24, 20, 24, 40, 8]
    for i, w in enumerate(widths, start=1):
        ws.column_dimensions[ws.cell(row=1, column=i).column_letter].width = w
    wb.save(path)
