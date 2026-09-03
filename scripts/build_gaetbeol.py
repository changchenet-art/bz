# -*- coding: utf-8 -*-
"""「한반도 연안의 갯벌」 초등 수업 PPT — 원고 스펙 그대로 HTML 20장 생성.

캔버스 A4 가로(297×210mm≈1122×794px) · Pretendard · 연파랑 테마
배경 #eff9fe/#c7eafb · 표지·간지 #518dcb · 글자 #2a2a2d/#3a3a3a/#888 · 파란 글자 금지
이미지는 원고에 지정된 파일명을 자리표(점선 박스)로 표시.
"""
import base64
import glob
import html
import os
import sys

W, H = 1122, 794

# 이미지 자료 폴더(원고가 참조하는 파일명을 여기서 찾아 자동 임베드)
ASSET_DIR = sys.argv[1] if len(sys.argv) > 1 else "assets/갯벌_수업"
_IMG_CACHE = {}


def _find_image(name):
    """파일명(확장자 제외 이름 포함)으로 ASSET_DIR 아래를 재귀 검색."""
    if not os.path.isdir(ASSET_DIR):
        return None
    key = os.path.splitext(name)[0]
    if key in _IMG_CACHE:
        return _IMG_CACHE[key]
    hit = None
    for ext in ("png", "jpg", "jpeg", "webp", "gif"):
        # 정확 파일명 우선
        exact = glob.glob(os.path.join(ASSET_DIR, "**", f"{key}.{ext}"), recursive=True)
        # 이름이 포함된 파일(번호 접두사 등 허용)
        loose = glob.glob(os.path.join(ASSET_DIR, "**", f"*{key}*.{ext}"), recursive=True)
        cands = exact + loose
        if cands:
            hit = cands[0]
            break
    _IMG_CACHE[key] = hit
    return hit


def _data_uri(path):
    ext = os.path.splitext(path)[1].lstrip(".").lower()
    mime = {"jpg": "jpeg"}.get(ext, ext)
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    return f"data:image/{mime};base64,{b64}"

CSS = f"""
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#5b6770;font-family:'Pretendard','Malgun Gothic','맑은 고딕',
     -apple-system,sans-serif;letter-spacing:-.3px;line-height:1.3;color:#3a3a3a}}
.deck{{display:flex;flex-direction:column;align-items:center;gap:20px;padding:20px}}
.slide{{position:relative;width:{W}px;height:{H}px;background:#eff9fe;overflow:hidden;
       box-shadow:0 6px 20px rgba(0,0,0,.25)}}
.pad{{position:absolute;inset:0;padding:40px 49px}}
.pageno{{position:absolute;right:22px;bottom:16px;font-size:11px;color:#888}}
h1,h2,h3{{color:#2a2a2d;letter-spacing:-.5px}}
.title{{font-size:34px;font-weight:800;color:#2a2a2d}}
.sub{{font-size:18px;color:#3a3a3a;margin-top:8px}}
.cap{{font-size:13px;color:#888}}
.badge{{display:inline-flex;align-items:center;justify-content:center;width:34px;height:34px;
       border-radius:9px;background:#518dcb;color:#fff;font-weight:800;font-size:17px}}
.card{{background:#eff9fe;border:1px solid #d6ecf7;border-radius:14px;padding:20px 22px}}
.card.blue{{background:#c7eafb;border-color:#a9dcf3}}
.callout{{background:#c7eafb;border-radius:12px;padding:14px 18px;font-size:16px;color:#2a2a2d}}
table{{width:100%;border-collapse:collapse;font-size:13px}}
th{{background:#e6e6e9;color:#2a2a2d;text-align:left;padding:7px 9px;border:1px solid #cccccc;font-weight:700}}
td{{padding:6px 9px;border:1px solid #cccccc;vertical-align:top;color:#3a3a3a}}
td.n{{font-weight:700;color:#2a2a2d;white-space:nowrap}}
.imgph{{background:#dceef8;border:1.5px dashed #8fbfe0;border-radius:10px;display:flex;
       align-items:center;justify-content:center;color:#5c86a5;font-size:12.5px;text-align:center;padding:6px}}
.imgbox{{border-radius:10px;overflow:hidden;background:#dceef8}}
.imgbox img{{width:100%;height:100%;object-fit:cover;display:block}}
.big{{font-size:52px;font-weight:800;color:#2a2a2d;line-height:1}}
ul{{padding-left:20px}} li{{margin-bottom:6px;font-size:15px}}

/* 표지 */
.cover{{background:#518dcb}}
.cover .r{{position:absolute;right:0;top:0;width:46%;height:100%}}
.cover .t{{position:absolute;left:56px;top:250px;right:52%;color:#fff}}
.cover .t .title{{color:#fff;font-size:44px;line-height:1.14}}
.cover .t .sub{{color:#eaf4ff;font-size:19px;margin-top:14px}}
.cover .t .cap{{color:#cfe4fb;margin-top:26px;font-size:15px}}

/* 간지 */
.divider .panel{{position:absolute;left:0;top:0;width:34%;height:100%;background:#518dcb;
                display:flex;flex-direction:column;justify-content:center;padding:0 44px;color:#fff}}
.divider .panel .k{{font-size:15px;color:#cfe4fb;font-weight:700;margin-bottom:14px}}
.divider .panel .title{{color:#fff;font-size:40px;line-height:1.15}}
.divider .panel .sub{{color:#eaf4ff;font-size:19px;margin-top:14px}}

/* 헤더(일반 슬라이드) */
.hd{{display:flex;align-items:center;gap:12px;margin-bottom:6px}}
.hd .title{{font-size:28px}}
.rule{{width:54px;height:5px;background:#518dcb;border-radius:3px;margin:10px 0 18px}}
.grid{{display:grid;gap:12px}}
.gcap{{font-size:12px;color:#888;margin:2px 0 2px}}
.opt{{color:#2a2a2d}}
.blank{{color:#2a2a2d;font-weight:700}}  /* 파란 글자 금지 규칙 준수 */
"""


def esc(t):
    return html.escape(str(t))


def slide(inner, *, cls="", pageno=None, bg=None):
    style = f' style="background:{bg}"' if bg else ""
    pn = f'<div class="pageno">{pageno}</div>' if pageno else ""
    return f'<div class="slide {cls}"{style}><div class="pad">{inner}</div>{pn}</div>'


def imgph(label, h=200, w="100%"):
    """폴더에서 파일을 찾으면 실제 이미지를, 없으면 점선 자리표를 반환."""
    path = _find_image(label)
    if path:
        uri = _data_uri(path)
        return (f'<div class="imgbox" style="height:{h}px;width:{w}">'
                f'<img src="{uri}" alt="{esc(label)}"></div>')
    return f'<div class="imgph" style="height:{h}px;width:{w}">🖼 {esc(label)}</div>'


def header(n, title):
    return (f'<div class="hd"><span class="badge">{n}</span>'
            f'<span class="title">{esc(title)}</span></div><div class="rule"></div>')


def table(headers, rows):
    th = "".join(f"<th>{esc(h)}</th>" for h in headers)
    trs = ""
    for r in rows:
        tds = "".join(f'<td class="n">{esc(c)}</td>' if i == 0 else f"<td>{esc(c)}</td>"
                      for i, c in enumerate(r))
        trs += f"<tr>{tds}</tr>"
    return f"<table><tr>{th}</tr>{trs}</table>"


S = []

# 1 표지
S.append(slide(
    f'<div class="r">{imgph("00_검은머리물떼새_갯벌.png", H)}</div>'
    '<div class="t"><div class="title">한반도 연안의 갯벌</div>'
    '<div class="sub">갯벌은 보물창고, 우리가 몰랐던 갯벌의 놀라운 가치</div>'
    '<div class="cap">초등 · 2차시</div></div>',
    cls="cover"))

# 2 학습목표
obj = (
    '<div class="grid" style="grid-template-columns:1fr 1fr">'
    '<div class="card"><div class="hd"><span class="badge">1</span>'
    '<span class="title" style="font-size:22px">1차시</span></div>'
    '<ul><li>검은머리물떼새를 비롯한 갯벌 생물의 생태적 특징을 설명하고, 먹이 관계로 '
    '갯벌 생태계의 연결성을 이해합니다.</li>'
    '<li>갯벌 서식지 감소가 생물다양성에 미치는 영향을 먹이사슬 관점에서 추론합니다.</li></ul></div>'
    '<div class="card"><div class="hd"><span class="badge">2</span>'
    '<span class="title" style="font-size:22px">2차시</span></div>'
    '<ul><li>갯벌이 제공하는 생태적·경제적·환경적 가치를 설명합니다.</li>'
    '<li>자연과 인간의 공존을 위한 일상 속 실천 방안을 제시합니다.</li></ul></div></div>')
S.append(slide(header("2", "오늘의 학습 목표") + obj, pageno="2"))

# 3 간지1
S.append(slide(
    '<div class="panel"><div class="k">1차시</div>'
    '<div class="title">갯벌은 보물창고</div>'
    '<div class="sub">갯벌에는 누가 살고 있을까?</div></div>',
    cls="divider", pageno="3"))

# 4 편지
letter = ('"안녕, 친구들! 나는 서해안 갯벌에 살고 있는 검은머리물떼새라고 해. 까만 양복에 하얀 '
          '셔츠를 입은 것처럼 멋지지? 주황빛 붉은 눈과 부리 덕분에 갯벌의 멋쟁이 신사라는 별명도 '
          '있어. 내가 왜 이 진흙투성이 갯벌에 사냐고? 이곳이 내게는 세상에서 가장 맛있는 먹이가 '
          '가득한 <b>\'보물창고\'</b>이기 때문이야! 그런데 요즘 갯벌이 조금씩 사라지고 있어서 마음이 '
          '아파. 갯벌이 아프면 조개와 게가 사라지고, 결국 나 같은 새들도 살 수 없게 되거든."')
S.append(slide(
    header("4", "검은머리물떼새의 편지") +
    '<div class="grid" style="grid-template-columns:40% 1fr;align-items:start">'
    f'{imgph("00_검은머리물떼새_갯벌.png", 380)}'
    f'<div><div class="card" style="font-size:16px;line-height:1.5">{letter}</div>'
    '<div class="callout" style="margin-top:14px"><b>발문</b> &nbsp;검은머리물떼새가 갯벌을 '
    '\'보물창고\'라고 부른 이유는 무엇이었을까요?</div></div></div>',
    pageno="4"))

# 5 생물 21종
groups = [
    ("염생식물", ["갈대", "칠면초", "퉁퉁마디"]), ("해조류", ["파래"]),
    ("조개류", ["맛조개", "동죽", "바지락", "갯고둥"]),
    ("연체·환형", ["낙지", "갯지렁이", "쏙"]),
    ("게류", ["민꽃게", "밤게", "칠게", "농게"]),
    ("물고기", ["짱뚱어", "망둑어"]),
    ("새", ["알락꼬리마도요", "검은머리물떼새", "저어새", "괭이갈매기"]),
]
cells = ""
for grp, names in groups:
    for nm in names:
        cells += (f'<div style="text-align:center">{imgph(nm, 78)}'
                  f'<div class="gcap">{esc(grp)} · {esc(nm)}</div></div>')
S.append(slide(
    header("5", "갯벌에는 누가 살고 있을까요? — 갯벌 생물 21종") +
    f'<div class="grid" style="grid-template-columns:repeat(7,1fr)">{cells}</div>',
    pageno="5"))

# 6 카드 자세히 ①
t6 = table(["생물", "영양원·먹이", "특징"], [
    ["갈대", "스스로 광합성", "갯벌 가장자리(염습지)에서 무리 지어 자람. 죽어 썩은 파편은 갯지렁이·게의 먹이"],
    ["칠면초", "스스로 광합성", "한 해 7가지 색으로 변함. 가을 갯벌을 붉게 물들임"],
    ["퉁퉁마디(함초)", "스스로 광합성", "소금기를 흡수해 짭조름함. 바닷가 환경을 정화"],
    ["파래", "스스로 광합성", "바위·진흙에 붙어 자라는 녹조류. 갯고둥의 먹이"],
    ["맛조개", "식물 플랑크톤", "대나무 마디처럼 길쭉. 위험하면 구멍으로 빠르게 도망"],
    ["동죽", "식물 플랑크톤", "하얗고 둥근 조개. 숨관을 뻗어 플랑크톤을 걸러 먹음"],
    ["바지락", "식물 플랑크톤", "가장 흔한 조개. 갯벌 바닷물을 정화"],
    ["갯고둥", "플랑크톤·파래", "갯벌 표면의 이끼·유기물을 갉아먹는 청소부"],
])
imgs6 = "".join(imgph(nm, 84) for nm in
                ["갈대", "칠면초", "퉁퉁마디", "파래", "맛조개", "동죽", "바지락", "갯고둥"])
S.append(slide(
    header("6", "생물카드 자세히 보기 ① 식물 · 조개류") +
    '<div class="grid" style="grid-template-columns:33% 1fr;align-items:start">'
    f'<div class="grid" style="grid-template-columns:1fr 1fr">{imgs6}</div>'
    f'<div>{t6}</div></div>',
    pageno="6"))

# 7 카드 자세히 ②
rows7 = [
    ["낙지", "칠게·밤게·갯지렁이", "8개의 다리를 가진 갯벌 최고의 포식자"],
    ["갯지렁이", "유기물·미생물", "흙에 산소를 공급하는 '갯벌의 쟁기'"],
    ["쏙", "플랑크톤·유기물", "1m 넘는 Y자 구멍에 삶. 붓을 넣으면 집게발로 꽉 잡음"],
    ["민꽃게(박하지)", "조개·작은 게·사체", "집게발 힘이 강해 조개껍데기를 부숨"],
    ["밤게", "죽은 생물 사체", "앞으로 똑바로 걷는 '갯벌의 청소부'"],
    ["칠게", "식물 플랑크톤", "가장 흔한 회갈색 게. 대형 포식자의 주요 먹이"],
    ["농게", "유기물·플랑크톤", "수컷의 거대한 붉은 집게발로 구애 춤"],
    ["짱뚱어", "식물 플랑크톤", "피부로도 숨을 쉬어 갯벌 위를 뛰어다님"],
    ["망둑어(풀망둑)", "갯지렁이·작은 게", "시력이 좋고 민첩한 육식성 물고기"],
    ["알락꼬리마도요", "칠게·농게·갯지렁이", "아래로 휜 긴 부리로 깊은 구멍 속을 사냥"],
    ["검은머리물떼새", "조개류·갯지렁이", "단단한 부리로 조개 관자를 끊어 먹음 (천연기념물)"],
    ["저어새", "짱뚱어·망둑어·새우", "주걱 부리를 좌우로 저으며 사냥 (천연기념물)"],
    ["괭이갈매기", "물고기·게·사체", "고양이 울음소리를 내는 잡식성 바닷새"],
]
strip7 = "".join(imgph(r[0], 62) for r in rows7)
S.append(slide(
    header("7", "생물카드 자세히 보기 ② 게 · 물고기 · 새") +
    f'<div class="grid" style="grid-template-columns:repeat(13,1fr);margin-bottom:10px">{strip7}</div>'
    f'<div style="font-size:11.5px">{table(["생물","먹이","특징"], rows7)}</div>',
    pageno="7"))

# 8 퀴즈 OX
ox = [
    "이 식물은 가을이 되면 갯벌을 붉은 양단처럼 물들여요. 한 해 7가지 색으로 변해서 이름 붙여진 이 식물은 <b>'갈대'</b>입니다.",
    "<b>'파래'</b>는 바위나 진흙에 붙어 자라는 초록색 해조류입니다. 갯고둥이나 초식 동물의 식사가 됩니다.",
    "<b>'동죽'</b>은 대나무 마디처럼 길쭉한 조개로, 위험을 감지하면 구멍 깊숙이 도망칩니다.",
    "<b>'밤게'</b>는 앞으로 똑바로 걸어 다니며 죽은 생물의 사체를 먹는 '갯벌의 청소부'입니다.",
    "<b>'농게'</b>는 수컷의 몸집만 한 거대한 붉은 집게발 하나가 특징입니다.",
    "<b>'짱뚱어'</b>는 피부로도 숨을 쉴 수 있어 물 밖 갯벌 위를 뛰어다닙니다.",
    "<b>'저어새'</b>는 고양이 울음소리를 내며, 물고기·게·사체를 가리지 않고 먹는 새입니다.",
]
lis = "".join(f'<li>{q} &nbsp;<b style="color:#2a2a2d">( O &nbsp;, &nbsp;X )</b></li>' for q in ox)
S.append(slide(
    header("8", "갯벌 생물 퀴즈 ① 맞으면 O, 틀리면 X") +
    f'<ul style="font-size:15px;line-height:1.35">{lis}</ul>'
    '<div class="callout" style="margin-top:12px"><b>진행</b> 개인 화이트보드에 O/X를 써서 동시에 들기'
    ' &nbsp;·&nbsp; <span class="cap">정답 1.X(칠면초) 2.O 3.X(맛조개) 4.O 5.O 6.O 7.X(괭이갈매기)</span></div>',
    pageno="8"))

# 9 퀴즈 객관식
mc = [
    ("마디가 퉁퉁하고 잎이 퇴화한 염생식물. 짭조름한 맛이 나는 이 식물은?", "① 갈대　② 칠면초　③ 퉁퉁마디　④ 파래"),
    ("하얗고 둥근 조개로, 숨관을 길게 뻗어 플랑크톤을 걸러 먹는 조개는?", "① 동죽　② 쏙　③ 맛조개　④ 갯고둥"),
    ("8개의 다리를 가진 갯벌 최고의 포식자로, 칠게 구멍에 다리를 넣어 사냥하는 생물은?", "① 낙지　② 쏙　③ 갯지렁이　④ 민꽃게"),
    ("1m 넘는 Y자 구멍에 살며, 구멍에 붓을 넣으면 집게발로 꽉 잡는 생물은?", "① 낙지　② 갯지렁이　③ 쏙　④ 칠게"),
    ("가장 흔하게 무리 지어 사는 회갈색 게로, 대형 포식자의 중요한 먹이가 되는 게는?", "① 농게　② 칠게　③ 밤게　④ 민꽃게"),
    ("검은색·흰색 깃털에 붉고 길쭉한 부리가 특징인 천연기념물 새는?", "① 알락꼬리마도요　② 검은머리물떼새　③ 저어새　④ 괭이갈매기"),
    ("주걱처럼 넓적한 검은 부리로 짱뚱어·새우를 사냥하는 천연기념물 새는?", "① 알락꼬리마도요　② 검은머리물떼새　③ 저어새　④ 괭이갈매기"),
]
lis = "".join(f'<li>{esc(q)}<br><span class="opt">{esc(o)}</span></li>' for q, o in mc)
S.append(slide(
    header("9", "갯벌 생물 퀴즈 ② 알맞은 답을 골라요") +
    f'<ul style="font-size:14.5px;line-height:1.3">{lis}</ul>'
    '<div class="cap" style="margin-top:8px">정답 8.③ 9.① 10.① 11.③ 12.② 13.② 14.③</div>',
    pageno="9"))

# 10 퀴즈 빈칸
fb = [
    ("갯벌 가장자리에서 무리 지어 자라며, 죽은 파편이 갯지렁이·게의 먹이가 되는 여러해살이 풀은?", "갈＿"),
    ("부채꼴 줄무늬가 있고 갯벌 바닷물을 정화하는 가장 흔한 조개는?", "바＿＿"),
    ("뾰족한 소라 모양 껍데기를 쓰고 갯벌 표면을 청소하는 생물은?", "갯＿＿"),
    ("흙을 온종일 먹고 배설하며 산소를 공급하는 '갯벌의 쟁기'는?", "갯＿＿＿"),
    ("성질이 사납고 집게발로 조개껍데기를 부수는, '박하지'라 불리는 게는?", "민＿＿"),
    ("시력이 좋고 민첩한 갯벌의 대표 육식성 물고기는?", "＿＿＿(풀망둑)"),
    ("몸길이만큼 길고 아래로 휜 부리로 깊은 구멍 속 게를 잡는 새는?", "알락꼬리＿＿＿"),
]
lis = "".join(f'<li>{esc(q)} &nbsp;정답 ( <span class="blank">{esc(a)}</span> )</li>' for q, a in fb)
S.append(slide(
    header("10", "갯벌 생물 퀴즈 ③ 이름을 직접 적어요") +
    f'<ul style="font-size:15px;line-height:1.4">{lis}</ul>'
    '<div class="cap" style="margin-top:8px">정답 15.갈대 16.바지락 17.갯고둥 18.갯지렁이 19.민꽃게 20.망둑어 21.알락꼬리마도요</div>',
    pageno="10"))

# 11 먹이사슬
S.append(slide(
    header("11", "활동 · 갯벌 먹이사슬 한 줄 잇기") +
    '<div class="grid" style="grid-template-columns:1fr 1fr;align-items:start">'
    '<div class="card blue"><b>1단계 — 피식과 포식 나누기</b>'
    '<ul style="margin-top:8px"><li><b>포식자</b>(잡아먹는 쪽): 민꽃게, 낙지, 망둑어, 알락꼬리마도요, '
    '검은머리물떼새, 저어새, 괭이갈매기</li>'
    '<li><b>피식자</b>(먹히는 쪽): 갈대 파편, 파래, 맛조개, 동죽, 바지락, 갯고둥, 갯지렁이, 칠게, 농게, 짱뚱어</li></ul></div>'
    '<div class="card"><b>2단계 — 화살표로 잇기</b>'
    '<div class="cap" style="margin:6px 0">화살표는 항상 <b>먹히는 쪽 ➔ 먹는 쪽</b>을 향하게.</div>'
    '<ul><li>파래 ➔ 바지락 ➔ 민꽃게 ➔ 검은머리물떼새</li>'
    '<li>갈대 파편 ➔ 갯지렁이 ➔ 망둑어 ➔ 저어새</li>'
    '<li>칠게·농게 ➔ 낙지 ➔ 괭이갈매기</li></ul></div></div>'
    '<div class="callout" style="margin-top:14px"><b>포인트</b> 민꽃게는 조개를 먹지만, 더 큰 새에게는 '
    '먹히는 <b>피식자</b>가 되기도 해요.</div>',
    pageno="11"))

# 12 사라지면
S.append(slide(
    header("12", "갯벌이 사라지면 어떤 일이 일어날까요?") +
    '<div class="grid" style="grid-template-columns:30% 1fr;align-items:start">'
    f'<div>{imgph("01_검은머리물떼새_실사.png",180)}<div style="height:10px"></div>'
    f'{imgph("02_검은머리물떼새_알_위장.png",160)}</div>'
    '<div><div class="callout"><b>발문</b> 갯벌이 사라지면 검은머리물떼새에게는 어떤 일이 일어날까요?</div>'
    '<ul style="margin-top:12px"><li>더 이상 먹이를 구하지 못해 굶주리게 됩니다.</li>'
    '<li>아기 새들을 건강하게 키울 수 없습니다.</li>'
    '<li>숫자가 점점 줄어 결국 멸종 위기에 처하게 됩니다.</li></ul>'
    '<div class="card blue" style="margin-top:12px"><b>우리가 할 수 있는 일</b> &nbsp;'
    '① 갯벌에 쓰레기를 버리지 않기 &nbsp; ② 지정된 탐방로 이용, 적당한 거리 유지 &nbsp; '
    '③ 갯벌 생물의 소중함을 친구들에게 알리기</div>'
    '<div class="cap" style="margin-top:10px"><b>교사용 참고</b> 천연기념물 제326호 · 환경부 멸종위기 '
    '야생생물 Ⅱ급. 자갈밭 바닥을 파고 알을 낳아 알이 주변 자갈과 완벽히 위장됩니다. 충남 서천 유부도 '
    '갯벌은 국내 최대 월동지 중 하나입니다.</div></div></div>',
    pageno="12"))

# 13 간지2
S.append(slide(
    '<div class="panel"><div class="k">2차시</div>'
    '<div class="title">갯벌의 놀라운 가치</div>'
    '<div class="sub">갯벌은 왜 \'갯세권\'일까?</div></div>',
    cls="divider", pageno="13"))

# 14 주요 갯벌
S.append(slide(
    header("14", "우리나라 주요 갯벌") +
    '<div class="grid" style="grid-template-columns:44% 1fr;align-items:start">'
    f'{imgph("10_우리나라주요갯벌_지도.png",420)}'
    '<div><p style="font-size:16px">우리나라 갯벌은 주로 <b>서해안과 남해안</b>에 분포합니다.</p>'
    '<div class="card" style="margin-top:12px"><b>유네스코 세계자연유산 \'한국의 갯벌\'</b><br>'
    '신안 · 보성순천 · 고창 · 서천 <span class="cap">(2021년 등재)</span><br>'
    '<span class="cap">추가 등재 추진: 서산 · 고흥 · 무안 · 여수</span></div>'
    '<div class="card blue" style="margin-top:12px">신안 갯벌 — 세계 5대 갯벌 중 하나.<br>'
    '밝혀진 서식 생물만 <span class="big" style="font-size:48px;vertical-align:-6px">2,150</span>'
    ' 여 종<br><span class="cap">다른 나라 갯벌의 두 배 이상</span></div></div></div>',
    pageno="14"))

# 15 6가지 가치
vals = [
    ("11", "해양 생태계 보전", "새·조개·게·염생식물이 살아가는 소중한 서식지"),
    ("12", "자연 정화 작용", "미생물이 오염물질을 분해 — 전국 하수처리장보다 뛰어난 효율"),
    ("13", "홍수 조절·해안 방파제", "태풍의 파도 에너지를 흡수해 침식·침수를 막음"),
    ("14", "어업 생산·경제적 가치", "낙지·조개·굴 등 풍부한 수산 자원 공급"),
    ("15", "생태 관광·교육", "체험과 탐방로를 통한 배움과 휴식의 공간"),
    ("16", "기후 조절(블루카본)", "이산화탄소를 흡수해 갯벌 흙 속에 오래 저장"),
]
cards = ""
for num, nm, desc in vals:
    cards += (f'<div class="card">{imgph(num+"_가치.png",120)}'
              f'<div style="font-weight:800;color:#2a2a2d;margin-top:8px;font-size:16px">{esc(nm)}</div>'
              f'<div class="cap" style="margin-top:2px">{esc(desc)}</div></div>')
S.append(slide(
    header("15", "갯벌의 6가지 가치") +
    f'<div class="grid" style="grid-template-columns:repeat(3,1fr)">{cards}</div>',
    pageno="15"))

# 16 숫자로 보는
nums = [
    ("50배", "블루카본은 그린카본보다 최대 50배 빠르게 온실가스를 흡수 (UN·IUCN)"),
    ("49만 톤", "한국 갯벌의 연간 최대 CO₂ 흡수량 — 자동차 20만 대의 1년 배출량"),
    ("18조 원", "갯벌의 연간 생태계 서비스 가치 (해양수산부·KMI, 약 17조 8,121억 원)"),
    ("23%", "지난 30년간 줄어든 국내 갯벌 면적"),
]
cards = "".join(
    f'<div class="card"><div class="big">{esc(n)}</div>'
    f'<div class="cap" style="margin-top:10px;font-size:13px">{esc(d)}</div></div>' for n, d in nums)
S.append(slide(
    header("16", "숫자로 보는 갯벌") +
    f'<div class="grid" style="grid-template-columns:repeat(4,1fr)">{cards}</div>'
    '<div class="callout" style="margin-top:16px"><b>정책</b> 해양수산부는 2030년까지 총 10㎢의 갯벌 '
    '복원과 염생식물 군락지 조성을 추진하고 있습니다.</div>',
    pageno="16"))

# 17 역할극
t17 = table(["역할", "대사 예시"], [
    ["어민", "낙지·바지락·게가 모두 사라져서 생계가 막막해졌어요."],
    ["검은머리물떼새", "쉴 곳과 먹이가 없어 굶어 죽을 위기예요."],
    ["해안가 주민", "파도를 막아줄 갯벌이 없으니 바닷물이 마을까지 들이쳐 침수됐어요."],
    ["지구(환경학자)", "갯벌이 흡수하던 이산화탄소가 배출돼 지구온난화가 더 빨라졌습니다."],
    ["갯벌 생물", "(직접 만들어 보세요)"],
    ["생태 관광객", "(직접 만들어 보세요)"],
    ["나", "(직접 만들어 보세요)"],
])
S.append(slide(
    header("17", "활동 · 갯벌이 사라진 지 1년 후, 나의 하루") +
    '<div class="grid" style="grid-template-columns:32% 1fr;align-items:start">'
    f'{imgph("17_역할극_다양한주체.png",380)}<div>{t17}'
    '<div class="callout" style="margin-top:12px"><b>마무리 질문</b> 우리는 갯벌을 살리기 위해 무엇을 '
    '해야 할까요?</div></div></div>',
    pageno="17"))

# 18 수호 활동
groups18 = [
    ("일상생활에서 갯벌 지키기 (오염 줄이기)",
     ["합성세제·샴푸 적당히 쓰기", "일회용 플라스틱 줄이기", "분리배출 철저히 하기", "강·하천 근처에 쓰레기 버리지 않기"]),
    ("갯벌 여행 시 실천하기 (생태계 보호)",
     ["갯벌 생물 과도하게 잡지 않기", "어린 생물(치어·작은 조개) 방생하기", "갯벌 주변 쓰레기 모두 되가져오기"]),
    ("관심 갖고 행동하기 (사회적 수호)",
     ["친구·가족에게 갯벌의 가치 알리기", "비치코밍·플로깅 참여하기", "무분별한 매립·개발 반대 서명 참여하기", "해양보호생물 기억하기"]),
]
cards = ""
for tt, items in groups18:
    li = "".join(f'<li>☐ {esc(x)}</li>' for x in items)
    cards += (f'<div class="card"><div style="font-weight:800;color:#2a2a2d;font-size:15px;'
              f'margin-bottom:8px">{esc(tt)}</div><ul style="list-style:none;padding-left:0">{li}</ul></div>')
S.append(slide(
    header("18", "내가 할 수 있는 갯벌 수호 활동") +
    f'<div class="grid" style="grid-template-columns:repeat(3,1fr)">{cards}</div>',
    pageno="18"))

# 19 정리 ○○이다
ex = [
    ("갯벌은 스펀지이다.", "태풍의 파도 에너지를 흡수해 마을 침수를 막아주기 때문이다."),
    ("갯벌은 정수기이다.", "생활하수와 오염물질을 미생물과 조개들이 깨끗하게 걸러주기 때문이다."),
    ("갯벌은 보물섬이다.", "수많은 바다 생물이 살며 어민들에게 풍요로운 삶을 선물하기 때문이다."),
    ("갯벌은 휴게소이다.", "멀리 이동하는 지친 철새들이 쉬어가고 배불리 먹을 수 있는 장소이기 때문이다."),
    ("갯벌은 지구의 에어컨이다.", "이산화탄소를 많이 흡수해 지구 온도가 오르지 않도록 돕기 때문이다."),
]
cards = "".join(
    f'<div class="card"><b style="color:#2a2a2d">{esc(a)}</b>'
    f'<div class="cap" style="margin-top:4px">{esc(b)}</div></div>' for a, b in ex)
S.append(slide(
    header("19", "정리 · 갯벌은 ○○이다") +
    '<div class="callout" style="font-size:24px;text-align:center;padding:22px">'
    '갯벌은 (　　　　)이다. &nbsp; 왜냐하면 　　　　 때문이다.</div>'
    f'<div class="grid" style="grid-template-columns:repeat(5,1fr);margin-top:16px">{cards}</div>',
    pageno="19"))

# 20 출처
refs = [
    "원자료: 「한반도 연안의 갯벌」 1차시·2차시 교수학습 자료, ㈜창체넷",
    "관련 성취기준: [4과06-03] 갯벌의 가치와 보전 / [4과14-02] 먹이그물 / [4과14-03] 인간 활동과 생태계 보전 / [6사01-01] 해안 지형 / [6사12-02] 지속가능한 미래 (2022 개정)",
    "국가교육과정정보센터 https://ncic.re.kr · 해양수산부 https://www.mof.go.kr",
    "해양환경공단 갯벌정보시스템 https://www.koem.or.kr",
    "유네스코 세계유산 '한국의 갯벌' https://whc.unesco.org/en/list/1591",
    "국가유산청(천연기념물 검은머리물떼새) https://www.khs.go.kr",
    "참고 영상: 「갯세권」·「신안갯벌」·「멸종위기 동식물들의 터전, 한국 갯벌」·「전 세계가 인정한 한국의 갯벌」 (YouTube)",
    "참고 영화: 다큐멘터리 「수라」(황윤 감독, 2023)",
]
li = "".join(f'<li>{esc(r)}</li>' for r in refs)
S.append(slide(
    header("20", "마무리 · 참고자료") +
    f'<ul style="font-size:14px;line-height:1.5">{li}</ul>',
    pageno="20"))


def main():
    os.makedirs("output", exist_ok=True)
    body = "".join(S)
    doc = (f"<!doctype html><html lang='ko'><head><meta charset='utf-8'>"
           f"<title>한반도 연안의 갯벌 · 수업 PPT</title><style>{CSS}</style></head>"
           f"<body><div class='deck'>{body}</div></body></html>")
    out = "output/한반도갯벌_수업PPT.html"
    with open(out, "w", encoding="utf-8") as f:
        f.write(doc)
    found = sum(1 for v in _IMG_CACHE.values() if v)
    total = len(_IMG_CACHE)
    print("생성:", out, "· 슬라이드", len(S), "장")
    print(f"이미지 폴더: {ASSET_DIR}  (자동 임베드 {found}/{total}, "
          f"나머지 {total - found}개는 자리표)")


if __name__ == "__main__":
    main()
