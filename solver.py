"""
Backtracking solver for the Lonpos 5x11 rectangular puzzle.

Public API
----------
solve(placed_pieces)                -> generator of solutions
solve_one(placed_pieces)            -> first solution or None
count_solutions(placed_pieces, ...) -> int

Each solution is a list of placement dicts (same format as in pieces.placements):
    {'piece', 'piece_id', 'offset', 'cells', 'mask'}
"""

from pieces import PIECES, placements

ROWS = 5
COLUMNS = 11
N_CELLS = ROWS * COLUMNS          # 55
FULL_MASK = (1 << N_CELLS) - 1


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def placed_pieces_to_mask(placed_pieces):
    """Convert user-placed pieces to (bitmask, set of used piece names)."""
    mask = 0
    used = set()
    for pp in placed_pieces:
        for (r, c) in pp['cells']:
            mask |= 1 << (r * COLUMNS + c)
        used.add(pp['piece'])
    return mask, used


def filter_placements(forbidden_mask):
    """Drop every placement that overlaps forbidden_mask."""
    out = {}
    for name, lst in placements.items():
        out[name] = [p for p in lst if not (p['mask'] & forbidden_mask)]
    return out


def build_cell_index(filtered):
    """For every board cell, list of placements that cover it."""
    index = [[] for _ in range(N_CELLS)]
    for lst in filtered.values():
        for p in lst:
            for (r, c) in p['cells']:
                index[r * COLUMNS + c].append(p)
    # Bigger pieces first — improves pruning.
    for i in range(N_CELLS):
        index[i].sort(key=lambda p: -len(p['cells']))
    return index


# ---------------------------------------------------------------------------
# Solver
# ---------------------------------------------------------------------------
def solve(placed_pieces):
    """
    Generator. Yields one solution at a time.

    Each solution is a list of placement dicts for the pieces that were NOT
    pre-placed by the user.
    """
    base_mask, used = placed_pieces_to_mask(placed_pieces)
    remaining = set(PIECES.keys()) - used

    filtered = filter_placements(base_mask)

    # Quick infeasibility check
    for name in remaining:
        if not filtered[name]:
            return

    cell_index = build_cell_index(filtered)

    def backtrack(mask, remaining, chosen):
        if mask == FULL_MASK:
            yield list(chosen)
            return

        # MRV: pick the empty cell with the fewest legal placements.
        best_cell = -1
        best_options = None
        for i in range(N_CELLS):
            if (mask >> i) & 1:
                continue
            options = [p for p in cell_index[i]
                       if p['piece'] in remaining and not (p['mask'] & mask)]
            if best_options is None or len(options) < len(best_options):
                best_options = options
                best_cell = i
                if not options:
                    break

        if not best_options:
            return

        for p in best_options:
            name = p['piece']
            remaining.remove(name)
            chosen.append(p)
            yield from backtrack(mask | p['mask'], remaining, chosen)
            chosen.pop()
            remaining.add(name)

    yield from backtrack(base_mask, remaining, [])


def solve_one(placed_pieces):
    """Return the first solution, or None if there is none."""
    for sol in solve(placed_pieces):
        return sol
    return None


def count_solutions(placed_pieces, limit=None):
    """Count solutions (stops early if limit is reached)."""
    n = 0
    for _ in solve(placed_pieces):
        n += 1
        if limit is not None and n >= limit:
            break
    return n
