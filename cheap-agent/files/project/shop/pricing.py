"""Price lookup that caches results from the store."""
from shop.cache import LRUCache


class PriceBook:
    def __init__(self, store, capacity=3):
        self.store = store
        self.cache = LRUCache(capacity)

    def price(self, name):
        cached = self.cache.get(name)
        if cached:
            return cached
        for item in self.store.items():
            if item["name"] == name:
                self.cache.put(name, item["price"])
                return item["price"]
        raise KeyError(name)
