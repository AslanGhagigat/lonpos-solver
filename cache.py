"""Solution cache — global pool of every solution ever found."""

import json
import os

CACHE_PATH = 'solutions_cache.jsonl'
CELLS = 55
EMPTY_CHAR = '.'


def solution_to_string(solution):
    arr = [EMPTY_CHAR] * CELLS
    for p in solution:
        name = p['piece']
        for (r, c) in p['cells']:
            arr[r * 11 + c] = name
    return ''.join(arr)


def string_to_solution(s):
    by_piece = {}
    for i, ch in enumerate(s):
        if ch == EMPTY_CHAR:
            continue
        r, c = divmod(i, 11)
        by_piece.setdefault(ch, []).append((r, c))
    return [{'piece': name, 'cells': by_piece[name]}
            for name in sorted(by_piece.keys())]


def is_compatible(sol_string, locked_pieces):
    for p in locked_pieces:
        name = p['piece']
        for (r, c) in p['cells']:
            if sol_string[r * 11 + c] != name:
                return False
    return True


def load_cache():
    if not os.path.exists(CACHE_PATH):
        return []
    out = []
    with open(CACHE_PATH, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line)['s'])
            except (json.JSONDecodeError, KeyError):
                continue
    return out


def append_to_cache(sol_string):
    with open(CACHE_PATH, 'a', encoding='utf-8') as f:
        f.write(json.dumps({'s': sol_string}, separators=(',', ':')) + '\n')
