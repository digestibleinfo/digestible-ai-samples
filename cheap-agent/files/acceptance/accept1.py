import json, subprocess, sys
def test_sort_flag(tmp_path):
    from tests.test_base import make
    p = make(tmp_path)
    out = subprocess.run([sys.executable, "-m", "shop.cli", p, "--sort", "price"], capture_output=True, text=True).stdout
    names = [l.split()[0] for l in out.splitlines() if l and not l.startswith("total")]
    assert names == ["pen", "ink", "lamp", "desk"]
    out = subprocess.run([sys.executable, "-m", "shop.cli", p, "--sort", "price", "--reverse"], capture_output=True, text=True).stdout
    names = [l.split()[0] for l in out.splitlines() if l and not l.startswith("total")]
    assert names == ["desk", "lamp", "ink", "pen"]
def test_sort_name(tmp_path):
    from tests.test_base import make
    p = make(tmp_path)
    out = subprocess.run([sys.executable, "-m", "shop.cli", p, "--sort", "name"], capture_output=True, text=True).stdout
    names = [l.split()[0] for l in out.splitlines() if l and not l.startswith("total")]
    assert names == ["desk", "ink", "lamp", "pen"]
