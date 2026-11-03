import json
from shop.store import Store
from shop.report import money, total_value


def make(tmp_path):
    p = tmp_path / "items.json"
    p.write_text(json.dumps([
        {"name": "pen", "category": "office", "price": 150, "stock": 10},
        {"name": "desk", "category": "furniture", "price": 12000, "stock": 0},
        {"name": "lamp", "category": "furniture", "price": 3000, "stock": 4},
        {"name": "ink", "category": "office", "price": 800, "stock": 2},
    ]))
    return str(p)


def test_store(tmp_path):
    s = Store(make(tmp_path))
    assert len(s.by_category("office")) == 2


def test_money():
    assert money(1234) == "$12.34"
    assert total_value([{"price": 100, "stock": 3}]) == 300
