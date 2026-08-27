# 창체넷 네이버 블로그 자동 발행

주 2~3회 블로그 발행을 위한 원고 저장소와 발행 스크립트입니다.

## 폴더 구조

```
blog/
├── posts/      발행 원고 (YYYY-MM-DD_섹션_주제.md)
├── scripts/    naver_publish.py — 네이버 블로그 글쓰기 API 발행
└── README.md
```

## 발행 로테이션

| 요일 | 섹션 | 대상 독자 |
|------|------|-----------|
| 월요일 | 📚 교육 콘텐츠 소개 | 교원, 교육 담당 기관 |
| 수요일 | 🌱 환경·기후 교육 ↔ 🌊 해양교육 (격주 교대) | 교사, 학부모 |
| 금요일 | 🏢 창체넷 소식 | 협력 기관, 교육청, 학교 |

## 원고 형식

`posts/*.md` 는 front matter + 고정 섹션 구조를 따릅니다. 발행 스크립트가 이 구조를
그대로 파싱하므로 섹션 제목(`# 제목`, `# 본문`, `# 해시태그`)은 바꾸지 않습니다.

- 제목: 30자 이내, 검색 키워드 포함
- 본문: 1200~1500자, `■` 로 시작하는 소제목 3~4개
- 해시태그: 10개
- `status`: `draft` → 사용자 확인 후 `approved` → 발행되면 `published`

## 발행 방법

```bash
# 1) 변환 결과만 미리 확인 (토큰 불필요)
python3 blog/scripts/naver_publish.py --dry-run blog/posts/2026-08-27_*.md

# 2) 원고 확인 후 front matter의 status 를 approved 로 변경

# 3) 실제 발행
export NAVER_ACCESS_TOKEN=...      # developers.naver.com 에서 발급한 OAuth 2.0 접근 토큰
export NAVER_CATEGORY_NO=...       # 선택
python3 blog/scripts/naver_publish.py blog/posts/2026-08-27_*.md
```

## 주의사항

- 네이버 블로그 글쓰기 API는 OAuth 2.0 접근 토큰이 필요하며 토큰에는 유효기간이 있습니다.
  만료되면 developers.naver.com 에서 재발급합니다.
- API로는 본문에 이미지를 넣을 수 없습니다. 발행 후 네이버 에디터에서 직접 올립니다.
- 태그는 API 파라미터로 안정적으로 전달되지 않아 본문 끝에 해시태그 문단으로 붙입니다.
- 접근 토큰은 절대 저장소에 커밋하지 않습니다. 환경변수로만 전달합니다.
