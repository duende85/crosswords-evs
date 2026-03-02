# -*- coding: utf-8 -*-
"""
Optimized Crossword Solver
Forward checking only on crossing slots + MRV heuristic
"""

import time
from collections import defaultdict, namedtuple

# ------------ CONFIG -----------------

DICT_FILE = "words_isg.txt"

GRID = [
    [' ',' ', ' ', ' ', ' ', ' '],
    ['#',' ', '#', ' ', '#', '#'],
    [' ',' ', ' ', ' ', ' ', ' '],
    ['#',' ', '#', ' ', '#', ' '],
    [' ',' ', ' ', ' ', ' ', ' '],
    ['#',' ', '#', ' ', '#', ' ']
]

MIN_LEN, MAX_LEN = 4, 6
MAX_SOL = 10

# -------------------------------------

Slot = namedtuple("Slot", "row col length dir")

ALLOWED = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ")

# -------- LOAD DICTIONARY --------

with open(DICT_FILE, encoding="utf-8") as f:
    WORDS = [
        w.strip().upper()
        for w in f
        if MIN_LEN <= len(w.strip()) <= MAX_LEN
        and set(w.strip().upper()) <= ALLOWED
    ]

WORDS = set(WORDS)

by_len = defaultdict(set)
for w in WORDS:
    by_len[len(w)].add(w)

# -------- SLOT DETECTION --------

def get_slots(grid):
    ROWS, COLS = len(grid), len(grid[0])
    out = []

    # Horizontal
    for r in range(ROWS):
        c = 0
        while c < COLS:
            if grid[r][c] != '#':
                s = c
                while c < COLS and grid[r][c] != '#':
                    c += 1
                if c - s > 1:
                    out.append(Slot(r, s, c - s, 'H'))
            else:
                c += 1

    # Vertical
    for c in range(COLS):
        r = 0
        while r < ROWS:
            if grid[r][c] != '#':
                s = r
                while r < ROWS and grid[r][c] != '#':
                    r += 1
                if r - s > 1:
                    out.append(Slot(s, c, r - s, 'V'))
            else:
                r += 1

    return out


SLOTS = get_slots(GRID)
SLOTS.sort(key=lambda s: -s.length)

# -------- BUILD CROSSING MAP --------

crossings = defaultdict(list)

for i, a in enumerate(SLOTS):
    for j in range(i + 1, len(SLOTS)):
        b = SLOTS[j]
        for ia in range(a.length):
            ra, ca = (a.row, a.col + ia) if a.dir == 'H' else (a.row + ia, a.col)
            for ib in range(b.length):
                rb, cb = (b.row, b.col + ib) if b.dir == 'H' else (b.row + ib, b.col)
                if ra == rb and ca == cb:
                    crossings[i].append(j)
                    crossings[j].append(i)

# -------- INITIAL CANDIDATES --------

def init_candidates():
    return {sid: set(by_len[slot.length]) for sid, slot in enumerate(SLOTS)}

cand = init_candidates()
filled = set()
used = set()
solutions = []

# -------- HEURISTIC (MRV) --------

def select_slot():
    best = None
    best_size = None

    for sid in range(len(SLOTS)):
        if sid in filled:
            continue
        size = len(cand[sid])
        if size == 0:
            return None
        if best is None or size < best_size:
            best = sid
            best_size = size

    return best

# -------- ASSIGN WITH FORWARD CHECKING --------

def assign(word, sid, changed_cells, changed_cand):
    slot = SLOTS[sid]
    r, c, L, d = slot
    coords = [(r, c+i) if d == 'H' else (r+i, c) for i in range(L)]

    # Write word
    for i, ch in enumerate(word):
        x, y = coords[i]
        if GRID[x][y] == ' ':
            GRID[x][y] = ch
            changed_cells.append((x, y))

    # Forward check only crossing slots
    for oid in crossings[sid]:
        if oid in filled:
            continue

        other = SLOTS[oid]
        r2, c2, L2, d2 = other
        coords2 = [(r2, c2+i) if d2 == 'H' else (r2+i, c2) for i in range(L2)]

        pattern = [GRID[x][y] if GRID[x][y] != ' ' else None for x, y in coords2]

        prev = cand[oid]
        filtered = set()

        for w in prev:
            for i in range(L2):
                if pattern[i] is not None and w[i] != pattern[i]:
                    break
            else:
                filtered.add(w)

        if filtered != prev:
            changed_cand.append((oid, prev))
            cand[oid] = filtered
            if not filtered:
                return False

    return True


def undo(changed_cells, changed_cand):
    for x, y in changed_cells:
        GRID[x][y] = ' '
    for oid, old in reversed(changed_cand):
        cand[oid] = old

# -------- DFS --------

def dfs(depth=0):
    if len(solutions) >= MAX_SOL:
        return True

    if depth == len(SLOTS):

        # Final validation safeguard
        for sid, slot in enumerate(SLOTS):
            r, c, L, d = slot
            word = ''
            for i in range(L):
                x, y = (r, c+i) if d == 'H' else (r+i, c)
                word += GRID[x][y]
            if word not in WORDS:
                return False

        solutions.append([''.join(r) for r in GRID])

        print(f"\n-- Solution {len(solutions)} --")
        for row in GRID:
            print(''.join(row))

        return False

    sid = select_slot()
    if sid is None:
        return False

    for word in sorted(cand[sid]):
        if word in used:
            continue

        changed_cells = []
        changed_cand = []

        filled.add(sid)

        if not assign(word, sid, changed_cells, changed_cand):
            filled.remove(sid)
            undo(changed_cells, changed_cand)
            continue

        used.add(word)

        if dfs(depth+1):
            return True

        used.remove(word)
        filled.remove(sid)
        undo(changed_cells, changed_cand)

    return False


# -------- RUN --------

if __name__ == "__main__":
    t0 = time.time()

    dfs()

    print(f"\nTotal solutions: {len(solutions)}")
    print(f"Time: {time.time() - t0:.2f}s")
