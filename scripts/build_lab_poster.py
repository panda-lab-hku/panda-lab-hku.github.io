"""Build the self-contained PANDA Lab HTML poster and export its A2 PDF.

python scripts/build_lab_poster.py
python scripts/build_lab_poster.py --export-only   # preserve direct HTML edits

Requires Pillow, opencv-python, fonttools[woff], playwright, pypdf and Chrome.
The default fonts are the installed OFL Noto Sans/Serif SC variable fonts.
"""
import argparse
import base64
import io
import json
import os
import re
from pathlib import Path
import shutil
import sys

from PIL import Image
import cv2
import numpy as np
from fontTools import subset
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output/pdf"
TEMP = ROOT / "tmp/pdfs"
HTML = OUTPUT / "panda-lab-poster.html"
PDF = OUTPUT / "panda-lab-poster-A2.pdf"
TEMPLATE = ROOT / "scripts/poster_template.html"


def data_uri(data, mime):
    return "data:" + mime + ";base64," + base64.b64encode(data).decode("ascii")


def image_uri(path):
    path = Path(path)
    return data_uri(path.read_bytes(), "image/png" if path.suffix == ".png" else "image/jpeg")


def frame(name, seconds, crop=None, blend_hero=False):
    cap = cv2.VideoCapture(str(ROOT / "assets" / (name + ".mp4")))
    cap.set(cv2.CAP_PROP_POS_MSEC, seconds * 1000)
    ok, value = cap.read()
    cap.release()
    if not ok:
        raise RuntimeError(f"Cannot extract {name} at {seconds}s")
    im = Image.fromarray(cv2.cvtColor(value, cv2.COLOR_BGR2RGB))
    if crop:
        im = im.crop(crop)
    if blend_hero:
        # Bake photographic gradients into the raster to prevent PDF stitching
        # seams between transparent browser layers. All poster text stays vector.
        height = round(im.width * 483 / 930)
        im = im.crop((0, 0, im.width, height))
        x = np.linspace(0, 1, im.width)
        y = np.linspace(0, 1, im.height)
        horizontal = np.interp(x, [0, .14, .35, .63, 1], [1, 235/255, 80/255, 0, 0])
        upper = np.interp(y, [0, .12, 1], [1, 0, 0])
        lower = np.interp(y, [0, .73, 1], [0, 0, 220/255])
        alpha = 1 - (1-horizontal[None, :]) * (1-upper[:, None]) * (1-lower[:, None])
        alpha[:, :2] = 1
        foreground = np.array([9, 47, 41], dtype=np.float32)
        pixels = np.array(im, dtype=np.float32) * (1-alpha[:, :, None]) + foreground * alpha[:, :, None]
        im = Image.fromarray(np.round(pixels).astype(np.uint8))
    path = TEMP / ("poster-" + name + (".png" if blend_hero else ".jpg"))
    im.save(path, quality=96, subsampling=0)
    return image_uri(path)


def font_uri(path, text):
    font = TTFont(path)
    opts = subset.Options()
    opts.flavor = "woff2"
    opts.recalc_bounds = True
    worker = subset.Subsetter(options=opts)
    worker.populate(text=text)
    worker.subset(font)
    font.flavor = "woff2"
    data = io.BytesIO()
    font.save(data)
    return data_uri(data.getvalue(), "font/woff2")


def qr_uri():
    matrix = cv2.QRCodeEncoder_create().encode("https://panda-lab-hku.github.io/")
    # OpenCV provides a two-module border; expand it to the four-module quiet zone.
    matrix = cv2.copyMakeBorder(matrix, 2, 2, 2, 2, cv2.BORDER_CONSTANT, value=255)
    im = Image.fromarray(matrix).resize((matrix.shape[1] * 16, matrix.shape[0] * 16), Image.Resampling.NEAREST)
    path = TEMP / "poster-qr.png"
    im.save(path)
    decoded, _, _ = cv2.QRCodeDetector().detectAndDecode(cv2.imread(str(path)))
    if decoded != "https://panda-lab-hku.github.io/":
        raise RuntimeError("QR code verification failed")
    return image_uri(path)


def build():
    html = TEMPLATE.read_text(encoding="utf-8")
    replacements = {
        "__FONT_SANS__": font_uri("C:/Windows/Fonts/NotoSansSC-VF.ttf", html),
        "__FONT_SERIF__": font_uri("C:/Windows/Fonts/NotoSerifSC-VF.ttf", "Lab"),
        "__LOGO__": image_uri(OUTPUT / "assets/hku-ai-logo.png"),
        "__PORTRAIT__": image_uri(ROOT / "people/photo/jpan_full.jpg"),
        "__HERO__": frame("rapid", 7.5, blend_hero=True),
        "__ALOHA__": frame("aloha", 9.0),
        "__GAUSS__": frame("gausmi", 14.5, (250, 190, 2480, 1440)),
        "__SOFT__": frame("softmimic", 3.7, (92, 46, 442, 670)),
        "__QR__": qr_uri(),
    }
    for key, value in replacements.items():
        html = html.replace(key, value)
    HTML.write_text(html, encoding="utf-8")


def export(chrome):
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        # Reuse an existing local tool installation when available.
        for folder in ["pears-demo-test-tools", "pears-browser-check"]:
            candidate = Path(os.environ.get("LOCALAPPDATA", "")) / "Temp" / folder
            if (candidate / "playwright").exists():
                sys.path.insert(0, str(candidate))
                break
        from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=chrome, headless=True)
        page = browser.new_page(viewport={"width": 1500, "height": 2200}, device_scale_factor=1)
        page.goto(HTML.as_uri(), wait_until="load")
        page.evaluate("document.fonts.ready")
        page.wait_for_function("Array.from(document.images).every(i => i.complete && i.naturalWidth > 0)")
        checks = page.evaluate("""() => ({
          missingImages: [...document.images].filter(i => !i.naturalWidth).map(i => i.alt),
          overflow: [...document.querySelectorAll('h1,h2,h3,p,.venue-line,.robot-list,.research-item,.pub,.footer')]
            .filter(e => e.scrollWidth > e.clientWidth + 2 || e.scrollHeight > e.clientHeight + 2)
            .map(e => ({className:e.className, text:e.innerText})),
          fontsLoaded: document.fonts.status,
          poster: {width:document.querySelector('.poster').offsetWidth, height:document.querySelector('.poster').offsetHeight}
        })""")
        page.locator(".poster").screenshot(path=str(TEMP / "html-preview.png"))
        page.emulate_media(media="print")
        page.pdf(path=str(PDF), prefer_css_page_size=True, print_background=True,
                 margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
                 display_header_footer=False, tagged=True)
        browser.close()
    from pypdf import PdfReader, PdfWriter
    # Chromium rounds metric paper sizes slightly. Normalize to exact A2 geometry.
    writer = PdfWriter(clone_from=PDF)
    for pdf_page in writer.pages:
        pdf_page.scale_to(420 * 72 / 25.4, 594 * 72 / 25.4)
    writer.add_metadata({"/Title": "PANDA Lab | HKU | Research Profile", "/Author": "PANDA Lab, The University of Hong Kong", "/Subject": "A2 research group introduction poster"})
    with open(TEMP / "normalized.pdf", "wb") as stream:
        writer.write(stream)
    shutil.copyfile(TEMP / "normalized.pdf", PDF)
    reader = PdfReader(PDF)
    checks["pdf_pages"] = len(reader.pages)
    checks["pdf_size_mm"] = [round(float(v) * 25.4 / 72, 2) for v in reader.pages[0].mediabox[2:]]
    text = "\n".join(page.extract_text() for page in reader.pages)
    checks["required_text"] = {s: s in text for s in ["PANDA", "Jia Pan", "Nature", "IJRR", "BIM-Loc", "NeuPAN", "UR", "Franka", "ALOHA", "G1", "LimX Oli", "Tron", "The University of Hong Kong", "School of Computing and Data Science", "Department of AI and Data Science", "Embodied AI"]}
    checks["non_english_text"] = bool(re.search(r"[\u3400-\u9fff]", text + HTML.read_text(encoding="utf-8")))
    checks["pdf_link_count"] = sum(len(page.get("/Annots", [])) for page in reader.pages)
    (TEMP / "verification.json").write_text(json.dumps(checks, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(checks, ensure_ascii=False, indent=2))
    if checks["missingImages"] or checks["overflow"] or checks["non_english_text"] or len(reader.pages) != 1 or not all(checks["required_text"].values()):
        raise RuntimeError("Poster verification requires attention")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export-only", action="store_true")
    parser.add_argument("--chrome", default=shutil.which("chrome") or "C:/Program Files/Google/Chrome/Application/chrome.exe")
    args = parser.parse_args()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    TEMP.mkdir(parents=True, exist_ok=True)
    if not args.export_only:
        build()
    export(args.chrome)


if __name__ == "__main__":
    main()
