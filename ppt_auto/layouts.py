"""레이아웃 메타데이터 — 각 레이아웃이 어떤 필드를 쓰고 언제 적합한지.

파스텔 레이아웃 키트의 "활용 상황" 문구를 그대로 반영한다. 파서가
자유 텍스트를 배치할 때, 그리고 문서/도움말 출력에 쓰인다.
"""
from __future__ import annotations

from dataclasses import dataclass

from .schema import Layout


@dataclass
class LayoutSpec:
    layout: Layout
    ko_name: str
    usage: str                     # 활용 상황
    min_items: int = 0
    max_items: int = 0
    wants_image: bool = False
    wants_chart: bool = False


SPECS: dict[Layout, LayoutSpec] = {
    Layout.COVER: LayoutSpec(
        Layout.COVER, "표지", "발표 시작 — 제목·부제·작성자", 0, 0),
    Layout.TOC: LayoutSpec(
        Layout.TOC, "목차", "전체 개요 제시", 2, 6),
    Layout.PHOTO_FOCUS: LayoutSpec(
        Layout.PHOTO_FOCUS, "사진 중심형",
        "사진으로 주제나 분위기를 보여줄 때 (예: 여행, 체험, 전시, 실험결과)",
        0, 0, wants_image=True),
    Layout.SPLIT: LayoutSpec(
        Layout.SPLIT, "좌우 분할형",
        "설명 중심 슬라이드, 개념이나 이론 소개용", 0, 0, wants_image=True),
    Layout.ICON_TRIPLE: LayoutSpec(
        Layout.ICON_TRIPLE, "아이콘 3분할형",
        "비교, 특징 정리, 요약형 콘텐츠에 적합", 2, 4),
    Layout.TIMELINE: LayoutSpec(
        Layout.TIMELINE, "타임라인 / 단계형",
        "순서나 과정 설명 (예: 실험 단계, 활동 순서, 성장 과정)", 2, 5),
    Layout.CHART_FOCUS: LayoutSpec(
        Layout.CHART_FOCUS, "그래프/비주얼 중심형",
        "조사 결과, 통계 자료, 비교 수치 발표에 활용", 0, 0, wants_chart=True),
    Layout.CARD_GRID: LayoutSpec(
        Layout.CARD_GRID, "카드형 / 그리드형",
        "여러 항목이나 사례를 한 번에 보여줄 때", 2, 6),
    Layout.CLOSING: LayoutSpec(
        Layout.CLOSING, "마무리", "발표 종료 — 감사 인사·연락처", 0, 0),
}


def spec(layout: Layout) -> LayoutSpec:
    return SPECS[layout]
