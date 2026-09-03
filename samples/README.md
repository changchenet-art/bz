# 샘플(템플릿) 모음 — 그동안 만든 결과물

각 HTML은 **자체 포함**(스타일 내장)이라 더블클릭하면 브라우저에서 바로 열립니다.
PDF가 필요하면 브라우저에서 열고 `Ctrl/Cmd + P → PDF로 저장`(용지 가로).

| 파일 | 종류 | 만든 방법(재생성) |
|---|---|---|
| `1_발표슬라이드_청주해양(네이비).html` | 발표 때 띄우는 슬라이드 덱 · 네이비 톤 | `python3 scripts/build_cheongju_draft.py` |
| `2_발표노트문서_청주해양(예시재현).html` | 발표노트 문서(배너+전략표+강점/미끼/참고) · 예시 포맷 재현 | `python3 scripts/build_cheongju_draft.py` |
| `3_수업PPT_갯벌(연파랑A4).html` | 초등 수업 PPT · A4 가로 연파랑(원고 스펙) | `python3 scripts/build_gaetbeol.py` |

## 재생성 / 수정
- 프로그램 본체: `ppt_auto/`  (파서 `parse/`, 렌더러 `render/`, 스킨 `skins/`)
- 갯벌 수업 PPT 이미지: `assets/갯벌_수업/images/` 에 넣으면 자동 임베드
- 결과물은 기본적으로 `output/`(저장소 제외)에 생성 → 필요한 것만 이 `samples/`로 복사해 공유

## CLI
    python -m ppt_auto gen -i 원고.txt  --engine html    # 발표 슬라이드
    python -m ppt_auto gen -i 노트.html --engine notes   # 발표노트 문서
    python -m ppt_auto gen -i 원고.xlsx --engine local --format both  # PPTX+PDF
