import contextlib
import io
import os
import re
import sys
import tempfile
import time
from pathlib import Path

import fitz  # PyMuPDF
import torch
from transformers import AutoModel, AutoTokenizer

pdf = sys.argv[1]  # for example: scans\lease_scanned.pdf
Path("out").mkdir(exist_ok=True)


def pdf_to_images(path, dpi=300):
    doc = fitz.open(path)
    folder = tempfile.mkdtemp(prefix="pdf_ocr_")
    paths = []
    for i, page in enumerate(doc):
        out = os.path.join(folder, f"page_{i + 1:04d}.png")
        page.get_pixmap(matrix=fitz.Matrix(dpi / 72, dpi / 72)).save(out)
        paths.append(out)
    return paths


def clean(raw):
    text = re.sub(r"<\|det\|>.*?<\|/det\|>", "", raw)
    text = re.sub(r"</tr>", "\n", text)
    text = re.sub(r"</t[dh]>", " | ", text)
    text = re.sub(r"<[^>]+>", "", text)
    return "\n".join(line.strip(" |") for line in text.splitlines() if line.strip(" |")).strip()


tokenizer = AutoTokenizer.from_pretrained("baidu/Unlimited-OCR", trust_remote_code=True)
model = AutoModel.from_pretrained("baidu/Unlimited-OCR", trust_remote_code=True, use_safetensors=True, dtype=torch.bfloat16)
model = model.eval().cuda()

pages = pdf_to_images(pdf)
start = time.perf_counter()
printed = io.StringIO()
with contextlib.redirect_stdout(printed):
    model.infer_multi(
        tokenizer, prompt="<image>Multi page parsing.", image_files=pages, output_path="out", image_size=1024,
        max_length=32768, no_repeat_ngram_size=35, ngram_window=1024,
    )
text = clean(printed.getvalue())
name = Path(pdf).stem
Path(f"out/{name}.txt").write_text(text, encoding="utf-8")
print(f"{name}: {len(pages)} pages read in {time.perf_counter() - start:.1f} s, {len(text)} characters, saved to out\\{name}.txt")
