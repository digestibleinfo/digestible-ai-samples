from shop.cache import LRUCache
from shop.pricing import PriceBook
from tests.test_base import make
from shop.store import Store
def test_capacity():
    c = LRUCache(2)
    c.put("a", 1); c.put("b", 2); c.put("c", 3)
    assert len(c) == 2 and c.get("a") is None
def test_recent_use_keeps():
    c = LRUCache(2)
    c.put("a", 1); c.put("b", 2); c.get("a"); c.put("c", 3)
    assert c.get("a") == 1 and c.get("b") is None
def test_falsy_value_cached():
    c = LRUCache(2); c.put("z", 0)
    assert c.get("z") == 0 and c.hits == 1
def test_pricebook(tmp_path):
    pb = PriceBook(Store(make(tmp_path)), capacity=2)
    for n in ["pen", "desk", "lamp"]: pb.price(n)
    assert len(pb.cache) == 2
    pb.price("lamp"); pb.price("lamp")
    assert pb.cache.hits == 2
def test_free_item_cached(tmp_path):
    import json
    p = tmp_path / "f.json"
    p.write_text(json.dumps([{"name": "gift", "category": "x", "price": 0, "stock": 1}]))
    pb = PriceBook(Store(str(p)))
    pb.price("gift"); pb.price("gift")
    assert pb.cache.hits == 1 and pb.cache.misses == 1
