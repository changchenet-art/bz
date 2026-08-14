"""자유 텍스트/마크다운 원고 → Deck.

형식(느슨함):
    제목: 2026 상반기 성과 브리핑
    부제: 지속가능 경영 성과
    작성자: 홍길동
    스킨: beige_business

    ## 추진 배경
    본문 문단...
    - 항목1: 설명
    - 항목2: 설명

    ## 주요 성과 [그래프]
    - 매출: 120억
    ...

'##' 로 슬라이드를 나눈다. 표지/목차/마무리는 자동 생성.
레이아웃은 제목의 [태그] 또는 내용 모양으로 자동 추론.
"""
from __future__ import annotations

import re

from ..schema import ChartSpec, Deck, Item, Layout, Slide
from ..skins.registry import DEFAULT_SKIN
from .common import infer_layout, parse_frontmatter, split_items


def _chart_from_items(items: list[Item]) -> ChartSpec | None:
    """항목이 '계열명: 12,34,56' 꼴이면 차트로 변환."""
    spec = ChartSpec(kind="bar")
    for it in items:
        nums = re.findall(r"-?\d+(?:\.\d+)?", it.body)
        if it.heading and len(nums) >= 2:
            spec.series[it.heading] = [float(n) for n in nums]
    if not spec.series:
        return None
    maxlen = max(len(v) for v in spec.series.values())
    spec.categories = [f"{i+1}" for i in range(maxlen)]
    return spec


def _section_to_slide(title: str, block: str) -> Slide:
    lines = block.splitlines()
    bullet_lines = [l for l in lines if re.match(r"^\s*(?:[-*•·▪◦o]\s+|\d+[.)]\s|Step)", l, re.I)]
    para = " ".join(l.strip() for l in lines
                    if l.strip() and l not in bullet_lines)
    items = split_items(bullet_lines)
    clean_title = re.sub(r"\s*\[[^\]]+\]\s*$", "", title).strip()
    layout = infer_layout(title, para, items)
    s = Slide(layout=layout, title=clean_title, body=para, items=items)
    if layout == Layout.PHOTO_FOCUS:
        s.image = "PLACEHOLDER"  # 렌더러가 자리표 사진 박스로
    if layout == Layout.CHART_FOCUS:
        s.chart = _chart_from_items(items)
        if s.chart:
            s.items = []  # 숫자는 차트로 옮겼으니 목록에서 제거
    return s


def parse(text: str) -> Deck:
    meta, body = parse_frontmatter(text)
    deck = Deck(
        title=meta.get("title", "제목을 입력하세요"),
        subtitle=meta.get("subtitle", ""),
        author=meta.get("author", ""),
        date=meta.get("date", ""),
        skin=meta.get("skin", DEFAULT_SKIN),
        issue=meta.get("issue", ""),
    )

    # '##' 헤딩으로 섹션 분리
    parts = re.split(r"^\s*##\s+", body, flags=re.M)
    sections: list[tuple[str, str]] = []
    for chunk in parts:
        chunk = chunk.strip("\n")
        if not chunk:
            continue
        head, _, rest = chunk.partition("\n")
        sections.append((head.strip(), rest))

    # 표지
    deck.slides.append(Slide(layout=Layout.COVER, title=deck.title,
                             subtitle=deck.subtitle))
    # 목차
    if sections:
        toc = Slide(layout=Layout.TOC, title="목차")
        toc.items = [Item(heading=re.sub(r"\s*\[[^\]]+\]\s*$", "", h).strip())
                     for h, _ in sections]
        deck.slides.append(toc)
    # 본문
    for head, rest in sections:
        deck.slides.append(_section_to_slide(head, rest))
    # 마무리
    deck.slides.append(Slide(layout=Layout.CLOSING, title="감사합니다",
                             subtitle=deck.author))
    return deck


def parse_file(path: str) -> Deck:
    with open(path, encoding="utf-8") as f:
        return parse(f.read())
