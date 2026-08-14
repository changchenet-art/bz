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
    on_primary: str = "#FFFFFF"  # primary 위 텍스트


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
        palette=Palette(bg="#0F2A45", ink="#EAF2F8", primary="#FFFFFF",
                        secondary="#2E9CA6", accent="#2E9CA6", muted="#9DB4C8",
                        card="#173A5A", on_primary="#0F2A45"),
        heading_font="프리텐다드", body_font="맑은 고딕",
        best_for=["위기·부정이슈 대응", "사내·기관 보고"]),
    "mono_focus": Skin(
        key="mono_focus", ko_name="모노 포커스", mood="집중·단호·단계강조",
        palette=Palette(bg="#141517", ink="#F4F4F2", primary="#FFFFFF",
                        secondary="#E4443A", accent="#E4443A", muted="#9AA0A6",
                        card="#1F2124", on_primary="#141517"),
        heading_font="프리텐다드", body_font="맑은 고딕",
        best_for=["위기·부정이슈 대응", "핵심 하나 강조"]),
    "green_sustain": Skin(
        key="green_sustain", ko_name="그린 서스테인", mood="자연·지속가능·창체넷",
        palette=Palette(bg="#22402E", ink="#F1F4E8", primary="#FFFFFF",
                        secondary="#A7CF4F", accent="#8FB93E", muted="#A9BBA6",
                        card="#2E5540", on_primary="#22402E"),
        heading_font="나눔스퀘어", body_font="맑은 고딕",
        best_for=["교육·강의", "환경교육"]),
    "ocean_blue": Skin(
        key="ocean_blue", ko_name="오션 블루", mood="해양·시원·창체넷",
        palette=Palette(bg="#083140", ink="#EAF7FA", primary="#FFFFFF",
                        secondary="#2FD0DF", accent="#14B0C4", muted="#8FBCC8",
                        card="#0E4658", on_primary="#083140"),
        heading_font="프리텐다드", body_font="맑은 고딕",
        best_for=["교육·강의", "해양교육"]),
}

DEFAULT_SKIN = "beige_business"


def get(key: str) -> Skin:
    if key not in SKINS:
        raise KeyError(f"알 수 없는 스킨: {key!r}. 사용 가능: {', '.join(SKINS)}")
    return SKINS[key]


def list_skins() -> list[Skin]:
    return list(SKINS.values())
