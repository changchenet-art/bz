#!/usr/bin/env python3
"""네이버 블로그 발행 스크립트.

포스트 마크다운(blog/posts/*.md)을 읽어 네이버 블로그 글쓰기 API로 발행한다.
표준 라이브러리만 사용한다.

필요한 환경변수:
  NAVER_ACCESS_TOKEN   네이버 로그인 OAuth 2.0 접근 토큰 (필수)
  NAVER_CATEGORY_NO    블로그 카테고리 번호 (선택)

사용:
  NAVER_ACCESS_TOKEN=xxx python3 blog/scripts/naver_publish.py blog/posts/2026-08-27_*.md
  python3 blog/scripts/naver_publish.py --dry-run blog/posts/2026-08-27_*.md

참고:
  - 네이버 블로그 글쓰기 API는 본문에 이미지를 넣을 수 없다. 이미지는 발행 후
    네이버 에디터에서 직접 올린다.
  - 태그는 API 파라미터로 안정적으로 전달되지 않아, 본문 마지막에 해시태그
    문단으로 붙여 발행한다.
"""

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

API_URL = "https://openapi.naver.com/blog/writePost.json"


def parse_post(path):
    """마크다운 포스트를 {title, body, tags, front} 로 파싱한다."""
    text = open(path, encoding="utf-8").read()

    front = {}
    if text.startswith("---\n"):
        end = text.index("\n---\n", 3)
        for line in text[4:end].splitlines():
            if ":" in line and not line.lstrip().startswith("#"):
                k, v = line.split(":", 1)
                front[k.strip()] = v.split("#")[0].strip().strip('"')
        text = text[end + 5:]

    def section(name):
        m = re.search(rf"^# {name}\n(.*?)(?=^# |\Z)", text, re.S | re.M)
        return m.group(1).strip() if m else ""

    title = section("제목")
    body = section("본문")
    tags = [t for t in section("해시태그").split() if t.startswith("#")]

    if not title or not body:
        sys.exit(f"[에러] 제목 또는 본문 섹션을 찾지 못했습니다: {path}")
    if len(title) > 30:
        print(f"[경고] 제목이 30자를 넘습니다 ({len(title)}자). SEO 권장은 30자 이내입니다.")

    return {"title": title, "body": body, "tags": tags, "front": front}


def to_html(body, tags):
    """본문 마크다운을 네이버 에디터가 받아들이는 단순 HTML로 변환한다."""
    parts = []
    for para in [p.strip() for p in body.split("\n\n") if p.strip()]:
        if para.startswith("■"):
            parts.append(f"<p><b>{para}</b></p>")
        else:
            parts.append("<p>" + para.replace("\n", "<br>") + "</p>")
    if tags:
        parts.append("<p>" + " ".join(tags) + "</p>")
    return "\n".join(parts)


def publish(post, token, category_no=None):
    data = {"title": post["title"], "contents": to_html(post["body"], post["tags"])}
    if category_no:
        data["categoryNo"] = category_no

    req = urllib.request.Request(
        API_URL,
        data=urllib.parse.urlencode(data).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")
        sys.exit(f"[에러] 발행 실패 (HTTP {e.code}): {detail}\n"
                 "토큰이 만료되었을 수 있습니다. developers.naver.com 에서 재발급하세요.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("post", help="발행할 마크다운 파일 경로")
    ap.add_argument("--dry-run", action="store_true", help="발행하지 않고 변환 결과만 출력")
    args = ap.parse_args()

    post = parse_post(args.post)

    print(f"제목: {post['title']}")
    print(f"본문: {len(post['body'])}자")
    print(f"태그: {' '.join(post['tags'])}\n")

    if args.dry_run:
        print(to_html(post["body"], post["tags"]))
        return

    if post["front"].get("status") != "approved":
        sys.exit("[중단] front matter의 status가 'approved'가 아닙니다. "
                 "사용자 확인 후 approved 로 바꾸고 다시 실행하세요.")

    token = os.environ.get("NAVER_ACCESS_TOKEN")
    if not token:
        sys.exit("[중단] NAVER_ACCESS_TOKEN 환경변수가 없습니다.")

    result = publish(post, token, os.environ.get("NAVER_CATEGORY_NO"))
    print("발행 완료:", json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
