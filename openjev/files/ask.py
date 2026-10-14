"""The model card's own example: a checkout page, three possible actions. Prints the probability
OpenJev gives each option.

    python ask.py
"""

from decide import choice

state = "A checkout page shows: Subtotal $40, Shipping $5, a Place order button, and a Coupon field."
best, probs, seconds = choice(state, "Which action completes the purchase?",
                              ["click_coupon: type a coupon", "click_place_order: click Place order", "go_back: return to cart"])
for option, p in sorted(probs.items(), key=lambda x: -x[1]):
    print(f"{p:7.2%}  {option}")
print(f"\nAnswer: {best}   ({seconds:.2f} s)")
