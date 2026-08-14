"""파서 공통 유틸 — 레이아웃 추론, 항목 분리, 프런트매터."""
from __future__ import annotations

import re

from ..schema import Item, Layout


_ICON_HINTS = {
    "지구": "earth", "환경": "leaf", "에너지": "sun", "물": "water",
    "성장": "chart", "안전": "shield", "확인": "check", "사람": "people",
    "목표": "target", "성과": "trophy", "알림": "bell", "시간": "clock",
}


def guess_icon(text: str) -> str:
    for k, v in _ICON_HINTS.items():
        if k in text:
            return v
    return "dot"


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    """머리말(제목:/부제:/작성자:/날짜:/스킨:) 추출 후 본문 반환."""
    meta: dict[str, str] = {}
    keys = {"제목": "title", "부제": "subtitle", "작성자": "author",
            "날짜": "date", "스킨": "skin", "이슈": "issue"}
    lines = text.splitlines()
    body_start = 0
    for i, ln in enumerate(lines):
        m = re.match(r"^\s*(제목|부제|작성자|날짜|스킨|이슈)\s*[:：]\s*(.+)$", ln)
        if m:
            meta[keys[m.group(1)]] = m.group(2).strip()
            body_start = i + 1
        elif ln.strip() == "" and meta:
            body_start = i + 1
            break
        elif meta:
            break
    return meta, "\n".join(lines[body_start:])


def split_items(lines: list[str]) -> list[Item]:
    """불릿/번호 줄들을 Item으로. '키워드: 설명' 또는 'Step 1) …' 지원."""
    items: list[Item] = []
    for raw in lines:
        ln = raw.strip()
        ln = re.sub(r"^[-*•·▪◦o]\s+", "", ln)
        step = ""
        ms = re.match(r"^(?:(\d+)[.)]\s*|Step\s*(\d+)\s*[.):]\s*)(.*)$", ln, re.I)
        if ms:
            num = ms.group(1) or ms.group(2)
            step = f"Step {num}"
            ln = ms.group(3).strip()
        if ":" in ln or "：" in ln:
            head, _, body = ln.replace("：", ":").partition(":")
            it = Item(heading=head.strip(), body=body.strip(), step_label=step)
        else:
            it = Item(heading=ln, step_label=step)
        it.icon = guess_icon(it.heading + it.body)
        items.append(it)
    return items


def infer_layout(title: str, body: str, items: list[Item]) -> Layout:
    """콘텐츠 모양 → 레이아웃 추론."""
    blob = f"{title} {body} " + " ".join(i.heading + i.body for i in items)

    # 명시 태그: [사진]/[좌우]/[아이콘]/[단계]/[그래프]/[카드]
    tag = re.search(r"\[(사진|좌우|아이콘|단계|타임라인|그래프|차트|카드)\]", title)
    if tag:
        return {"사진": Layout.PHOTO_FOCUS, "좌우": Layout.SPLIT,
                "아이콘": Layout.ICON_TRIPLE, "단계": Layout.TIMELINE,
                "타임라인": Layout.TIMELINE, "그래프": Layout.CHART_FOCUS,
                "차트": Layout.CHART_FOCUS, "카드": Layout.CARD_GRID}[tag.group(1)]

    has_steps = any(i.step_label for i in items)
    if has_steps or re.search(r"단계|과정|순서|절차|경위|경과", blob):
        if items:
            return Layout.TIMELINE
    if re.search(r"\d+\s*%|\d+\s*(명|건|개|원|점|위)|통계|수치|비교\s*표", blob):
        return Layout.CHART_FOCUS
    if len(items) >= 4:
        return Layout.CARD_GRID
    if 2 <= len(items) <= 3:
        return Layout.ICON_TRIPLE
    if re.search(r"사진|이미지|현장|모습|풍경|\[img", blob):
        return Layout.PHOTO_FOCUS
    return Layout.SPLIT
