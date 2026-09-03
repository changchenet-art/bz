"""스킨 레지스트리 — 레이아웃은 동일, 옷(색·폰트·분위기)만 교체.

각 스킨은:
  - palette: 로컬 PPTX 렌더러가 쓰는 색
  - fonts: 제목/본문 글꼴 (설치 안 되어 있으면 뷰어 기본으로 대체)
  - canva_design_id: Canva 출력 경로에서 복제·자동채우기할 원본 레이아웃 키트

Canva 키트 4종은 모두 동일한 9페이지 구조를 가진 '레이아웃 키트'다.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Palette:
    bg: str          # 슬라이드 배경
    ink: str         # 본문 텍스트
    primary: str     # 제목·강조 1
    secondary: str   # 강조 2
    accent: str      # 포인트(단계 번호, 바)
    muted: str       # 보조 텍스트
    card: str        # 카드/박스 배경
    on_primary: str = "#FFFFFF"  # primary(네이비) 위 텍스트
    card_line: str = "#E7ECF0"   # 흰 카드 테두리
    soft: str = "#EEF3F7"        # 칩·표 헤더 등 옅은 톤 배경
    soft_ink: str = "#31637F"    # 옅은 톤 위 텍스트
    highlight: str = "#FFF3C4"   # 키워드 형광 하이라이트


@dataclass
class Skin:
    key: str
    ko_name: str
    mood: str
    palette: Palette
    heading_font: str = "맑은 고딕"
    body_font: str = "맑은 고딕"
    canva_design_id: str = ""      # Canva 레이아웃 키트 원본 (있으면 Canva 경로 사용 가능)
    best_for: list[str] = field(default_factory=list)


SKINS: dict[str, Skin] = {
    # ── Canva 키트 4종에서 도출 ──────────────────────────────
    "pastel_cute": Skin(
        key="pastel_cute", ko_name="파스텔 귀여운", mood="밝고 친근·교육",
        palette=Palette(bg="#FBF7EE", ink="#3A3F45", primary="#2E3440",
                        secondary="#5B7FB9", accent="#7FB77E", muted="#8A8F98",
                        card="#5B7FB9", on_primary="#FFFFFF"),
        heading_font="Gmarket Sans", body_font="맑은 고딕",
        canva_design_id="DAHSR7mImrc",
        best_for=["교육·강의", "어린이·청소년", "친근한 안내"]),
    "beige_business": Skin(
        key="beige_business", ko_name="베이지 심플 비즈니스", mood="깔끔·차분·보고",
        palette=Palette(bg="#F5EFE1", ink="#3B3B3B", primary="#2B2B2B",
                        secondary="#C9A24B", accent="#E6C560", muted="#8C8577",
                        card="#4A4A4A", on_primary="#FFFFFF"),
        heading_font="나눔스퀘어", body_font="맑은 고딕",
        canva_design_id="DAHSR8I8UMk",
        best_for=["사내·기관 보고", "제안·발표", "격식 있는 설명"]),
    "white_blue_minimal": Skin(
        key="white_blue_minimal", ko_name="화이트·블루 미니멀", mood="정갈·신뢰·설명",
        palette=Palette(bg="#FFFFFF", ink="#2A2E35", primary="#2C3E9E",
                        secondary="#5B6BD6", accent="#3B53C8", muted="#7A8090",
                        card="#EEF1FB", on_primary="#FFFFFF"),
        heading_font="프리텐다드", body_font="맑은 고딕",
        canva_design_id="DAHSRzk9TEA",
        best_for=["설명·안내", "인포그래픽", "무난한 전천후"]),
    "blue_modern": Skin(
        key="blue_modern", ko_name="블루톤 모던", mood="산뜻·전문·제안",
        palette=Palette(bg="#FFFFFF", ink="#2B3038", primary="#2F4EA1",
                        secondary="#4B79C4", accent="#2F4EA1", muted="#8890A0",
                        card="#EDF1F8", on_primary="#FFFFFF"),
        heading_font="프리텐다드", body_font="맑은 고딕",
        canva_design_id="DAHSR40VjII",
        best_for=["제안·발표", "비즈니스", "산뜻한 보고"]),

    # ── 신규 보완(컨셉 보드) — 로컬 전용, Canva ID 없음 ─────────
    "deep_navy": Skin(
        key="deep_navy", ko_name="딥 네이비 코퍼레이트", mood="신뢰·안정·위기대응",
        palette=Palette(bg="#FFFFFF", ink="#1E2A38", primary="#12314F",
                        secondary="#2E7D8A", accent="#2E9CA6", muted="#6B7A88",
                        card="#12314F", on_primary="#FFFFFF"),
        heading_font="프리텐다드", body_font="맑은 고딕",
        best_for=["위기·부정이슈 대응", "사내·기관 보고"]),
    "mono_focus": Skin(
        key="mono_focus", ko_name="모노 포커스", mood="집중·단호·단계강조",
        palette=Palette(bg="#FFFFFF", ink="#1A1C1F", primary="#1A1C1F",
                        secondary="#C8392F", accent="#E4443A", muted="#7A8087",
                        card="#26282B", on_primary="#FFFFFF"),
        heading_font="프리텐다드", body_font="맑은 고딕",
        best_for=["위기·부정이슈 대응", "핵심 하나 강조"]),
    "green_sustain": Skin(
        key="green_sustain", ko_name="그린 서스테인", mood="자연·지속가능·창체넷",
        palette=Palette(bg="#FFFFFF", ink="#24352A", primary="#2F7D4F",
                        secondary="#6E9E2E", accent="#8FB93E", muted="#7C8A78",
                        card="#2F7D4F", on_primary="#FFFFFF"),
        heading_font="나눔스퀘어", body_font="맑은 고딕",
        best_for=["교육·강의", "환경교육"]),
    "ocean_blue": Skin(
        key="ocean_blue", ko_name="오션 블루", mood="해양·시원·창체넷",
        palette=Palette(bg="#FFFFFF", ink="#123543", primary="#0D6E8C",
                        secondary="#0E8CA0", accent="#14B0C4", muted="#6E8A94",
                        card="#0D6E8C", on_primary="#FFFFFF"),
        heading_font="프리텐다드", body_font="맑은 고딕",
        best_for=["교육·강의", "해양교육"]),

    # ── 발표노트 예시 팔레트를 그대로 옮긴 정본 스킨 ─────────────
    #    밝은 회색 배경 + 흰 카드(그림자) + 네이비 헤더 + 골드/그린 포인트
    "report_navy": Skin(
        key="report_navy", ko_name="리포트 네이비", mood="정갈·신뢰·제안발표",
        palette=Palette(bg="#F4F6F8", ink="#1F2A33", primary="#0B3A5B",
                        secondary="#31637F", accent="#D9A400", muted="#5B6770",
                        card="#FFFFFF", on_primary="#FFFFFF"),
        heading_font="맑은 고딕", body_font="맑은 고딕",
        best_for=["제안·발표", "사내·기관 보고", "격식 있는 설명"]),
}

DEFAULT_SKIN = "report_navy"


def get(key: str) -> Skin:
    if key not in SKINS:
        raise KeyError(f"알 수 없는 스킨: {key!r}. 사용 가능: {', '.join(SKINS)}")
    return SKINS[key]


def list_skins() -> list[Skin]:
    return list(SKINS.values())
