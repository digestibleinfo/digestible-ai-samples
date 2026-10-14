"""Builds long_document.txt: a made-up staff handbook (about 25 000 tokens) with five facts hidden at
different depths, for the long-document test.

    python make_long.py
"""

import random
from pathlib import Path

random.seed(3)
TOPICS = ["leave", "travel", "equipment", "meetings", "security", "training", "expenses", "health and safety",
          "communication", "parking", "visitors", "IT support", "customer service", "procurement", "records"]
VERBS = ["must", "should", "may", "are expected to", "are encouraged to"]
ACTIONS = ["submit a request through the staff portal", "inform their line manager in writing", "keep a copy of all receipts",
           "complete the relevant form before the end of the month", "follow the procedure in the appendix",
           "check the notice board for updates", "ask the HR office for guidance", "record the details in the shared register",
           "wait for written approval before going ahead", "report any problems to the facilities team"]
WHEN = ["at least five working days in advance", "as soon as reasonably possible", "before the start of each quarter",
        "within two working days", "during normal office hours", "whenever circumstances change"]
FACTS = {
    3: "The access code for the storeroom on the ground floor is 4417, and it is changed every January.",
    12: "Lindiwe Khoza is the fire marshal on the second floor and leads the evacuation drill each March.",
    22: "Every permanent employee receives 5 days of paid study leave per year, which cannot be carried over.",
    31: "The company's backup generator is serviced every six months by its supplier, Ubuntu Power Systems.",
    40: "Salaries are paid on the 25th day of each month, or on the last working day before it.",
}
sections = []
for n in range(1, 46):
    topic = random.choice(TOPICS)
    paras = []
    for _ in range(6):
        sentences = [f"Staff {random.choice(VERBS)} {random.choice(ACTIONS)} {random.choice(WHEN)}." for _ in range(6)]
        paras.append(" ".join(sentences))
    if n in FACTS:
        paras.insert(random.randint(1, 4), FACTS[n])
    sections.append(f"SECTION {n}: {topic.upper()}\n\n" + "\n\n".join(paras))
text = "ACME HOLDINGS STAFF HANDBOOK (made up for a test)\n\n" + "\n\n".join(sections)
Path("long_document.txt").write_text(text, encoding="utf-8")
print(len(text), "characters,", len(text.split()), "words")
