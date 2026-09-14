# -*- coding: utf-8 -*-
"""원고를 네이버 에디터에 바로 붙여넣을 수 있는 HTML로 내보낸다.

발행 API를 쓸 수 없는 환경에서 손으로 올릴 때 쓴다. 브라우저로 열어 본문 영역을
전체 선택(Ctrl+A 대신 본문만 드래그) 후 복사해 네이버 에디터에 붙여넣으면
굵은 글씨와 줄바꿈이 그대로 유지된다.

사용:
  python3 blog/scripts/export_html.py blog/posts/*.md --out blog/export/
"""
import argparse
import base64
import html as html_mod
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from naver_publish import parse_post, to_html   # 발행 스크립트와 같은 변환기를 쓴다

def embed_images(body_html):
    """![캡션](경로) 를 실제 그림이 박힌 <img> 로 바꾼다.

    네이버 에디터에 붙여넣을 때 그림이 함께 넘어가도록 파일을 base64 로 심는다.
    붙여넣기가 안 먹는 경우를 대비해 캡션에 원본 파일명을 남긴다.
    """
    from PIL import Image

    def one(m):
        cap, path = m.group(1), m.group(2)
        if not os.path.exists(path):
            return '<p style="color:#c00">[이미지 없음: %s]</p>' % html_mod.escape(path)
        im = Image.open(path)
        if im.mode in ("RGBA", "P"):
            im = im.convert("RGB")
        w, h = im.size
        if max(w, h) > 900:                      # 붙여넣기 부담을 줄인다
            k = 900 / max(w, h)
            im = im.resize((round(w * k), round(h * k)), Image.LANCZOS)
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=82, optimize=True)
        b64 = base64.b64encode(buf.getvalue()).decode()
        return ('<p><img src="data:image/jpeg;base64,%s" alt="%s" '
                'style="max-width:100%%;height:auto;border-radius:6px;"></p>'
                '<p style="font-size:13px;color:#888;text-align:center;margin-top:-8px">'
                '%s <span style="color:#bbb">· %s</span></p>'
                % (b64, html_mod.escape(cap), html_mod.escape(cap),
                   html_mod.escape(os.path.basename(path))))

    return re.sub(r"<p>!\[(.*?)\]\((.*?)\)</p>", one, body_html)


PAGE = """<!doctype html>
<html lang="ko"><head><meta charset="utf-8">
<title>{title}</title>
<style>
 body{{margin:0;padding:28px;background:#f5f5f7;
      font-family:"Pretendard","Noto Sans KR","맑은 고딕",sans-serif;color:#2a2a2d;
      line-height:1.75;letter-spacing:-.3px}}
 .meta{{max-width:760px;margin:0 auto 18px;background:#fff;border:1px solid #ccc;
        border-radius:10px;padding:16px 20px;font-size:13px;color:#5f5f5f}}
 .meta b{{color:#2a2a2d}}
 .meta .t{{font-size:19px;font-weight:700;color:#2a2a2d;margin-bottom:8px}}
 .hint{{max-width:760px;margin:0 auto 18px;background:#e6f0cb;border-left:3px solid #40b65a;
        border-radius:0 8px 8px 0;padding:12px 18px;font-size:13px;color:#3a3a3a}}
 .body{{max-width:760px;margin:0 auto;background:#fff;border:1px solid #ccc;
        border-radius:10px;padding:32px 34px;font-size:16px}}
 .body p{{margin:0 0 16px}}
 @media print{{body{{background:#fff;padding:0}} .meta,.hint{{display:none}}
               .body{{border:0;max-width:none;padding:0}}}}
</style></head><body>
<div class="meta">
  <div class="t">{title}</div>
  <div><b>카테고리</b> {category} &nbsp;·&nbsp; <b>발행</b> {when} &nbsp;·&nbsp; <b>분량</b> {chars}자</div>
</div>
<div class="hint">아래 흰 상자 안을 드래그해 복사한 뒤 네이버 글쓰기 에디터에 붙여넣으세요.
굵은 글씨·줄바꿈·그림이 함께 들어갑니다. 그림이 안 넘어가면 함께 보낸 이미지 파일을
캡션에 적힌 이름대로 그 자리에 직접 올리시면 됩니다.</div>
<div class="body">
{body}
</div>
</body></html>
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("posts", nargs="+")
    ap.add_argument("--out", default="blog/export/")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)

    for path in a.posts:
        post = parse_post(path)
        f = post["front"]
        status = f.get("status", "draft")
        if status == "published":
            print("건너뜀 (발행 완료):", os.path.basename(path))
            continue
        when = f.get("scheduled_at") or f.get("publish_date") or "-"
        page = PAGE.format(
            title=html_mod.escape(post["title"]),
            category=html_mod.escape(f.get("category", "-")),
            when=html_mod.escape(when),
            chars=len(post["body"]),
            body=embed_images(to_html(post["body"], post["tags"])),
        )
        name = os.path.splitext(os.path.basename(path))[0] + ".html"
        out = os.path.join(a.out, name)
        open(out, "w", encoding="utf-8").write(page)
        print("내보냄:", out)


if __name__ == "__main__":
    main()
