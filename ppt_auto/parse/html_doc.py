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


# ── 예시 발표노트(.card) 포맷 리치 파서 ─────────────────────────
def _inner(el) -> str:
    """요소의 안쪽 HTML을 <b> 강조만 남기고 공백 정리해 반환."""
    from bs4 import NavigableString, Tag
    out = []
    for c in el.children:
        if isinstance(c, NavigableString):
            out.append(str(c))
        elif isinstance(c, Tag):
            inner = c.decode_contents()
            if c.name in ("b", "strong"):
                out.append(f"<b>{inner}</b>")
            else:
                out.append(inner)
    return re.sub(r"\s+", " ", "".join(out)).strip()


def _lis(scope, selector) -> list[str]:
    box = scope.select_one(selector)
    if not box:
        return []
    return [_inner(li) for li in box.select("li") if _txt(li)]


def _parse_cards(soup, *, skin: str) -> Deck:
    """예시 발표노트 형식(.top 배너 + .strat 전략표 + .card N개)을 그대로 담는다."""
    top = soup.select_one(".top")
    title = _txt(top.select_one("h1")) if top and top.select_one("h1") else \
        (_txt(soup.title) if soup.title else "발표 노트")
    subtitle = _txt(top.select_one("p")) if top and top.select_one("p") else ""
    banner = [_txt(d) for d in top.select(".meta div")] if top else []

    deck = Deck(title=title, subtitle=subtitle, skin=skin, banner_meta=banner)

    # 전략지도 표
    strat = soup.select_one(".strat")
    if strat and strat.select_one("table"):
        rows = strat.select("table tr")
        for tr in rows[1:]:  # 헤더 제외
            cells = [_txt(td) for td in tr.find_all(["td", "th"])]
            if len(cells) >= 3:
                deck.strategy_rows.append(
                    {"slide": cells[0], "q": cells[1], "bait": cells[2]})
        deck.issue = _txt(strat.select_one("h3")) if strat.select_one("h3") else ""

    total = len(soup.select(".card"))
    for i, c in enumerate(soup.select(".card")):
        h2 = c.select_one(".tl h2") or c.select_one("h2")
        title_i = _clean_title(_txt(h2)) if h2 else f"슬라이드 {i}"
        tm = c.select_one(".time")
        chips = [_txt(x) for x in c.select(".chip")]
        points = [_inner(li) for li in c.select("ul.talk li") if _txt(li)]
        hook = _lis(c, ".hook")
        bait = _lis(c, ".bait")
        ref = _lis(c, ".ref")
        shot = "PLACEHOLDER" if c.select_one(".shot img, img") else ""

        layout = Layout.COVER if i == 0 else Layout.CARD_GRID
        s = Slide(layout=layout, title=title_i,
                  items=[Item(heading=ch, icon=guess_icon(ch)) for ch in chips[:3]],
                  time=_txt(tm) if tm else "",
                  points=points, hook=hook, bait=bait, ref=ref, shot=shot)
        # 발표자 노트(PDF 설명자료 호환): 스크립트=발표멘트 평문
        plain = re.sub(r"<[^>]+>", "", "  ".join(points))
        s.note = SlideNote(summary=title_i, must_know=[re.sub(r"<[^>]+>", "", h)
                           for h in hook[:3]], script=plain)
        s.image = "PLACEHOLDER" if shot else ""
        deck.slides.append(s)
    return deck


def parse(html: str, *, skin: str = DEFAULT_SKIN) -> Deck:
    soup = BeautifulSoup(html, "html.parser")

    # 예시 발표노트 포맷이면 리치 파서 사용
    if soup.select(".card"):
        return _parse_cards(soup, skin=skin)

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
