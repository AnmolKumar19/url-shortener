"""
Short-code generation strategy.

We encode the database auto-increment ID as base62 (0-9, a-z, A-Z). This is
the same idea services like early bit.ly used, and it's a deliberate choice
over "random 6 chars + hope for no collision":

  - Guaranteed unique: the ID is unique by definition (primary key), so the
    encoded code is unique too. No collision-retry loop needed.
  - Short: base62 packs a lot of range into few characters. 3 chars already
    covers 62^3 = ~238k links; 6 chars covers 62^6 = ~56 billion.
  - Sequential-but-not-obvious: codes aren't purely sequential digits, which
    avoids trivially enumerable short URLs like /1, /2, /3...

Trade-off worth mentioning in an interview: because it's derived from an
incrementing ID, codes ARE still somewhat guessable/orderable if someone
studies enough of them (you can infer roughly when a link was created
relative to others). A pure random-hash scheme avoids that at the cost of
needing collision detection. For a portfolio project, base62-from-ID is the
right trade: simpler, no collision retries, still short.
"""

ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
BASE = len(ALPHABET)


def encode_base62(num: int) -> str:
    if num == 0:
        return ALPHABET[0]
    chars = []
    while num > 0:
        num, rem = divmod(num, BASE)
        chars.append(ALPHABET[rem])
    return "".join(reversed(chars))


def decode_base62(code: str) -> int:
    num = 0
    for char in code:
        num = num * BASE + ALPHABET.index(char)
    return num
