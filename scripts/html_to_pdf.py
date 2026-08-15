"""HTML → PDF (크로미움). 사용: html_to_pdf.py <in.html> <out.pdf> [slides|doc]

slides: 1280×720 가로 슬라이드(1장=1페이지)
doc   : A4 세로 문서(발표노트)
"""
import os
import sys

from playwright.sync_api import sync_playwright

EXE = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"


def main():
    src = os.path.abspath(sys.argv[1])
    out = os.path.abspath(sys.argv[2])
    mode = sys.argv[3] if len(sys.argv) > 3 else "doc"
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=EXE, args=["--no-sandbox"])
        pg = b.new_page()
        pg.goto(f"file://{src}")
        pg.emulate_media(media="print")
        pg.wait_for_timeout(300)
        if mode == "slides":
            pg.pdf(path=out, width="1280px", height="720px", print_background=True,
                   margin={"top": "0", "bottom": "0", "left": "0", "right": "0"})
        else:
            pg.pdf(path=out, format="A4", print_background=True,
                   margin={"top": "12mm", "bottom": "12mm",
                           "left": "10mm", "right": "10mm"})
        b.close()
    print("PDF:", out)


if __name__ == "__main__":
    main()
