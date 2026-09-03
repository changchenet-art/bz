"""슬라이드 노트 자동 생성.

각 슬라이드에 대해 세 가지를 만든다:
  - summary   : 핵심 요약 (한 줄)
  - must_know : 꼭 알아야 할 것 (불릿)
  - script    : "안녕하세요…"로 이어지는 발표 스크립트

파서가 이미 채운 노트가 있으면 존중하고, 비어 있는 항목만 보완한다.
템플릿 기반이라 오프라인에서 동작한다. (필요하면 상위에서 LLM으로 교체 가능)
"""
from __future__ import annotations

import re

from .schema import Deck, Layout, Slide


def _sentences(text: str) -> list[str]:
    text = re.sub(r"\s+", " ", (text or "").strip())
    if not text:
        return []
    parts = re.split(r"(?<=[.!?。])\s+|(?<=[다요])\.\s*", text)
    return [p.strip(" .") for p in parts if p.strip(" .")]


def _keypoints(slide: Slide) -> list[str]:
    pts: list[str] = []
    for it in slide.items:
        h = it.heading.strip()
        b = it.body.strip()
        if h and b:
            pts.append(f"{h}: {b}")
        elif h or b:
            pts.append(h or b)
    if not pts:
        pts = _sentences(slide.body)[:3]
    return pts[:4]


def _script_for(slide: Slide, deck: Deck, idx: int, total: int) -> str:
    title = slide.title.strip() or deck.title
    body = slide.body.strip()
    pts = _keypoints(slide)

    if slide.layout == Layout.COVER:
        who = f"{deck.author} " if deck.author else ""
        return (f"안녕하세요. 오늘 발표를 맡은 {who}입니다. "
                f"지금부터 「{deck.title}」에 대해 말씀드리겠습니다. "
                + (f"{deck.subtitle} " if deck.subtitle else "")
                + "끝까지 함께해 주시면 감사하겠습니다.").replace("  ", " ")

    if slide.layout == Layout.TOC:
        names = " / ".join(it.heading for it in slide.items if it.heading)
        return (f"먼저 오늘 발표의 전체 흐름을 소개해 드리겠습니다. "
                + (f"{names} 순서로 진행합니다. " if names else "")
                + "각 부분을 차례대로 살펴보겠습니다.")

    if slide.layout == Layout.CLOSING:
        return ("이상으로 발표를 마치겠습니다. "
                "궁금하신 점은 언제든 말씀해 주세요. 경청해 주셔서 감사합니다.")

    # 콘텐츠 슬라이드
    lead = f"이번 슬라이드에서는 {title}에 대해 말씀드리겠습니다. "
    if slide.layout == Layout.TIMELINE:
        steps = " 그리고 ".join(
            f"{it.step_label or f'{i+1}단계'}에서는 {it.heading}"
            for i, it in enumerate(slide.items) if it.heading)
        mid = f"진행은 {steps} 순으로 이어집니다. " if steps else ""
    elif slide.layout in (Layout.ICON_TRIPLE, Layout.CARD_GRID):
        mid = "".join(f"{it.heading}은(는) {it.body} " for it in slide.items
                      if it.heading and it.body)
    elif slide.layout == Layout.CHART_FOCUS:
        mid = (body + " ") if body else "그래프에서 보시는 것처럼 수치를 함께 짚어보겠습니다. "
    else:
        mid = (body + " ") if body else ""

    tail = "이 점을 특히 기억해 주시면 좋겠습니다."
    return (lead + mid + tail).strip()


def generate(deck: Deck, *, presenter: str = "", org: str = "") -> Deck:
    """Deck의 각 슬라이드 노트를 채운다(빈 항목만)."""
    total = len(deck.slides)
    for i, s in enumerate(deck.slides):
        note = s.note
        if not note.summary:
            note.summary = (s.title.strip()
                            or (_sentences(s.body)[:1] or [""])[0]
                            or deck.title)
        if not note.must_know:
            note.must_know = _keypoints(s)
        if not note.script:
            note.script = _script_for(s, deck, i, total)
    return deck
