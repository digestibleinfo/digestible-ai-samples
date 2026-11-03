"""Text reports over a list of items."""


def money(cents):
    return f"${cents / 100:.2f}"


def table(items):
    lines = [f"{i['name']:<12}{i['category']:<10}{money(i['price']):>8}{i['stock']:>5}" for i in items]
    return "\n".join(lines)


def total_value(items):
    return sum(i["price"] * i["stock"] for i in items)
