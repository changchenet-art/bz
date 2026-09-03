"""부정 이슈 + 원고 세트 → 대응 브리핑 Deck.

'부정적인 것'(이슈)과 '원고'를 주면, 차분한 위기·해명 브리핑 구성으로 짠다.
기본 스킨은 신뢰감 있는 deep_navy.

입력:
  - issue_text : 대응 대상이 되는 부정적 이슈(사실/주장) 원문
  - manuscript : 대응 원고. '##' 섹션이 있으면 그대로 쓰고, 없으면
                 표준 대응 골격(개요→사실관계→경과→근거→대응→향후)으로 배치.
"""
from __future__ import annotations

import re

from ..schema import Deck, Item, Layout, Slide
from .common import infer_layout, parse_frontmatter, split_items
from .freetext import _section_to_slide

DEFAULT_ISSUE_SKIN = "deep_navy"

# 원고에 섹션이 없을 때 채워 넣는 표준 대응 골격
_SCAFFOLD = [
    ("사안 개요", Layout.SPLIT),
    ("사실관계 확인", Layout.ICON_TRIPLE),
    ("경과 및 대응 경위", Layout.TIMELINE),
    ("근거 자료", Layout.CHART_FOCUS),
    ("대응 방안", Layout.CARD_GRID),
    ("향후 계획", Layout.SPLIT),
]


def parse(issue_text: str, manuscript: str) -> Deck:
    meta, body = parse_frontmatter(manuscript)
    skin = meta.get("skin", DEFAULT_ISSUE_SKIN)
    deck = Deck(
        title=meta.get("title", "사안 대응 브리핑"),
        subtitle=meta.get("subtitle", "사실관계와 대응 방향"),
        author=meta.get("author", ""),
        date=meta.get("date", ""),
        skin=skin,
        issue=issue_text.strip(),
    )

    # 표지
    deck.slides.append(Slide(layout=Layout.COVER, title=deck.title,
                             subtitle=deck.subtitle))

    # 원고 섹션 분리
    parts = re.split(r"^\s*##\s+", body, flags=re.M)
    sections: list[tuple[str, str]] = []
    for chunk in parts:
        chunk = chunk.strip("\n")
        if not chunk:
            continue
        head, _, rest = chunk.partition("\n")
        sections.append((head.strip(), rest))

    # 목차
    toc = Slide(layout=Layout.TOC, title="목차")

    content: list[Slide] = []
    # 1) 사안 개요 — 이슈 원문을 중립적으로 제시
    overview = Slide(
        layout=Layout.SPLIT, title="사안 개요",
        subtitle="무엇이 제기되었는가",
        body=(f"다음과 같은 지적이 제기되었습니다.\n\n“{deck.issue}”\n\n"
              "이에 대한 사실관계와 대응 방향을 말씀드리겠습니다.").strip(),
    )
    content.append(overview)

    if sections:
        # 원고에 섹션이 있으면 그대로 사용
        for head, rest in sections:
            content.append(_section_to_slide(head, rest))
    else:
        # 없으면 표준 골격에 원고 전체를 개요 본문으로만 배치
        if body.strip():
            overview.body += "\n\n" + body.strip()

    deck.slides.extend(content)
    toc.items = [Item(heading=s.title) for s in content if s.title]
    deck.slides.insert(1, toc)

    # 마무리
    deck.slides.append(Slide(layout=Layout.CLOSING, title="감사합니다",
                             subtitle=deck.author or "문의 사항은 언제든 연락 주세요"))
    return deck


def parse_files(issue_path: str, manuscript_path: str) -> Deck:
    with open(issue_path, encoding="utf-8") as f:
        issue = f.read()
    with open(manuscript_path, encoding="utf-8") as f:
        manuscript = f.read()
    return parse(issue, manuscript)
