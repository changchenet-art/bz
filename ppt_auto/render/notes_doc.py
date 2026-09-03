"""발표노트 문서 렌더러 — 예시(청주해양 발표노트) 포맷을 그대로 재현한다.

예시 파일의 CSS를 그대로 계승:
  · 상단 네이비 배너(.top) + 전략지도 표(.strat)
  · 슬라이드마다 카드(.card): 헤더 + 사진영역(.shot) + 발표멘트(ul.talk) +
    ★강점(.hook) + 🎣미끼(.bait) + 참고(.ref)
points/hook/bait/ref 는 <b> 강조를 포함한 HTML 조각이므로 그대로 주입한다.
"""
from __future__ import annotations

import html as _h

# 예시 파일에서 그대로 가져온 스타일(발표노트 톤의 준거)
CSS = """
*{box-sizing:border-box}
body{margin:0;background:#f4f6f8;font-family:'Malgun Gothic','맑은 고딕',-apple-system,sans-serif;color:#111;line-height:1.62}
.wrap{max-width:960px;margin:0 auto;padding:26px 16px 60px}
.top{background:#0b3a5b;color:#fff;border-radius:12px;padding:24px 28px;margin-bottom:18px}
.top h1{margin:0 0 6px;font-size:22px;letter-spacing:-.4px}
.top p{margin:0;font-size:13px;color:#bcd9ee}
.meta{display:flex;gap:10px;flex-wrap:wrap;margin-top:14px}
.meta div{background:rgba(255,255,255,.12);border-radius:6px;padding:6px 12px;font-size:12.5px}
.strat{background:#fff;border-radius:12px;padding:20px 24px;margin-bottom:22px;box-shadow:0 1px 3px rgba(0,0,0,.08)}
.strat h3{margin:0 0 4px;font-size:16px}
.strat p{margin:0 0 12px;font-size:12.5px;color:#5b6770}
table{width:100%;border-collapse:collapse;font-size:12.5px}
th{background:#eef3f7;color:#31637f;text-align:left;padding:7px 10px;font-size:12px}
td{border-bottom:1px solid #eef1f4;padding:7px 10px;vertical-align:top}
td.q{color:#0b3a5b;font-weight:700}
.card{background:#fff;border-radius:12px;box-shadow:0 1px 3px rgba(0,0,0,.08);margin-bottom:24px;overflow:hidden;page-break-inside:avoid}
.hdr{display:flex;align-items:center;justify-content:space-between;padding:10px 16px;border-bottom:1px solid #eef1f4}
.sn{background:#0b3a5b;color:#fff;font-size:11.5px;font-weight:700;letter-spacing:.4px;padding:4px 10px;border-radius:5px}
.hr{font-size:11px;color:#8a949c}
.shot{padding:14px 16px 6px;background:#fbfcfd}
.shot .ph{width:100%;height:250px;display:flex;align-items:center;justify-content:center;
          border:1.5px dashed #c7d4dd;border-radius:6px;color:#8a949c;font-size:13px;background:#fff}
.note{padding:14px 20px 20px}
.tl{display:flex;align-items:center;justify-content:space-between;gap:12px;border-left:4px solid #0b3a5b;padding-left:10px;margin-bottom:10px}
.tl h2{margin:0;font-size:16.5px;letter-spacing:-.3px}
.time{flex:none;background:#e8f2f9;color:#0b3a5b;font-size:12px;font-weight:700;padding:4px 12px;border-radius:14px;white-space:nowrap}
.chips{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:12px}
.chip{background:#eef3f7;color:#31637f;font-size:11.5px;font-weight:600;padding:4px 10px;border-radius:12px}
.badge{display:inline-block;background:#0b3a5b;color:#fff;font-size:11.5px;font-weight:700;padding:3px 12px;border-radius:4px;margin-bottom:8px}
ul.talk{margin:0 0 14px;padding-left:20px}
ul.talk li{margin-bottom:9px;font-size:14px}
ul.talk li b{background:#fff3c4;padding:0 2px;border-radius:2px}
.hook{background:#fff8e6;border:1px solid #f0dda8;border-left:4px solid #d9a400;border-radius:8px;padding:11px 16px;margin-bottom:10px}
.ht{font-size:12px;font-weight:700;color:#8a6a00;margin-bottom:5px}
.hook ul{margin:0;padding-left:18px}
.hook li{font-size:13.2px;color:#4a3c10;margin-bottom:5px}
.bait{background:#eef7f1;border:1px solid #c4e3d1;border-left:4px solid #2e8b57;border-radius:8px;padding:11px 16px;margin-bottom:10px}
.bt{font-size:12px;font-weight:700;color:#1f6b41;margin-bottom:5px}
.bait ul{margin:0;padding-left:18px}
.bait li{font-size:13.2px;color:#22422f;margin-bottom:5px}
.ref{background:#f7f9fa;border:1px solid #e7ecf0;border-radius:8px;padding:12px 16px}
.rt{font-size:12px;font-weight:700;color:#5b6770;margin-bottom:6px}
.ref ul{margin:0;padding-left:18px}
.ref li{font-size:12.8px;color:#3c464e;margin-bottom:6px}
.ref li b{color:#0b3a5b}
@media print{body{background:#fff} .card{box-shadow:none;border:1px solid #ddd}}
"""

HOOK_T = "★ 강점 — 여기서 못 박을 것"
BAIT_T = "미끼 — 이 슬라이드가 끌어낼 질문"
REF_T = "참고 — 질문 나오면 쓰는 근거"
STRAT_DESC = ("발표는 설명이 아니라 <b>질문 설계</b>다. 우리가 답을 준비한 질문이 "
              "나오도록 슬라이드마다 미끼를 심는다. 「끌어낼 질문」은 예상 질의응답집 번호와 같다.")


def _esc(t: str) -> str:
    return _h.escape(str(t or ""))


def _card(idx: int, total: int, s, doctitle: str) -> str:
    chips = "".join(f'<span class="chip">{_esc(i.heading)}</span>' for i in s.items)
    chips = f'<div class="chips">{chips}</div>' if chips else ""
    talk = "".join(f"<li>{p}</li>" for p in s.points)
    talk = f'<ul class="talk">{talk}</ul>' if talk else ""
    shot = ('<div class="shot"><div class="ph">📷 슬라이드 화면 (캡처 삽입 영역)</div></div>'
            if s.shot else "")
    time = f'<span class="time">{_esc(s.time)}</span>' if s.time else ""

    def box(cls, tcls, title, items):
        if not items:
            return ""
        lis = "".join(f"<li>{x}</li>" for x in items)
        return (f'<div class="{cls}"><div class="{tcls}">{title}</div>'
                f"<ul>{lis}</ul></div>")

    hook = box("hook", "ht", HOOK_T, s.hook)
    bait = box("bait", "bt", BAIT_T, s.bait)
    ref = box("ref", "rt", REF_T, s.ref)
    return f"""<div class="card">
      <div class="hdr"><span class="sn">SLIDE {idx} / {total}</span>
        <span class="hr">{_esc(doctitle)}</span></div>
      {shot}
      <div class="note">
        <div class="tl"><h2>{_esc(s.title)}</h2>{time}</div>
        {chips}<span class="badge">발표</span>
        {talk}{hook}{bait}{ref}
      </div></div>"""


def render(deck) -> str:
    metas = "".join(f"<div>{_esc(m)}</div>" for m in deck.banner_meta)
    # subtitle 안에 파이프로 붙은 메타가 있으면 pill 로 분해
    if deck.subtitle and "|" in deck.subtitle:
        for part in deck.subtitle.split("|"):
            part = part.strip()
            if part:
                metas = f"<div>{_esc(part)}</div>" + metas
        sub = ""
    else:
        sub = f"<p>{_esc(deck.subtitle)}</p>" if deck.subtitle else ""
    top = (f'<div class="top"><h1>{_esc(deck.title)}</h1>{sub}'
           f'<div class="meta">{metas}</div></div>')

    strat = ""
    if deck.strategy_rows:
        rows = "".join(
            f'<tr><td>{_esc(r.get("slide",""))}</td>'
            f'<td class="q">{_esc(r.get("q",""))}</td>'
            f'<td>{_esc(r.get("bait",""))}</td></tr>' for r in deck.strategy_rows)
        strat = (f'<div class="strat"><h3>전략 지도 — 어느 슬라이드가 어느 질문을 끌어내는가</h3>'
                 f'<p>{STRAT_DESC}</p><table>'
                 f'<tr><th>슬라이드</th><th>끌어낼 질문</th><th>미끼가 되는 말</th></tr>'
                 f"{rows}</table></div>")

    total = len(deck.slides)
    cards = "".join(_card(i + 1, total, s, deck.title)
                    for i, s in enumerate(deck.slides))
    return (f"<!doctype html><html lang='ko'><head><meta charset='utf-8'>"
            f"<title>{_esc(deck.title)}</title><style>{CSS}</style></head>"
            f'<body><div class="wrap">{top}{strat}{cards}</div></body></html>')


def build(deck, out_path: str, *, skin=None) -> str:
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(render(deck))
    return out_path
