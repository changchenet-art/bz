"""HTML 덱 → 슬라이드별 PNG + 컨택트시트(PIL)."""
import os
import sys

from PIL import Image
from playwright.sync_api import sync_playwright

EXE = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
HTML = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else "output/청주해양_제안발표.html")
OUT = sys.argv[2] if len(sys.argv) > 2 else \
    "/tmp/claude-0/-home-user-bz/c6157116-9528-54cf-a6ad-1b680722eda5/scratchpad/shots"
os.makedirs(OUT, exist_ok=True)


def main():
    paths = []
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=EXE, args=["--no-sandbox",
                              "--force-color-profile=srgb"])
        pg = b.new_page(viewport={"width": 1320, "height": 760},
                        device_scale_factor=2)
        pg.goto(f"file://{HTML}")
        pg.wait_for_timeout(400)
        slides = pg.query_selector_all(".slide")
        print("slides:", len(slides))
        for i, el in enumerate(slides):
            fp = os.path.join(OUT, f"s{i:02d}.png")
            el.screenshot(path=fp)
            paths.append(fp)
        b.close()

    # 컨택트시트: 앞 12장, 3열 그리드
    thumbs = paths[:12]
    cols, gap, bg = 3, 24, (91, 103, 112)
    ims = [Image.open(t) for t in thumbs]
    tw = 520
    th = int(ims[0].height * tw / ims[0].width)
    rows = (len(ims) + cols - 1) // cols
    W = cols * tw + (cols + 1) * gap
    H = rows * th + (rows + 1) * gap
    sheet = Image.new("RGB", (W, H), bg)
    for i, im in enumerate(ims):
        r, c = divmod(i, cols)
        x = gap + c * (tw + gap)
        y = gap + r * (th + gap)
        sheet.paste(im.resize((tw, th)), (x, y))
    sheet_path = os.path.join(OUT, "contact_sheet.png")
    sheet.save(sheet_path)
    print("contact sheet:", sheet_path)


if __name__ == "__main__":
    main()
