"""HTML 도식을 3200x1800 PNG(1600x900 레이아웃, 2배 해상도)로 렌더링합니다.

사용법: <venv python> render.py src/<이름>.html out/<이름>.png
- HTML은 같은 폴더의 base.css를 <link rel="stylesheet" href="../base.css">로 불러옵니다.
- 렌더 후 글자가 상자를 넘치면(scrollWidth/Height > client) 경고를 출력합니다.
"""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

src, out = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
out.parent.mkdir(parents=True, exist_ok=True)
with sync_playwright() as p:
    browser = p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome")
    page = browser.new_page(viewport={"width": 1600, "height": 900}, device_scale_factor=2)
    page.goto(src.as_uri())
    page.wait_for_timeout(300)
    page.evaluate("document.fonts.ready")
    overflow = page.evaluate("""() => [...document.querySelectorAll('body *')]
        .filter(e => e.scrollWidth > e.clientWidth + 2 || e.scrollHeight > e.clientHeight + 2)
        .filter(e => getComputedStyle(e).overflow !== 'visible' || e === document.body)
        .map(e => e.className || e.tagName).slice(0, 10)""")
    body_overflow = page.evaluate("document.body.scrollHeight > 900 || document.body.scrollWidth > 1600")
    page.screenshot(path=str(out), clip={"x": 0, "y": 0, "width": 1600, "height": 900})
    browser.close()
print("saved", out)
if body_overflow:
    print("WARNING: 본문이 1600x900을 넘칩니다(잘림).")
if overflow:
    print("WARNING: 넘치는 요소:", overflow)

# 빈 공간 검사: 흰 배경이 아닌 픽셀의 범위로 내용이 캔버스를 얼마나 채우는지 계산합니다.
from PIL import Image, ImageChops
img = Image.open(out).convert("RGB")
diff = ImageChops.difference(img, Image.new("RGB", img.size, (255, 255, 255))).convert("L").point(lambda v: 255 if v > 12 else 0)
box = diff.getbbox()
W, H = img.size
if box:
    left, top, right, bottom = box
    bottom_gap = (H - bottom) / H
    side_gap = max(left, W - right) / W
    print(f"FILL: 내용 범위 x {left/W:.0%}–{right/W:.0%}, y {top/H:.0%}–{bottom/H:.0%} (아래 여백 {bottom_gap:.0%}, 옆 여백 최대 {side_gap:.0%})")
    if bottom_gap > 0.06 or side_gap > 0.06:
        print("WARNING: 빈 공간이 큽니다. 아래·옆 여백이 6% 이하가 되도록 카드·글자를 키우거나 배치를 바꾸세요.")
    # 세로 방향으로 큰 빈 띠(내용 사이 공백)가 있는지 검사
    rows = [diff.crop((0, y, W, y + 1)).getbbox() is not None for y in range(top, bottom)]
    run = best = 0
    for filled in rows:
        run = 0 if filled else run + 1
        best = max(best, run)
    if best / H > 0.10:
        print(f"WARNING: 내용 사이에 높이 {best/H:.0%}의 빈 띠가 있습니다. 간격을 줄이거나 내용을 키우세요.")
