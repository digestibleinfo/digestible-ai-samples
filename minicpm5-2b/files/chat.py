"""Ask MiniCPM5-2B one question (through llama-server) and see how fast it answers.

    python chat.py "Your question"
    python chat.py "Your question" --nothink   (skip the thinking step)
"""

import sys

from mini import ask

question = next((a for a in sys.argv[1:] if not a.startswith("--")), "Who are you? Please briefly introduce yourself.")
answer, seconds, tokens = ask(question, think="--nothink" not in sys.argv, max_new_tokens=2048)
print(answer)
print(f"\n{tokens} tokens in {seconds:.1f} s = {tokens / seconds:.1f} tokens per second")
