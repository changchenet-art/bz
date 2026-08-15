"""데이터 스키마 — 원고를 담는 중립적(스킨/엔진 독립적) 구조.

파서(입력) → Deck → 렌더러(출력)로 흐른다. Deck은 어떤 스킨/엔진에도
종속되지 않는 순수 데이터다.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class Layout(str, Enum):
    """9가지 레이아웃 유형. 파스텔 레이아웃 키트(및 스킨 4종)에서 도출."""

    COVER = "cover"                # 표지: 큰제목·부제·작성자
    TOC = "toc"                    # 목차: 항목 리스트(6분할 권장)
    PHOTO_FOCUS = "photo_focus"    # ① 사진 중심형: 제목 + 대형사진 + 설명문
    SPLIT = "split"                # ② 좌우 분할형: 좌 사진 / 우 제목·부제·설명
    ICON_TRIPLE = "icon_triple"    # ③ 아이콘 3(4)분할: 제목 + 아이콘 카드
    TIMELINE = "timeline"          # ④ 타임라인/단계형: Step 1·2·3
    CHART_FOCUS = "chart_focus"    # ⑤ 그래프/비주얼: 좌 그래프 / 우 설명
    CARD_GRID = "card_grid"        # ⑥ 카드/그리드형: 키워드 카드 여러 개
    CLOSING = "closing"            # 마무리: 감사합니다 + 연락처


# 콘텐츠 성격 → 추천 레이아웃 (자유텍스트 자동배치에 사용)
CONTENT_LAYOUTS = [
    Layout.PHOTO_FOCUS,
    Layout.SPLIT,
    Layout.ICON_TRIPLE,
    Layout.TIMELINE,
    Layout.CHART_FOCUS,
    Layout.CARD_GRID,
]


@dataclass
class Item:
    """아이콘/타임라인/카드/목차의 한 항목."""

    heading: str = ""              # 부제목 / 키워드 / 단계 이름
    body: str = ""                 # 설명 문장
    icon: str = ""                 # 아이콘 키워드(예: earth, leaf, sun, check)
    step_label: str = ""           # "Step 1" 등 (타임라인)


@dataclass
class ChartSpec:
    """간단한 차트 명세. 로컬 렌더러가 python-pptx 차트로 그린다."""

    kind: str = "bar"              # bar | line | pie | radar
    categories: list[str] = field(default_factory=list)
    series: dict[str, list[float]] = field(default_factory=dict)  # {계열명: [값...]}
    unit: str = ""


@dataclass
class SlideNote:
    """슬라이드 하단 발표자 노트 → PDF 설명자료 소스."""

    summary: str = ""              # 핵심 요약 (한 줄)
    must_know: list[str] = field(default_factory=list)  # 꼭 알아야 할 것
    script: str = ""               # "안녕하세요…" 발표 스크립트


@dataclass
class Slide:
    layout: Layout = Layout.PHOTO_FOCUS
    title: str = ""
    subtitle: str = ""
    body: str = ""                 # 본문/설명문
    items: list[Item] = field(default_factory=list)
    image: str = ""                # 이미지 경로 또는 키워드(플레이스홀더)
    chart: Optional[ChartSpec] = None
    note: SlideNote = field(default_factory=SlideNote)
    reveal: bool = True            # 단계적 표현(항목 하나씩 등장) 사용 여부
    usage: str = ""                # "활용 상황" 메모(선택)

    # ── 발표노트(예시 포맷) 전용 리치 필드 ─────────────────────
    time: str = ""                 # "40초" 등 배정 시간
    points: list[str] = field(default_factory=list)  # 발표 멘트(핵심 강조 문장)
    hook: list[str] = field(default_factory=list)     # ★강점 — 못 박을 것
    bait: list[str] = field(default_factory=list)     # 🎣미끼 — 끌어낼 질문
    ref: list[str] = field(default_factory=list)      # 참고 — 근거
    shot: str = ""                 # 사진/캡처 자리표 라벨(있으면 표시)


@dataclass
class Deck:
    title: str = "제목을 입력하세요"
    subtitle: str = ""
    author: str = ""
    date: str = ""
    skin: str = "beige_business"   # skins.registry 의 키
    slides: list[Slide] = field(default_factory=list)
    # 부정 이슈 대응 모드에서 채워지는 부가 정보
    issue: str = ""                # 대상이 되는 부정적 이슈 원문
    # 발표노트(예시 포맷) 문서 상단
    banner_meta: list[str] = field(default_factory=list)   # 배너 메타 pill 문구들
    strategy_rows: list[dict] = field(default_factory=list)  # 전략지도 표 행
    #   각 행: {"slide": "04", "q": "공격 Q5 · 실무 Q1", "bait": "감액 조항 …"}

    def content_slides(self) -> list[Slide]:
        return [s for s in self.slides
                if s.layout not in (Layout.COVER, Layout.TOC, Layout.CLOSING)]
