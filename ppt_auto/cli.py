"""명령행 인터페이스.

예)
  # 자유 텍스트 원고 → PPT + PDF
  python -m ppt_auto gen -i examples/sample.md --skin beige_business

  # 엑셀 양식 → PPT + PDF
  python -m ppt_auto gen -i deck.xlsx --skin white_blue_minimal

  # 부정 이슈 + 원고 세트 → 대응 브리핑
  python -m ppt_auto gen --issue issue.txt --manuscript manuscript.md

  # 엑셀 입력 템플릿 만들기
  python -m ppt_auto template -o templates/입력양식.xlsx

  # 스킨 목록
  python -m ppt_auto skins
"""
from __future__ import annotations

import argparse
import os
import sys

from . import __version__
from .notes import generate as generate_notes
from .parse import excel as p_excel
from .parse import freetext as p_freetext
from .parse import html_doc as p_html
from .parse import issue as p_issue
from .render import canva as r_canva
from .render import pdf_notes as r_pdf
from .render import pptx_local as r_pptx
from .schema import Deck
from .skins.registry import DEFAULT_SKIN, list_skins


def _load_deck(args) -> Deck:
    if args.issue:
        if not args.manuscript:
            sys.exit("오류: --issue 사용 시 --manuscript 도 필요합니다.")
        deck = p_issue.parse_files(args.issue, args.manuscript)
    elif args.input:
        ext = os.path.splitext(args.input)[1].lower()
        if ext in (".xlsx", ".xlsm"):
            deck = p_excel.parse_file(args.input)
        elif ext in (".html", ".htm"):
            deck = p_html.parse_file(args.input, skin=args.skin or "white_blue_minimal")
        else:
            deck = p_freetext.parse_file(args.input)
    else:
        sys.exit("오류: -i/--input 또는 --issue 를 지정하세요.")
    if args.skin:
        deck.skin = args.skin
    return deck


def cmd_gen(args) -> None:
    deck = _load_deck(args)
    generate_notes(deck, presenter=deck.author)
    os.makedirs(args.out_dir, exist_ok=True)
    stem = args.name or _safe(deck.title)
    made = []

    if args.format in ("pptx", "both") and args.engine == "local":
        path = os.path.join(args.out_dir, f"{stem}.pptx")
        r_pptx.build(deck, path, skin=args.skin)
        made.append(path)
    if args.engine == "canva":
        path = os.path.join(args.out_dir, f"{stem}_canva.json")
        r_canva.build(deck, path, skin=args.skin)
        made.append(path)
        made.append(path.rsplit(".", 1)[0] + "_runbook.md")
    if args.format in ("pdf", "both"):
        path = os.path.join(args.out_dir, f"{stem}_설명자료.pdf")
        r_pdf.build(deck, path)
        made.append(path)

    print(f"[{deck.skin}] 슬라이드 {len(deck.slides)}장 생성 완료:")
    for m in made:
        print("  -", m)


def cmd_template(args) -> None:
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    p_excel.write_template(args.out)
    print("엑셀 입력 양식 생성:", args.out)


def cmd_skins(args) -> None:
    print("사용 가능한 스킨:")
    for sk in list_skins():
        canva = f" · Canva:{sk.canva_design_id}" if sk.canva_design_id else ""
        print(f"  {sk.key:20s} {sk.ko_name:14s} [{sk.mood}]{canva}")
        print(f"  {'':20s}   추천: {', '.join(sk.best_for)}")


def _safe(name: str) -> str:
    import re
    return re.sub(r"[^\w가-힣._-]+", "_", name).strip("_") or "deck"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="ppt_auto", description="원고 → PPT + PDF 설명자료 자동화")
    ap.add_argument("--version", action="version", version=f"ppt_auto {__version__}")
    sub = ap.add_subparsers(dest="cmd", required=True)

    g = sub.add_parser("gen", help="원고에서 PPT/PDF 생성")
    g.add_argument("-i", "--input", help="원고 파일 (.md/.txt 또는 .xlsx)")
    g.add_argument("--issue", help="부정 이슈 파일 (대응 브리핑 모드)")
    g.add_argument("--manuscript", help="대응 원고 파일 (--issue 와 함께)")
    g.add_argument("--skin", default=None, help=f"스킨 키 (기본: {DEFAULT_SKIN})")
    g.add_argument("--engine", choices=["local", "canva"], default="local",
                   help="출력 엔진 (local=python-pptx, canva=자동채우기 페이로드)")
    g.add_argument("--format", choices=["pptx", "pdf", "both"], default="both")
    g.add_argument("--out-dir", default="output")
    g.add_argument("--name", help="출력 파일명(확장자 제외)")
    g.set_defaults(func=cmd_gen)

    t = sub.add_parser("template", help="엑셀 입력 양식 생성")
    t.add_argument("-o", "--out", default="templates/입력양식.xlsx")
    t.set_defaults(func=cmd_template)

    s = sub.add_parser("skins", help="스킨 목록")
    s.set_defaults(func=cmd_skins)
    return ap


def main(argv=None) -> None:
    ap = build_parser()
    args = ap.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
