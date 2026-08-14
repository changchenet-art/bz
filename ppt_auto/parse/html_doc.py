"""HTML 자료 → Deck.

발표 노트/제안서 형태의 HTML을 슬라이드로 변환한다.
  - <section> (없으면 <h2> 블록) 하나 = 슬라이드 하나
  - 제목: 섹션의 h1/h2/h3
  - 발표 스크립트: class 에 talk/script/speak/발표 가 있는 요소
  - 항목: <li> 또는 class 에 chip/keyword 가 있는 요소
  - 강조(꼭 알아야 할 것): class 에 hook/강점/key 가 있는 요소
레이아웃은 내용 모양으로 자동 추론. 이미지는 자리표 처리.
"""
from __future__ import annotations

import re

from bs4 import BeautifulSoup

from ..schema import Deck, Item, Layout, SlideNote, Slide
from ..skins.registry import DEFAULT_SKIN
from .common import guess_icon, infer_layout

_TALK = re.compile(r"talk|script|speak|발표|멘트|나레이션", re.I)
_KEY = re.compile(r"hook|강점|핵심|key|중요", re.I)
_CHIP = re.compile(r"chip|keyword|키워드|badge|tag", re.I)
_SKIP = re.compile(r"hdr|\bsn\b|slide-?no|번호|time|badge|ref|bait|미끼", re.I)


def _txt(el) -> str:
    return re.sub(r"\s+", " ", el.get_text(" ", strip=True)).strip()


def _classes(el) -> str:
    return " ".join(el.get("class", []))


def _clean_title(t: str) -> str:
    t = re.sub(r"^\s*(SLIDE\s*\d+.*?|\d+\s*/\s*\d+.*?)$", "", t, flags=re.I).strip()
    return t


def parse(html: str, *, skin: str = DEFAULT_SKIN) -> Deck:
    soup = BeautifulSoup(html, "html.parser")

    title = ""
    if soup.title and _txt(soup.title):
        title = _txt(soup.title)
    if soup.h1:
        title = _txt(soup.h1) or title
    title = re.sub(r"^발표\s*노트\s*[·•]\s*", "", title).strip() or "발표 자료"

    deck = Deck(title=title, skin=skin)

    sections = soup.find_all("section")
    if not sections:
        # section 이 없으면 h2 기준으로 가른다
        sections = []
        for h2 in soup.find_all(["h2"]):
            sections.append(h2)

    for idx, sec in enumerate(sections):
        # 제목
        head = sec.find(["h1", "h2", "h3"]) if hasattr(sec, "find") else None
        stitle = _clean_title(_txt(head)) if head else ""

        # 발표 스크립트
        script_parts = []
        for el in sec.find_all(True):
            if _TALK.search(_classes(el)):
                tx = _txt(el)
                if tx and tx not in script_parts:
                    script_parts.append(tx)
        script = "  ".join(script_parts)

        # 꼭 알아야 할 것
        must = []
        for el in sec.find_all(True):
            if _KEY.search(_classes(el)):
                tx = _txt(el)
                if tx:
                    must.append(re.sub(r"^★\s*", "", tx))

        # 항목: chip 우선, 없으면 li
        items: list[Item] = []
        seen: set[str] = set()
        for el in sec.find_all(True):
            cls = _classes(el)
            if not (_CHIP.search(cls) and not _SKIP.search(cls)):
                continue
            # 컨테이너(내부에 또 다른 chip 이 있는 래퍼: 예 .chips)는 건너뛰고
            # 리프 칩만 잡아 '전체문장 + 개별칩' 중복을 막는다.
            if any(d is not el and _CHIP.search(_classes(d))
                   for d in el.find_all(True)):
                continue
            tx = _txt(el)
            if tx and len(tx) < 40 and tx not in seen:
                seen.add(tx)
                items.append(Item(heading=tx, icon=guess_icon(tx)))
        if not items:
            for li in sec.find_all("li"):
                tx = _txt(li)
                if not tx:
                    continue
                if ":" in tx or "：" in tx:
                    h, _, b = tx.replace("：", ":").partition(":")
                    items.append(Item(heading=h.strip(), body=b.strip(),
                                      icon=guess_icon(tx)))
                else:
                    items.append(Item(heading=tx[:60], icon=guess_icon(tx)))

        # 본문: 짧은 문단(스크립트/항목 제외)
        body = ""
        for p in sec.find_all("p"):
            if _TALK.search(_classes(p)) or _KEY.search(_classes(p)):
                continue
            tx = _txt(p)
            if tx:
                body = tx
                break

        has_img = sec.find("img") is not None
        layout = (Layout.COVER if idx == 0 else
                  infer_layout(stitle, body, items))
        if idx == 0:
            layout = Layout.COVER
        elif has_img and layout == Layout.SPLIT:
            layout = Layout.PHOTO_FOCUS

        s = Slide(layout=layout, title=stitle or f"슬라이드 {idx+1}",
                  body=body, items=items[:6])
        if layout in (Layout.PHOTO_FOCUS, Layout.SPLIT):
            s.image = "PLACEHOLDER"
        s.note = SlideNote(summary=stitle, must_know=must[:4], script=script)
        deck.slides.append(s)

    # 표지 제목 보정
    if deck.slides and deck.slides[0].layout == Layout.COVER:
        deck.slides[0].title = deck.title
        deck.slides[0].subtitle = deck.slides[0].subtitle or ""

    # 마무리 슬라이드가 없으면 추가
    if not any(s.layout == Layout.CLOSING for s in deck.slides):
        deck.slides.append(Slide(layout=Layout.CLOSING, title="감사합니다"))
    return deck


def parse_file(path: str, *, skin: str = DEFAULT_SKIN) -> Deck:
    with open(path, encoding="utf-8", errors="replace") as f:
        return parse(f.read(), skin=skin)
