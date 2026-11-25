"""Builds the commentary script: one sentence per line plus its start offset in the recording.
Only general, true statements about the setup and the game's rules, plus clock lines. No claims about outcomes."""
import json
from pathlib import Path

ONES = "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen".split()
TENS = {20: "twenty", 30: "thirty", 40: "forty", 50: "fifty", 60: "sixty", 70: "seventy", 80: "eighty", 90: "ninety", 100: "one hundred"}


def words(n):
    if n > 100: return "one hundred " + words(n - 100)
    if n < 20: return ONES[n]
    t, o = divmod(n, 10)
    return TENS[n] if n in TENS else TENS[t * 10] + " " + ONES[o]


content = [
    "Welcome to a long strategy game played entirely by computer players, with nobody touching the mouse.",
    "Six bots share this round map, and each one is trying to build the biggest economy.",
    "The game is called zero A D, and it is a free, open source game about ancient civilizations.",
    "Every bot starts with a few workers, a town centre and a handful of soldiers.",
    "The first job for any bot is food, so look for workers around berry bushes and farms.",
    "Wood comes next, because houses, barracks and fields all need timber.",
    "In this view you can see a stone wall, a tower and a large field of farms, all built by the bots.",
    "Houses matter a lot, because a bot cannot train more workers than its houses allow.",
    "Stone and metal are needed later, for towers, fortresses and better soldiers.",
    "Each civilization in this game has its own buildings and its own special units.",
    "Soldiers train in barracks, and most bots keep more than one barracks running.",
    "The bots in this round are all the same kind of computer player, set to the same difficulty.",
    "A strong bot expands to new spots on the map and builds more town centres.",
    "Watch the small round map in the corner, it shows where every player has built.",
    "Forests run out, so workers keep walking further to cut the next tree.",
    "Farms never run out, but each field only feeds a few workers at a time.",
    "Markets let a player trade one resource for another, at a worse rate each time.",
    "Towers watch over a base, and soldiers can garrison inside to shoot arrows from safety.",
    "Archers, spearmen and swordsmen make up the first armies, each good against something different.",
    "Cavalry is fast, so it often raids the workers of a neighbour.",
    "When two armies meet, you can see small groups of soldiers charging and breaking apart.",
    "Healers and champions come later, once a player has reached a higher age.",
    "A player advances through ages by paying resources, and each age unlocks stronger buildings.",
    "Siege weapons, like catapults, are used to knock down walls and fortresses.",
    "A bot that has lost its town centre has to rebuild before it can grow again.",
    "The game has no end condition in this round, so it keeps running until we stop recording.",
    "Because nothing ends the game, the bots keep trading blows and rebuilding for hours.",
    "The terrain on this map is mostly savanna, with scattered trees and open grass.",
    "Wild animals roam the map, and workers hunt them for a quick supply of food.",
    "Every bot works out what to build next by looking at its own resources and its neighbours.",
    "The recording is one single take of the screen, with no cuts and no edits.",
    "There is no sound from the game itself, only this commentary track.",
    "If you watch for a while, the bots look busy, but most of the work is plain gathering.",
    "Big battles are a small part of the time, and quiet building makes up the rest.",
    "Walls can slow an attack, but a bot has to decide to build them first.",
    "Temples train healers, and docks build ships, but this map has very little water.",
    "Workers carry only a small load, so every trip back to a drop site counts.",
    "Dropping off wood near the forest saves a lot of walking, so smart bots build storehouses close by.",
    "When a building is destroyed, the workers nearby usually run to a safe place.",
    "A single big fight can change the whole picture of the game in a few minutes.",
    "This kind of match is very long, which is why it makes a good test for tools that cut long videos.",
    "A good clip has a start, a point and an end, even if the game never says where they are.",
    "On screen the action keeps moving, but the talking only comes in short bursts.",
    "Remember that the people playing here are computer programs, so nothing here is live.",
    "The commentary is recorded after the match, and we place each sentence at a fixed time.",
    "Whatever you see next is the same single recording, from the first minute to the last.",
    "In a game like this, armies are built slowly and spent quickly.",
    "Farms are the steady part of the picture, because workers keep the same field for a long time.",
    "Bots decide on their own when to expand, so no two matches look the same.",
    "A tower like the one in view is cheap, and it covers the nearby fields.",
    "The wall in this view is there to slow down enemy soldiers who walk toward the base.",
    "A skirmish can start anywhere on the map, at any time.",
    "Houses keep appearing around the town centre, because every new worker needs a place to live.",
    "The bots keep going whether or not anyone is watching, which is exactly what makes them useful here.",
    "The match is nearly at the end of the recording now.",
    "Thanks for watching this very long bot match.",
]
lines, offs = [], []
t = 25.0
total = 7000.0
n_total = 80
step = (total - 150) / n_total
ci = 0
for i in range(n_total):
    off = 25 + i * step
    if i % 3 == 2:
        m = int(round(off / 60))
        text = f"The clock on this recording says minute {words(m)}."
    else:
        text = content[ci % len(content)]
        ci += 1
    lines.append(text); offs.append(round(off, 1))
cd = Path(r"WORKDIR\commentary"); cd.mkdir(exist_ok=True)
(cd / "narration.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
json.dump([{"i": i + 1, "t": o, "text": l} for i, (o, l) in enumerate(zip(offs, lines))],
          open(cd / "offsets.json", "w", encoding="utf-8"), indent=1)
print(len(lines), "lines; content used", ci, "of", len(content))

