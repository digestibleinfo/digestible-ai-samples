import csv, io, subprocess, sys
from tests.test_base import make
def run(*args):
    return subprocess.run([sys.executable, "-m", "shop.cli", *args], capture_output=True, text=True)
def test_csv_all(tmp_path):
    p = make(tmp_path); out = tmp_path / "o.csv"
    run(p, "--csv", str(out))
    rows = list(csv.DictReader(open(out, newline="")))
    assert [r["name"] for r in rows] == ["pen", "desk", "lamp", "ink"]
    assert list(rows[0].keys()) == ["name", "category", "price", "stock"]
    assert rows[0]["price"] == "1.50"
def test_csv_filter(tmp_path):
    p = make(tmp_path); out = tmp_path / "o.csv"
    run(p, "--category", "furniture", "--in-stock", "--csv", str(out))
    rows = list(csv.DictReader(open(out, newline="")))
    assert [r["name"] for r in rows] == ["lamp"]
def test_export_function(tmp_path):
    from shop.export import to_csv
    s = to_csv([{"name": "a", "category": "c", "price": 250, "stock": 1}])
    assert s.splitlines()[0] == "name,category,price,stock"
    assert s.splitlines()[1] == "a,c,2.50,1"
def test_store_filter():
    from shop.store import Store
    import inspect
    assert hasattr(Store, "filter")
