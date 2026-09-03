"""HTML 슬라이드 덱 렌더러 — 발표노트 예시(네이비/흰 카드/골드 포인트) 톤 계승.

각 슬라이드는 1280×720(16:9) `.slide` 블록. 브라우저에서 바로 넘겨보거나
인쇄→PDF, 또는 크로미움으로 PNG 캡처해 미리보기로 쓴다.

입력: 아래 형태의 slide dict 리스트
  {kind: 'cover'|'content'|'closing',
   num: '3' | '', title, time, chips: [..], points: [..],
   lead: '' , footer: ''}
"""
from __future__ import annotations

import html as _h

# ── 예시에서 그대로 가져온 디자인 토큰 ──────────────────────────
CSS = """
*{box-sizing:border-box;margin:0;padding:0}
body{background:#5b6770;font-family:'Malgun Gothic','맑은 고딕','Apple SD Gothic Neo',
     -apple-system,sans-serif;color:#1f2a33;-webkit-font-smoothing:antialiased}
.deck{display:flex;flex-direction:column;align-items:center;gap:22px;padding:22px}
.slide{position:relative;width:1280px;height:720px;background:#f4f6f8;
       border-radius:6px;overflow:hidden;box-shadow:0 6px 24px rgba(0,0,0,.28)}
.pad{position:absolute;inset:0;padding:54px 64px;display:flex;flex-direction:column}

/* 헤더 */
.eb{display:flex;align-items:center;gap:16px}
.badge{width:46px;height:46px;border-radius:11px;background:#0b3a5b;color:#fff;
       font-size:22px;font-weight:800;display:flex;align-items:center;justify-content:center}
.htitle{font-size:29px;font-weight:800;color:#0b3a5b;letter-spacing:-.6px}
.time{position:absolute;top:56px;right:64px;background:#e8f2f9;color:#0b3a5b;
      font-size:15px;font-weight:700;padding:7px 18px;border-radius:16px}
.rule{width:64px;height:5px;background:#d9a400;border-radius:3px;margin:16px 0 20px 62px}

/* 칩 */
.chips{display:flex;gap:9px;flex-wrap:wrap;margin:0 0 26px 62px}
.chip{background:#eef3f7;color:#31637f;font-size:15px;font-weight:700;
      padding:7px 15px;border-radius:15px}

/* 핵심 포인트(진술 카드) */
.points{display:flex;flex-direction:column;gap:18px;margin-left:62px;max-width:1030px;
        flex:1;justify-content:center;padding-bottom:40px}
.pt{background:#fff;border:1px solid #e7ecf0;border-left:6px solid #0b3a5b;
    border-radius:12px;padding:20px 26px;box-shadow:0 2px 6px rgba(31,42,55,.06);
    font-size:22px;font-weight:600;color:#1f2a33;line-height:1.4}
.pt.gold{border-left-color:#d9a400}
.pt b,.pt .hl{background:#fff3c4;font-weight:800;padding:0 3px;border-radius:3px}
.lead{margin:6px 0 24px 62px;font-size:18px;color:#5b6770;max-width:1020px;line-height:1.55}

/* 표지 */
.cover{background:#0b3a5b;color:#fff}
.cover .bar{position:absolute;left:0;top:0;bottom:0;width:14px;background:#d9a400}
.cover .kick{position:absolute;top:120px;left:96px;font-size:19px;font-weight:700;
             color:#bcd9ee;letter-spacing:3px}
.cover h1{position:absolute;top:238px;left:94px;right:110px;font-size:60px;
          font-weight:800;line-height:1.14;letter-spacing:-1.2px;white-space:pre-line}
.cover .cvrule{position:absolute;left:98px;top:440px;width:120px;height:7px;background:#d9a400}
.cover .sub{position:absolute;left:98px;top:472px;right:120px;font-size:24px;color:#dbe9f4}
.cover .meta{position:absolute;left:98px;bottom:96px;display:flex;gap:12px}
.cover .meta div{background:rgba(255,255,255,.13);border-radius:8px;
                 padding:10px 18px;font-size:16px}

/* 마무리 */
.closing{background:#0b3a5b;color:#fff;display:flex;flex-direction:column;
         align-items:center;justify-content:center}
.closing .bar{position:absolute;left:0;top:0;bottom:0;width:14px;background:#d9a400}
.closing h1{font-size:56px;font-weight:800;letter-spacing:-1px;white-space:pre-line;
            text-align:center;line-height:1.2}
.closing .cvrule{width:120px;height:7px;background:#d9a400;margin:22px 0}
.closing .sub{font-size:22px;color:#dbe9f4}
.closing .meta{margin-top:34px;font-size:16px;color:#bcd9ee}

/* 푸터 */
.foot{position:absolute;left:64px;right:64px;bottom:30px;display:flex;
      justify-content:space-between;font-size:13px;color:#8a949c;
      border-top:1px solid #e2e7ec;padding-top:12px}

/* 인쇄/PDF: 슬라이드 1장 = 1페이지 */
@page{size:1280px 720px;margin:0}
@media print{
  body{background:#fff}
  .deck{gap:0;padding:0}
  .slide{border-radius:0;box-shadow:none;break-after:page;page-break-after:always}
  .slide:last-child{break-after:auto;page-break-after:auto}
}
"""


def _esc(t: str) -> str:
    return _h.escape(str(t or ""))


def _cover(s: dict) -> str:
    metas = "".join(f"<div>{_esc(m)}</div>" for m in s.get("meta", []) if m)
    return f"""<div class="slide cover"><div class="bar"></div>
      <div class="kick">{_esc(s.get('kicker','CHANGCHENET'))}</div>
      <h1>{_esc(s['title'])}</h1><div class="cvrule"></div>
      <div class="sub">{_esc(s.get('sub',''))}</div>
      <div class="meta">{metas}</div></div>"""


def _closing(s: dict) -> str:
    meta = _esc(s.get("meta", ""))
    return f"""<div class="slide closing"><div class="bar"></div>
      <h1>{_esc(s['title'])}</h1><div class="cvrule"></div>
      <div class="sub">{_esc(s.get('sub',''))}</div>
      <div class="meta">{meta}</div></div>"""


def _content(s: dict) -> str:
    time = f'<div class="time">{_esc(s["time"])}</div>' if s.get("time") else ""
    chips = "".join(f'<span class="chip">{_esc(c)}</span>' for c in s.get("chips", []))
    chips = f'<div class="chips">{chips}</div>' if chips else ""
    lead = f'<div class="lead">{_esc(s["lead"])}</div>' if s.get("lead") else ""
    pts = ""
    for i, p in enumerate(s.get("points", [])):
        gold = " gold" if i % 2 else ""
        pts += f'<div class="pt{gold}">{p}</div>'  # p may contain <b>
    pts = f'<div class="points">{pts}</div>' if pts else ""
    foot = s.get("footer", "")
    footer = (f'<div class="foot"><span>{_esc(foot)}</span>'
              f'<span>{_esc(s.get("page",""))}</span></div>') if foot else ""
    return f"""<div class="slide"><div class="pad">
      <div class="eb"><div class="badge">{_esc(s.get('num','•'))}</div>
        <div class="htitle">{_esc(s['title'])}</div></div>{time}
      <div class="rule"></div>{chips}{lead}{pts}{footer}</div></div>"""


def render(slides: list[dict], *, title: str = "제안 발표") -> str:
    body = []
    for s in slides:
        k = s.get("kind", "content")
        body.append(_cover(s) if k == "cover" else
                    _closing(s) if k == "closing" else _content(s))
    return (f"<!doctype html><html lang='ko'><head><meta charset='utf-8'>"
            f"<title>{_esc(title)}</title><style>{CSS}</style></head>"
            f"<body><div class='deck'>{''.join(body)}</div></body></html>")


def write(slides: list[dict], out_path: str, *, title: str = "제안 발표") -> str:
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(render(slides, title=title))
    return out_path


# ── 일반 Deck → 슬라이드 dict 어댑터 ─────────────────────────────
def from_deck(deck) -> list[dict]:
    """중립 Deck 을 HTML 덱 슬라이드 dict 로 변환한다."""
    from ..schema import Layout

    meta = [x for x in [getattr(deck, "author", ""), getattr(deck, "date", "")] if x]
    slides: list[dict] = []
    n = 0
    for s in deck.slides:
        if s.layout == Layout.COVER:
            slides.append(dict(kind="cover", kicker=(deck.author or "CHANGCHENET"),
                               title=s.title or deck.title, sub=s.subtitle or "",
                               meta=meta))
        elif s.layout == Layout.CLOSING:
            slides.append(dict(kind="closing", title=s.title or "감사합니다",
                               sub=s.subtitle or "", meta="  ·  ".join(meta)))
        else:
            n += 1
            chips, points = [], []
            for it in s.items[:6]:
                if it.body:
                    points.append(f"<b>{_esc(it.heading)}</b> — {_esc(it.body)}"
                                  if it.heading else _esc(it.body))
                elif it.heading:
                    chips.append(it.heading)
            if not points and s.body:
                points = [_esc(s.body)]
            slides.append(dict(kind="content", num=str(n),
                               title=s.title or f"슬라이드 {n}",
                               time="", chips=chips[:3], points=points[:4],
                               lead=s.subtitle or "", page=f"{n:02d}",
                               footer=deck.title))
    return slides


def build(deck, out_path: str, *, skin=None) -> str:
    """CLI 어댑터: Deck → HTML 덱 파일."""
    return write(from_deck(deck), out_path, title=deck.title)
