# ppt_auto — 원고 → PPT + PDF 설명자료 자동화

부정 이슈나 원고를 넣으면 **가독성 높은 발표용 PPT**와, 그 아래 **슬라이드 노트를
모은 PDF 설명자료**(핵심 요약 · 꼭 알아야 할 것 · "안녕하세요…" 발표 스크립트)를
자동으로 만들어 줍니다.

```
[원고]  ─파싱→  [Deck]  ─렌더→  PPTX (로컬 스킨 또는 Canva)
                   └─노트생성→  PDF 설명자료
```

핵심 아이디어: **`[레이아웃 스키마 1개] × [스킨 N개]`**.
레이아웃(무엇을 채울지)은 고정, 옷(색·폰트·분위기)만 갈아입습니다.

---

## 설치

```bash
pip install -r requirements.txt   # python-pptx, reportlab, openpyxl
```

## 빠른 시작

```bash
# 1) 자유 텍스트/마크다운 원고 → PPT + PDF
python -m ppt_auto gen -i examples/sample.md --skin green_sustain

# 2) 엑셀 양식으로 정확히 제어
python -m ppt_auto template -o templates/입력양식.xlsx   # 빈칸 채우기 양식 생성
python -m ppt_auto gen -i templates/입력양식.xlsx --skin white_blue_minimal

# 3) 부정 이슈 + 원고 세트 → 차분한 대응 브리핑
python -m ppt_auto gen --issue examples/issue.txt --manuscript examples/manuscript.md

# 스킨 목록
python -m ppt_auto skins
```

출력은 `output/`에 `<이름>.pptx`, `<이름>_설명자료.pdf`로 저장됩니다.

---

## 9가지 레이아웃 (파스텔 레이아웃 키트에서 도출)

| 레이아웃 | 언제 쓰나 |
|---|---|
| 표지 / 목차 / 마무리 | 시작·개요·종료 (자동 생성) |
| 사진 중심형 | 사진으로 주제·분위기 (여행·체험·실험결과) |
| 좌우 분할형 | 설명 중심, 개념·이론 소개 |
| 아이콘 3분할형 | 비교·특징 정리·요약 |
| 타임라인/단계형 | 순서·과정 (실험단계·활동순서) — 클릭 시 단계별 등장 |
| 그래프/비주얼 | 조사결과·통계·수치 (실제 차트 렌더링) |
| 카드/그리드형 | 여러 항목·사례를 한눈에 — 클릭 시 하나씩 등장 |

자유 텍스트에서는 내용 모양으로 레이아웃을 **자동 추론**하고, 제목에 `[사진]`
`[좌우]` `[아이콘]` `[단계]` `[그래프]` `[카드]` 태그로 **직접 지정**할 수도 있습니다.

## 스킨

Canva 레이아웃 키트 4종 + 보완 4종:

| 키 | 이름 | 성격 | Canva 키트 |
|---|---|---|---|
| `pastel_cute` | 파스텔 귀여운 | 교육·친근 | ✔ |
| `beige_business` | 베이지 심플 비즈니스 | 보고·발표 | ✔ |
| `white_blue_minimal` | 화이트·블루 미니멀 | 설명·전천후 | ✔ |
| `blue_modern` | 블루톤 모던 | 제안·비즈니스 | ✔ |
| `deep_navy` | 딥 네이비 | 위기·부정이슈 대응 | |
| `mono_focus` | 모노 포커스 | 핵심 하나 강조 | |
| `green_sustain` | 그린 서스테인 | 환경교육 | |
| `ocean_blue` | 오션 블루 | 해양교육 | |

## 출력 엔진 (`--engine`)

- `local` (기본): **python-pptx**로 스킨을 직접 그려 `.pptx` 생성. 오프라인·반복·대량.
- `canva`: Canva 레이아웃 키트에 흘려넣기 위한 **자동채우기 페이로드(JSON)+런북**
  생성. 실제 채우기·내보내기는 Canva 커넥터(read-design/edit-design/export-design)로
  수행 — 귀여운 원본 디자인을 100% 그대로 유지.

---

## 입력 형식

### 자유 텍스트 / 마크다운
```
제목: 우리 동네 자원순환 캠페인
부제: 함께 만드는 깨끗한 마을
작성자: 창체넷 환경교육팀
스킨: green_sustain

## 추진 배경
본문 문단...

## 3대 실천 방향
- 분리배출: 종류별로 정확하게
- 다회용기: 다시 쓰는 습관
- 자원순환: 새 쓰임 더하기

## 참여 성과 [그래프]
정확도가 크게 좋아졌습니다.
- 정확도: 62,78,91
```

### 엑셀 (.xlsx)
`layout | title | subtitle | body | items | image | chart_kind | chart_categories |
chart_series | note_summary | note_must | note_script | reveal` — 1행 = 1슬라이드.
`template` 명령으로 예시가 채워진 양식을 만들 수 있습니다.

### 부정 이슈 + 원고
`--issue`(이슈 원문) + `--manuscript`(대응 원고). "사안 개요 → (원고 섹션) →
마무리" 구성으로 차분한 대응 브리핑을 짭니다.

---

## 구조

```
ppt_auto/
  schema.py            # Deck/Slide/Item/ChartSpec/SlideNote (중립 데이터)
  layouts.py           # 9개 레이아웃 메타 + 활용 상황
  notes.py             # 발표자 노트 자동 생성
  parse/
    common.py          # 레이아웃 추론·항목 분리
    freetext.py        # 자유 텍스트 → Deck
    excel.py           # 엑셀 양식 → Deck (+양식 생성)
    issue.py           # 부정 이슈+원고 → 대응 브리핑
  render/
    pptx_local.py      # python-pptx 렌더러 (+클릭 등장 애니메이션)
    pdf_notes.py       # reportlab 한글 PDF 설명자료
    canva.py           # Canva 자동채우기 페이로드/런북
  skins/registry.py    # 스킨(색·폰트·Canva 키트 ID) 카탈로그
  cli.py               # 명령행 인터페이스
```

## 알려진 한계 / 다음 단계

- 로컬 렌더러는 사진 자리에 **자리표 박스**를 넣습니다(이미지 경로를 주면 삽입하도록
  확장 예정).
- 클릭 등장 애니메이션은 PowerPoint에서 동작합니다(일부 뷰어는 미지원).
- Canva 엔진의 실제 채우기·내보내기는 커넥터 런타임에서 수행합니다(런북 참고).
- 노트 스크립트는 템플릿 기반이며, 원하면 상위에서 LLM으로 교체할 수 있습니다.
