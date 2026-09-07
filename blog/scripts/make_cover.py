# -*- coding: utf-8 -*-
"""「이달의 대문」 타이틀 이미지와 메뉴 위젯을 만든다.

창체넷 브랜드 규정(ccn-rule)을 따른다 — 배경·면에만 테마색을 쓰고 글자는 무채색,
이모지 없음, hairline 구분선.

사용 예:
  python3 blog/scripts/make_cover.py \
      --image 사진.jpg --label "이달의 대문  ·  2026년 10월" \
      --title "올해 단풍, 언제 왔나요" --out blog/covers/2026-10_단풍/ --crop-top 0.5
"""
import argparse
import os
from PIL import Image, ImageDraw, ImageFont, ImageOps

# 창체넷 색상 토큰
THEMES = {"green": (64, 182, 90), "blue": (56, 111, 183), "amber": (254, 208, 96)}
N1, N3, N5 = (42, 42, 45), (95, 95, 95), (204, 204, 204)
PAPER = (250, 246, 234)
FONT_DIR = "/usr/share/fonts/truetype/nanum/"
BOLD, REG = "NanumSquareB.ttf", "NanumSquareR.ttf"
S = 2                      # 2배로 그린 뒤 축소해 글자를 매끄럽게 한다

MENUS = [("환경교육", "ENVIRONMENT"), ("해양교육", "OCEAN"), ("교재·교구", "CONTENTS"),
         ("프로그램", "PROGRAM"), ("창체넷 소식", "NEWS")]


def font(name, px):
    return ImageFont.truetype(FONT_DIR + name, px * S)


def fit(draw, text, name, px, max_w):
    """폭을 넘으면 글자 크기를 줄여 맞춘다."""
    while px > 8:
        f = font(name, px)
        if draw.textlength(text, font=f) <= max_w * S:
            return f
        px -= 1
    return font(name, 8)


def make_title(src_path, label, title, right, out_path, theme, crop_top, w, h, img_h):
    accent = THEMES[theme]
    canvas = Image.new("RGB", (w * S, h * S), PAPER)
    d = ImageDraw.Draw(canvas)

    # 사진을 가로 폭에 맞춰 잘라 넣는다. crop_top 은 잘라낼 세로 위치(0=위, 1=아래).
    src = ImageOps.exif_transpose(Image.open(src_path)).convert("RGB")
    crop_h = min(src.height, int(src.width / (w / img_h)))
    top = int((src.height - crop_h) * max(0.0, min(1.0, crop_top)))
    band = src.crop((0, top, src.width, top + crop_h)).resize((w * S, img_h * S), Image.LANCZOS)
    canvas.paste(band, (0, 0))

    # 사진 하단을 종이색으로 페이드 → 아래 밴드와 자연스럽게 이어진다
    fade_h = 26 * S
    canvas.paste(Image.new("RGB", (w * S, fade_h), PAPER), (0, img_h * S - fade_h),
                 Image.linear_gradient("L").resize((w * S, fade_h)))
    d.rectangle([0, img_h * S, w * S, img_h * S + S - 1], fill=N5)          # hairline

    pad = 36
    d.rounded_rectangle([pad * S, 292 * S, (pad + 4) * S, 306 * S], radius=2 * S, fill=accent)
    d.text(((pad + 14) * S, 291 * S), label, font=font(REG, 14), fill=N3)
    d.text((pad * S, 318 * S), title, font=fit(d, title, BOLD, 34, w - pad * 2 - 200), fill=N1)
    f_r = font(REG, 15)
    d.text((w * S - pad * S - d.textlength(right, font=f_r), 316 * S), right, font=f_r, fill=N3)

    canvas.resize((w, h), Image.LANCZOS).save(out_path)
    return out_path


def make_widgets(out_dir, theme, ww=170, wh=90):
    accent = THEMES[theme]
    made = []
    for i, (name, en) in enumerate(MENUS, 1):
        c = Image.new("RGB", (ww * S, wh * S), PAPER)
        d = ImageDraw.Draw(c)
        d.rounded_rectangle([S, S, (ww - 1) * S, (wh - 1) * S], radius=8 * S,
                            fill=(255, 255, 255), outline=N5, width=S)
        d.rounded_rectangle([(ww // 2 - 16) * S, 13 * S, (ww // 2 + 16) * S, 16 * S],
                            radius=2 * S, fill=accent)
        f_n = fit(d, name, BOLD, 21, ww - 18)
        d.text(((ww * S - d.textlength(name, font=f_n)) / 2, 33 * S), name, font=f_n, fill=N1)
        f_e = font(REG, 10)
        d.text(((ww * S - d.textlength(en, font=f_e)) / 2, 63 * S), en, font=f_e, fill=N3)
        p = os.path.join(out_dir, "창체넷_위젯%d_%s.png" % (i, name.replace("·", "")))
        c.resize((ww, wh), Image.LANCZOS).save(p)
        made.append(p)
    return made


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--image", required=True, help="배경으로 쓸 사진")
    ap.add_argument("--title", required=True, help="대문 제목")
    ap.add_argument("--label", required=True, help='윗줄 라벨 (예: "이달의 대문  ·  2026년 10월")')
    ap.add_argument("--right", default="㈜창체넷  환경·기후 교육", help="우측 소문구")
    ap.add_argument("--out", required=True, help="저장 폴더")
    ap.add_argument("--theme", default="green", choices=list(THEMES))
    ap.add_argument("--crop-top", type=float, default=0.5, help="사진에서 잘라낼 세로 위치 0~1")
    ap.add_argument("--width", type=int, default=966)
    ap.add_argument("--height", type=int, default=380)
    ap.add_argument("--image-height", type=int, default=268)
    ap.add_argument("--name", default="타이틀", help="타이틀 파일명에 붙일 이름")
    ap.add_argument("--no-widgets", action="store_true")
    a = ap.parse_args()

    os.makedirs(a.out, exist_ok=True)
    t = make_title(a.image, a.label, a.title, a.right,
                   os.path.join(a.out, "창체넷_대문_%s.png" % a.name),
                   a.theme, a.crop_top, a.width, a.height, a.image_height)
    print("타이틀 저장  %dx%d  %s" % (a.width, a.height, t))
    if not a.no_widgets:
        print("위젯 %d개 저장  170x90" % len(make_widgets(a.out, a.theme)))


if __name__ == "__main__":
    main()
