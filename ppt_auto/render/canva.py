"""Canva 출력 어댑터 (브리지).

Canva 실제 편집은 런타임에 Canva 커넥터(MCP: read-design / edit-design /
export-design)로 수행된다. 파이썬 프로그램은 네트워크 밖에서 도는 '두뇌'이므로,
여기서는 Deck을 Canva 레이아웃 키트에 흘려넣기 위한 **자동채우기 페이로드(JSON)**
와 **런북(markdown)** 을 만든다.

흐름:
  1. 스킨의 canva_design_id(레이아웃 키트) 확인
  2. build_payload(deck, skin) → 페이지별 placeholder 매핑 JSON
  3. (어시스턴트가) 커넥터로:
       copy-design(키트) → read-design(open_transaction) 로 locator 확인
       → edit-design 으로 텍스트/이미지 교체 → export-design(pptx/pdf)
"""
from __future__ import annotations

import json

from ..schema import Deck, Layout
from ..skins.registry import get as get_skin


def build_payload(deck: Deck, skin: str | None = None) -> dict:
    sk = get_skin(skin or deck.skin)
    pages = []
    for i, s in enumerate(deck.slides, start=1):
        fields = {
            "layout": s.layout.value,
            "title": s.title,
            "subtitle": s.subtitle,
            "body": s.body,
            "items": [{"heading": it.heading, "body": it.body,
                       "step_label": it.step_label} for it in s.items],
            "image": s.image,
        }
        if s.chart:
            fields["chart"] = {"kind": s.chart.kind,
                               "categories": s.chart.categories,
                               "series": s.chart.series}
        pages.append({"page_index": i, "fields": fields})
    return {
        "skin": sk.key,
        "canva_design_id": sk.canva_design_id,
        "deck_title": deck.title,
        "author": deck.author,
        "pages": pages,
    }


def build_runbook(deck: Deck, skin: str | None = None) -> str:
    sk = get_skin(skin or deck.skin)
    kit = sk.canva_design_id or "(이 스킨은 Canva 키트가 없습니다 — 로컬 렌더러 사용)"
    lines = [
        f"# Canva 자동채우기 런북 — {deck.title}",
        "",
        f"- 스킨: **{sk.ko_name}** (`{sk.key}`)",
        f"- 원본 레이아웃 키트: `{kit}`",
        f"- 슬라이드 수: {len(deck.slides)}",
        "",
        "## 커넥터 실행 순서",
        "1. `copy-design`으로 키트를 복제 → 새 디자인 ID 확보",
        "2. `read-design`(open_transaction=true)로 각 페이지 locator_id 확인",
        "3. 아래 페이지 매핑대로 `edit-design`으로 텍스트/이미지 교체",
        "4. `export-design`으로 PPTX·PDF 내보내기",
        "",
        "## 페이지 매핑",
    ]
    for i, s in enumerate(deck.slides, start=1):
        lines.append(f"- **p{i}** ({s.layout.value}): {s.title}")
        if s.body:
            lines.append(f"    - 본문: {s.body[:60]}...")
        for it in s.items:
            lines.append(f"    - {it.step_label or '항목'}: {it.heading} — {it.body}")
    return "\n".join(lines)


def build(deck: Deck, out_path: str, *, skin: str | None = None) -> str:
    """페이로드 JSON을 파일로 저장(런북도 옆에)."""
    payload = build_payload(deck, skin)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    runbook_path = out_path.rsplit(".", 1)[0] + "_runbook.md"
    with open(runbook_path, "w", encoding="utf-8") as f:
        f.write(build_runbook(deck, skin))
    return out_path
