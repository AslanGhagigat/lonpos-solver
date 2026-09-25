def shape(piece):
    return len(piece), len(piece[0])


def convert_to_coordinate(piece):
    coordinate = []
    x, y = shape(piece)
    for i in range(x):
        for j in range(y):
            if piece[i][j] != -1:
                coordinate.append((i, j))
    return coordinate


def normalize_coordinate(piece):
    x_min = min(i for i, j in piece)
    y_min = min(j for i, j in piece)
    return [(i - x_min, j - y_min) for i, j in piece]


def rotate(piece):
    new_coordinates = []
    for i, j in piece:
        new_coordinates.append((j, -i))
    new_coordinates = normalize_coordinate(new_coordinates)
    return new_coordinates


def mirror(piece):
    new_coordinates = []
    for i, j in piece:
        new_coordinates.append((i, -j))
    new_coordinates = normalize_coordinate(new_coordinates)
    return new_coordinates


def all_possible_pos(piece):
    seen = set()
    unique = []
    for _ in range(2):
        for _ in range(4):
            key = frozenset(piece)
            if key not in seen:
                seen.add(key)
                unique.append(piece)
            piece = rotate(piece)
        piece = mirror(piece)
    return unique


A = [[-1, -1, 0],
     [0,  0,  0]]
B = [[-1, 1, 1],
     [1,  1, 1]]
C = [[2, 2, 2, 2],
     [-1, -1, -1, 2]]
D = [[3, 3, 3, 3],
     [-1, -1, 3, -1]]
E = [[4, 4, 4, -1],
     [-1, -1, 4, 4]]
F = [[5, 5],
     [-1, 5]]
G = [[6, 6, 6],
     [-1, -1, 6],
     [-1, -1, 6]]
H = [[7, 7, -1],
     [-1, 7, 7],
     [-1, -1, 7]]
I = [[8, 8, 8],
     [8, -1, 8]]
J = [[9, 9, 9, 9]]
K = [[10, 10],
     [10, 10]]
L = [[-1, 11, -1],
     [11, 11, 11],
     [-1, 11, -1]]

PIECES = {}
PIECES['A'] = convert_to_coordinate(A)
PIECES['B'] = convert_to_coordinate(B)
PIECES['C'] = convert_to_coordinate(C)
PIECES['D'] = convert_to_coordinate(D)
PIECES['E'] = convert_to_coordinate(E)
PIECES['F'] = convert_to_coordinate(F)
PIECES['G'] = convert_to_coordinate(G)
PIECES['H'] = convert_to_coordinate(H)
PIECES['I'] = convert_to_coordinate(I)
PIECES['J'] = convert_to_coordinate(J)
PIECES['K'] = convert_to_coordinate(K)
PIECES['L'] = convert_to_coordinate(L)


def piece_mask(cells):
    mask = 0
    for i, j in cells:
        mask |= 1 << (i * 11 + j)
    return mask

PIECES_ID = {
    'A': 0,
    'B': 1,
    'C': 2,
    'D': 3,
    'E': 4,
    'F': 5,
    'G': 6,
    'H': 7,
    'I': 8,
    'J': 9,
    'K': 10,
    'L': 11,
}

def generate_placements(PIECES):
    placements = {}

    for piece_name in PIECES:
        piece = PIECES[piece_name]
        positions = all_possible_pos(piece)
        placements[piece_name] = []
        for position in positions:
            x_max = max(i for i, j in position)
            y_max = max(j for i, j in position)
            for x_offset in range(0, 5 - x_max):
                for y_offset in range(0, 11 - y_max):
                    cells = []
                    # mask = 0
                    
                    for i, j in position:
                        abs_x = i + x_offset
                        abs_y = j + y_offset
                        cells.append((abs_x, abs_y))
                        # mask |= 1 << (abs_x * 11 + abs_y)
                    # print(cells)
                    # print(piece_mask(cells))
                    repl = {
                        'piece': piece_name,
                        'piece_id': PIECES_ID[piece_name],
                        # 'variant': position,
                        'offset': (x_offset, y_offset),
                        'cells': cells,
                        'mask': piece_mask(cells)
                    }
                    placements[piece_name].append(repl)
    return placements


placements = generate_placements(PIECES)
total = sum(len(placements[p]) for p in placements)

if __name__ == '__main__':
    print(f"Total placements: {total}")
    for name in PIECES:
        print(f"  {name}: {len(placements[name])} placements, "
              f"{len(all_possible_pos(PIECES[name]))} unique variants")
    print(f"Total cells: {sum(len(PIECES[p]) for p in PIECES)}")
