import contextlib
import glob
import io
import re
import sys
import time
from pathlib import Path

import torch
from transformers import AutoModel, AutoTokenizer

# python read_page.py scans\receipt_*.jpg scans\invoice_*.jpg
# python read_page.py notag scans\hard_receipt_*.jpg     <- the same, with the prompt typed wrongly (see the video)
args = sys.argv[1:]
notag = bool(args) and args[0] == "notag"
patterns = args[1:] if notag else args
images = [path for pattern in patterns for path in sorted(glob.glob(pattern))]
PROMPT = "document parsing." if notag else "<image>document parsing."
Path("out").mkdir(exist_ok=True)


def clean(raw):
    """Remove the position tags, and turn each HTML table into plain rows: cell | cell | cell."""
    text = re.sub(r"<\|det\|>.*?<\|/det\|>", "", raw)
    text = re.sub(r"</tr>", "\n", text)
    text = re.sub(r"</t[dh]>", " | ", text)
    text = re.sub(r"<[^>]+>", "", text)
    return "\n".join(line.strip(" |") for line in text.splitlines() if line.strip(" |")).strip()


start = time.perf_counter()
tokenizer = AutoTokenizer.from_pretrained("baidu/Unlimited-OCR", trust_remote_code=True)
model = AutoModel.from_pretrained("baidu/Unlimited-OCR", trust_remote_code=True, use_safetensors=True, dtype=torch.bfloat16)
model = model.eval().cuda()
print(f"Model loaded in {time.perf_counter() - start:.0f} s. Prompt: {PROMPT!r}")

for image in images:
    start = time.perf_counter()
    printed = io.StringIO()
    with contextlib.redirect_stdout(printed):  # the model prints its answer instead of returning it
        model.infer(
            tokenizer, prompt=PROMPT, image_file=image, output_path="out",
            base_size=1024, image_size=640, crop_mode=True, max_length=32768,
            no_repeat_ngram_size=35, ngram_window=128,
        )
    text = clean(printed.getvalue())
    name = Path(image).stem + ("_notag" if notag else "")
    Path(f"out/{name}.txt").write_text(text, encoding="utf-8")
    print(f"{name}: read in {time.perf_counter() - start:.1f} s, {len(text)} characters")
