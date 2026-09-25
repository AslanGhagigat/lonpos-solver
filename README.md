# Lonpos Solver 🧩

A graphical solver for the **Lonpos 5×11** puzzle, written in Python.

Place the pieces on the board, hit **Solve**, and the program finds every
possible solution. Solutions are cached on disk so subsequent runs are
instant.

---

## ✨ Features

- 🎨 **Modern GUI** built with `CustomTkinter`
- 🧩 **Manual piece placement** with rotation and mirroring
- ⚡ **Backtracking solver** with MRV (minimum remaining values) heuristic
- 💾 **On-disk solution cache** (JSONL) for instant lookups on later runs
- 🔁 **Batch solving** — 10 quick solutions first, the rest streamed in the background
- 🧮 **Solve All** — enumerate all 371,020 possible solutions
- 💿 **Save / Load puzzles** as JSON
- 🔀 **Use Cache toggle** to bypass the cache when needed

---

## 📸 Screenshots

<!-- ![Main window](screenshots/empty-board.png)
![Solver in action](screenshots/solution-1.png)
![Load a saved puzzle](screenshots/loaded-puzzle.png)

<figure>
  <img src="screenshots/empty-board.png" alt="Main window" width="600"/>
  <figcaption>The main editor window.</figcaption>
</figure> -->

<!-- <figure>
  <img src="screenshots/empty-board.png" alt="Empty board" width="600"/>
  <figcaption>The main editor window with an empty board.</figcaption>
</figure>

<div style="display: flex; gap: 20px; justify-content: center; flex-wrap: wrap; margin-top: 20px;">
  <figure style="margin: 0; text-align: center;">
    <img src="screenshots/solution-1.png" alt="Solving a puzzle" width="360"/>
    <figcaption>Solving a custom puzzle.</figcaption>
  </figure>
  <figure style="margin: 0; text-align: center;">
    <img src="screenshots/loaded-puzzle.png" alt="Loaded puzzle" width="360"/>
    <figcaption>Loading a saved puzzle.</figcaption>
  </figure>
</div> -->


<table>
  <tr>
    <td colspan="2" align="center">
      <figure>
        <img
          src="screenshots/empty-board.png"
          alt="Empty board"
          width="720"
        />
        <figcaption>
          The main editor window with an empty board.
        </figcaption>
      </figure>
    </td>
  </tr>

  <tr>
    <td align="center">
      <img
        src="screenshots/solution-1.png"
        alt="Solving a puzzle"
        width="360"
      />
      <br />
      <sub>Solving a custom puzzle.</sub>
    </td>
    <td align="center">
      <img
        src="screenshots/loaded-puzzle.png"
        alt="Loaded puzzle"
        width="360"
      />
      <br />
      <sub>Loading a saved puzzle.</sub>
    </td>
  </tr>
</table>

---

## 🚀 Installation

### Requirements

- Python 3.10 or newer
- pip

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/AslanGhagigat/lonpos-solver.git
cd lonpos-solver

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run
python ui.py
```

---

## 🎮 Usage

1. Select a piece from the panel on the right (e.g. `A`).
2. Use **Rotate** and **Mirror** to change its shape.
3. Click on empty cells to place the piece.
   - The white dot in the preview marks the piece's anchor cell.
4. Click on any of a piece's cells to remove it.
5. Press **Solve** to generate solutions.
6. Press **Next ▶** to cycle through them.

### Special buttons

| Button | Description |
|---|---|
| **Use cache** | When on, solutions are looked up from the on-disk cache first |
| **Solve** | Incremental solving — 10 solutions immediately, the rest in the background |
| **Solve All** | Exhaustive solving — finds every solution and saves them to the cache |
| **Clear** | Clears the board |
| **Save / Load** | Stores or loads a puzzle to/from `puzzle.json` |

---

## 📂 Project Structure


lonpos-solver/
├── ui.py                     # GUI (CustomTkinter)
├── solver.py                 # Backtracking engine
├── pieces.py                 # 12 piece definitions + rotation + placement generation
├── cache.py                  # Solution cache (read/write)
├── puzzle.json               # Saved puzzle (optional)
├── solutions_cache.jsonl     # Solution cache (auto-generated)
├── requirements.txt
├── README.md
└── .gitignore


---

## 🧠 How It Works

### 1. Piece representation
Each piece is a list of relative cell coordinates. The `rotate` and `mirror`
functions generate every possible orientation, and duplicates are removed
using `frozenset`.

### 2. Placement generation
`generate_placements` enumerates every valid position of every piece on the
board and stores each one as a **55-bit bitmask**. Overlap checks reduce to a
single `&` operation.

### 3. Solver
`solver.solve` is a generator that performs **backtracking** with the **MRV**
heuristic — at each step, it picks the empty cell with the fewest legal
placements. Every found solution is yielded as a list of placement dicts.

### 4. Cache
Each solution is converted to a 55-character string (one character per cell,
representing the piece covering it) and appended to `solutions_cache.jsonl`.
On the next run, the file is loaded and solutions compatible with the user's
locked pieces are filtered out.

### 5. Background execution
The solver runs in a daemon `threading.Thread` and communicates with the GUI
through a `queue.Queue`. The UI never blocks.

---

## 📊 Stats

| Item | Value |
|---|---|
| Board size | 5 × 11 = 55 cells |
| Number of pieces | 12 |
| Unique placements | ~1,600 |
| Empty-board solutions | 371,020 |
| Full cache size | ~26 MB |

---

## 🛠 Dependencies

- [`customtkinter`](https://github.com/TomSchimansky/CustomTkinter) — GUI toolkit
- `tkinter` — Canvas and events (built-in)
- `threading`, `queue`, `json` — built-in

---

## 📝 License

Released under the MIT License. See `LICENSE` for details.

---

## 🤝 Contributing

Pull requests and issues are welcome. For major changes, please open an
issue first to discuss what you'd like to change.

---

## 🙏 Acknowledgements

Inspired by the classic **Lonpos 101** puzzle.