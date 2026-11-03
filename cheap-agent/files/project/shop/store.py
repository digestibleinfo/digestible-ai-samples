"""Item storage: a JSON file of items with name, category, price (cents) and stock."""
import json


class Store:
    def __init__(self, path):
        self.path = path
        self._items = None

    def items(self):
        if self._items is None:
            with open(self.path) as f:
                self._items = json.load(f)
        return list(self._items)

    def by_category(self, category):
        return [i for i in self.items() if i["category"] == category]

    def in_stock(self):
        return [i for i in self.items() if i["stock"] > 0]
