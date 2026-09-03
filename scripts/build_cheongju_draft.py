"""청주해양 제안발표 초안: 예시 HTML → 예시 톤 HTML 덱 + PNG 미리보기."""
import os
import re
import sys

from bs4 import BeautifulSoup

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ppt_auto.render import html_deck  # noqa: E402
from ppt_auto.parse import html_doc as p_html  # noqa: E402
from ppt_auto.render import notes_doc as r_notes  # noqa: E402

SRC = "examples/청주해양_발표노트.html"
OUT_HTML = "output/청주해양_제안발표.html"
OUT_NOTES = "output/청주해양_발표노트.html"
FOOTER = "국립청주해양과학관 전시운영 위탁 · 제안발표"

# 슬라이드에 올리지 않을 지문/군더더기
_DROP = re.compile(r"본다|쉬고|외워서|슬라이드를|말한다|안녕하십니까")
_MARK = re.compile(r"^[━\-\s]*(첫째|둘째|셋째|넷째)[━\-\s]*$")


def _clean(t: str) -> str:
    return re.sub(r"\s+", " ", t).strip(" .·—-")


def curate_points(card, limit=3):
    pts, seen = [], set()
    for b in card.select("ul.talk li b"):
        t = _clean(b.get_text(" ", strip=True))
        if not t or len(t) < 3 or len(t) > 46:
            continue
        if _DROP.search(t) or _MARK.match(t):
            continue
        if t in seen:
            continue
        seen.add(t)
        pts.append(t)
        if len(pts) >= limit:
            break
    return pts


def main():
    soup = BeautifulSoup(open(SRC, encoding="utf-8", errors="replace").read(),
                         "html.parser")
    cards = soup.select(".card")
    slides = []

    # 표지
    slides.append(dict(kind="cover", kicker="㈜ 창체넷 · CHANGCHENET",
                       title="국립청주해양과학관\n전시운영 위탁 제안",
                       sub="바다를 아는 사람, 바다를 설명해 온 회사",
                       meta=["제안발표 · 20분", "2026", "㈜창체넷"]))

    for i, c in enumerate(cards):
        h2 = c.select_one(".tl h2")
        title = _clean(h2.get_text(strip=True)) if h2 else f"슬라이드 {i}"
        if i == 0:  # 표지 카드는 위에서 처리
            continue
        if "부록" in title:  # 부록(잘라낼 순서)은 생략
            continue
        tm = c.select_one(".time")
        time = tm.get_text(strip=True) if tm else ""
        chips = [x.get_text(strip=True) for x in c.select(".chip")][:3]
        pts = curate_points(c, limit=4 if i == 1 else 3)
        points = [f"<b>{html_deck._esc(p)}</b>" if j == 0 else html_deck._esc(p)
                  for j, p in enumerate(pts)]
        slides.append(dict(kind="content", num=str(i), title=title, time=time,
                           chips=chips, points=points, footer=FOOTER,
                           page=f"{i:02d}"))

    # 마무리
    slides.append(dict(kind="closing", title="바다를 여는 첫해,\n함께 하겠습니다",
                       sub="공정채용 · 무결원 운영 · 본사 밀착지원 · 지역 네트워크",
                       meta="㈜창체넷 · 국립청주해양과학관 전시운영 위탁 제안"))

    os.makedirs("output", exist_ok=True)
    html_deck.write(slides, OUT_HTML, title="국립청주해양과학관 전시운영 위탁 제안")
    print(f"발표 슬라이드 덱: {OUT_HTML}  (슬라이드 {len(slides)}장)")

    # 발표노트 문서(예시 포맷 재현) — 리치 파서로 원본 그대로
    deck = p_html.parse_file(SRC, skin="report_navy")
    r_notes.build(deck, OUT_NOTES)
    print(f"발표노트 문서: {OUT_NOTES}  (카드 {len(deck.slides)}장)")
    return slides


if __name__ == "__main__":
    main()
