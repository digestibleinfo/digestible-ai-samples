"""Command line: python -m shop.cli ITEMS.json [--category NAME] [--in-stock]"""
import argparse

from shop.report import money, table, total_value
from shop.store import Store


def main(argv=None):
    p = argparse.ArgumentParser(prog="shop")
    p.add_argument("path")
    p.add_argument("--category")
    p.add_argument("--in-stock", action="store_true")
    a = p.parse_args(argv)
    store = Store(a.path)
    items = store.items()
    if a.category:
        items = store.by_category(a.category)
    if a.in_stock:
        items = [i for i in items if i["stock"] > 0]
    print(table(items))
    print("total", money(total_value(items)))


if __name__ == "__main__":
    main()
