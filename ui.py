# import customtkinter as ctk
# import tkinter as tk
# import json
# import queue
# import threading

# from pieces import PIECES, rotate, mirror, all_possible_pos
# from cache import (load_cache, append_to_cache, is_compatible,
#                    string_to_solution, solution_to_string)

# # ---------- Config ----------
# ROWS = 5
# COLUMNS = 11
# CELL_SIZE = 42
# MARGIN = 10
# PREVIEW_SIZE = 150
# PIECES_PER_ROW = 4

# BATCH_SIZE = 10            # solutions per batch
# PREFETCH_THRESHOLD = 3     # when this few remain, request next batch

# PIECE_COLORS = {
#     'A': '#e74c3c', 'B': '#3498db', 'C': '#2ecc71', 'D': '#f1c40f',
#     'E': '#e67e22', 'F': '#9b59b6', 'G': '#1abc9c', 'H': '#e91e63',
#     'I': '#a1887f', 'J': '#95a5a6', 'K': '#34495e', 'L': '#8bc34a',
# }

# EMPTY_COLOR = '#4a4a4a'
# CELL_OUTLINE = '#2a2a2a'
# SOLVER_DOT_COLOR = '#ffffff'


# class LonposApp(ctk.CTk):
#     def __init__(self):
#         super().__init__()

#         self.title("Lonpos Solver")
#         self.geometry("820x540")
#         self.resizable(False, False)

#         # ----- Board state -----
#         self.board = [[None] * COLUMNS for _ in range(ROWS)]
#         self.placed_pieces = []
#         self.used_pieces = set()
#         self.current_piece = None
#         self.current_shape = []
        
#         # ----- Solver state -----
#         self.solver_thread = None
#         self.solution_queue = None
#         self.request_queue = None
#         self.cancel_event = None
#         self.batch_pending = False

#         self.solutions = []
#         self.current_solution_index = -1
#         self.solver_done = False
#         self.solver_error = None
#         self.solver_overlay = []
        
#         # ----- Cache Loader -----
#         self.cached_solutions = load_cache()       # list of 55-char strings
#         self.cached_set = set(self.cached_solutions)

#         self._build_ui()
#         self._select_piece('A')

#     # ==============================================================
#     #  UI Construction
#     # ==============================================================
#     def _build_ui(self):
#         # ---------- Left: board + buttons ----------
#         left_frame = ctk.CTkFrame(self)
#         left_frame.pack(side="left", padx=(20, 0), pady=20, fill="y")

#         canvas_w = COLUMNS * CELL_SIZE + 2 * MARGIN
#         canvas_h = ROWS * CELL_SIZE + 2 * MARGIN

#         self.canvas = tk.Canvas(
#             left_frame,
#             width=canvas_w,
#             height=canvas_h,
#             bg='#2b2b2b',
#             highlightthickness=0,
#         )
#         self.canvas.pack(pady=(40,10))
#         self.canvas.bind("<Button-1>", self._on_canvas_click)

#         self._draw_board()

#         btn_row = ctk.CTkFrame(left_frame, fg_color="transparent")
#         btn_row.pack(fill="x", pady=(10, 0), padx=MARGIN)

#         ctk.CTkButton(btn_row, text="Clear", width=75,
#                       command=self._clear_board).pack(side="left", padx=3)
#         ctk.CTkButton(btn_row, text="Save", width=75,
#                       command=self._save_puzzle).pack(side="left", padx=3)
#         ctk.CTkButton(btn_row, text="Load", width=75,
#                       command=self._load_puzzle).pack(side="left", padx=3)

#         self.next_button = ctk.CTkButton(
#             btn_row, text="Next ▶", width=80,
#             fg_color="#3b7cbf", hover_color="#2c5e91",
#             state="disabled", command=self._on_next_solution)
#         self.next_button.pack(side="right", padx=3)

#         self.solve_button = ctk.CTkButton(
#             btn_row, text="Solve", width=90,
#             fg_color="#2a8c4a", hover_color="#1e6b38",
#             command=self._on_solve)
#         self.solve_button.pack(side="right", padx=3)

#         # ---------- Right: piece selector + preview ----------
#         right_frame = ctk.CTkFrame(self)
#         right_frame.pack(side="right", padx=(0, 20), pady=20, fill="y")

#         ctk.CTkLabel(right_frame, text="Pieces",
#                      font=("Arial", 15, "bold")).pack(pady=(10, 6))

#         piece_grid = ctk.CTkFrame(right_frame, fg_color="transparent")
#         piece_grid.pack(padx=10, pady=(0, 10))

#         self.piece_buttons = {}
#         for idx, name in enumerate(PIECES.keys()):
#             r, c = divmod(idx, PIECES_PER_ROW)
#             btn = ctk.CTkButton(
#                 piece_grid,
#                 text=name,
#                 width=58, height=40,
#                 fg_color=PIECE_COLORS[name],
#                 hover_color=self._darken(PIECE_COLORS[name]),
#                 text_color="white",
#                 font=("Arial", 14, "bold"),
#                 corner_radius=6,
#                 border_width=0,
#                 command=lambda n=name: self._select_piece(n),
#             )
#             btn.grid(row=r, column=c, padx=4, pady=4)
#             self.piece_buttons[name] = btn

#         ctk.CTkLabel(right_frame, text="Preview",
#                      font=("Arial", 13, "bold")).pack(pady=(6, 2))

#         self.preview_canvas = tk.Canvas(
#             right_frame,
#             width=PREVIEW_SIZE, height=PREVIEW_SIZE,
#             bg='#2b2b2b',
#             highlightthickness=1,
#             highlightbackground='#555555',
#         )
#         self.preview_canvas.pack(pady=2)

#         rot_row = ctk.CTkFrame(right_frame, fg_color="transparent")
#         rot_row.pack(pady=(6, 2))
#         ctk.CTkButton(rot_row, text="⟳  Rotate", width=88, height=30,
#                       command=self._rotate_current).pack(side="left", padx=3)
#         ctk.CTkButton(rot_row, text="⇋  Mirror", width=88, height=30,
#                       command=self._mirror_current).pack(side="left", padx=3)

#         self.status_label = ctk.CTkLabel(
#             right_frame, text="",
#             font=("Arial", 11),
#             text_color="#cccccc",
#             wraplength=240,
#             justify="center",
#         )
#         self.status_label.pack(pady=(8, 10), padx=10)

#     def _darken(self, hex_color):
#         hex_color = hex_color.lstrip('#')
#         r, g, b = int(hex_color[0:2], 16), int(
#             hex_color[2:4], 16), int(hex_color[4:6], 16)
#         r, g, b = max(0, r - 30), max(0, g - 30), max(0, b - 30)
#         return f'#{r:02x}{g:02x}{b:02x}'

#     # ==============================================================
#     #  Board drawing
#     # ==============================================================
#     def _cell_bbox(self, r, c):
#         x1 = MARGIN + c * CELL_SIZE
#         y1 = MARGIN + r * CELL_SIZE
#         return x1, y1, x1 + CELL_SIZE, y1 + CELL_SIZE

#     def _draw_board(self):
#         for r in range(ROWS):
#             for c in range(COLUMNS):
#                 self._draw_cell(r, c)

#     def _draw_cell(self, r, c):
#         x1, y1, x2, y2 = self._cell_bbox(r, c)
#         fill = self._cell_color(r, c)
#         self.canvas.delete(f"cell_{r}_{c}")
#         self.canvas.create_oval(
#             x1 + 2, y1 + 2, x2 - 2, y2 - 2,
#             fill=fill, outline=CELL_OUTLINE, width=1,
#             tags=f"cell_{r}_{c}",
#         )
#         if self._is_solver_cell(r, c):
#             cx = (x1 + x2) / 2
#             cy = (y1 + y2) / 2
#             rad = (x2 - x1) * 0.12
#             self.canvas.create_oval(
#                 cx - rad, cy - rad, cx + rad, cy + rad,
#                 fill=SOLVER_DOT_COLOR, outline='',
#                 tags=f"cell_{r}_{c}",
#             )

#     def _cell_color(self, r, c):
#         piece = self.board[r][c]
#         if piece is None:
#             return EMPTY_COLOR
#         return PIECE_COLORS.get(piece, '#999999')

#     def _is_solver_cell(self, r, c):
#         for p in self.solver_overlay:
#             if (r, c) in p['cells']:
#                 return True
#         return False

#     # ==============================================================
#     #  Piece selection / preview
#     # ==============================================================
#     def _select_piece(self, name):
#         if name in self.used_pieces:
#             self.status_label.configure(
#                 text=f"Piece {name} is already on the board")
#             return
#         self.current_piece = name
#         self.current_shape = list(PIECES[name])
#         self._update_piece_buttons()
#         self._draw_preview()
#         self.status_label.configure(text=f"Selected: {name}")

#     def _update_piece_buttons(self):
#         for n, btn in self.piece_buttons.items():
#             if n in self.used_pieces:
#                 btn.configure(fg_color='#555555', hover_color='#444444',
#                               text_color='#888888', border_width=0)
#             else:
#                 btn.configure(fg_color=PIECE_COLORS[n],
#                               hover_color=self._darken(PIECE_COLORS[n]),
#                               text_color='white', border_width=0)
#             if n == self.current_piece and n not in self.used_pieces:
#                 btn.configure(border_width=3, border_color='white')

#     def _anchor_cell(self):
#         if not self.current_shape:
#             return None
#         return min(self.current_shape)

#     def _draw_preview(self):
#         self.preview_canvas.delete("all")
#         if not self.current_shape or not self.current_piece:
#             return

#         max_r = max(r for r, c in self.current_shape)
#         max_c = max(c for r, c in self.current_shape)
#         n_rows, n_cols = max_r + 1, max_c + 1

#         pad = 15
#         available = PREVIEW_SIZE - 2 * pad
#         cell = min(available // max(n_rows, 1),
#                    available // max(n_cols, 1), 35)
#         w, h = n_cols * cell, n_rows * cell
#         pad_x = (PREVIEW_SIZE - w) // 2
#         pad_y = (PREVIEW_SIZE - h) // 2

#         color = PIECE_COLORS.get(self.current_piece, '#888888')
#         for (r, c) in self.current_shape:
#             x1 = pad_x + c * cell
#             y1 = pad_y + r * cell
#             x2 = x1 + cell
#             y2 = y1 + cell
#             self.preview_canvas.create_oval(
#                 x1 + 2, y1 + 2, x2 - 2, y2 - 2,
#                 fill=color, outline='#222222', width=1,
#             )

#         anchor = self._anchor_cell()
#         if anchor:
#             ar, ac = anchor
#             ax1 = pad_x + ac * cell
#             ay1 = pad_y + ar * cell
#             ax2 = ax1 + cell
#             ay2 = ay1 + cell
#             self.preview_canvas.create_oval(
#                 ax1 + 2, ay1 + 2, ax2 - 2, ay2 - 2,
#                 fill='', outline='#ffffff', width=3,
#             )
#             cx = (ax1 + ax2) / 2
#             cy = (ay1 + ay2) / 2
#             rad = cell * 0.14
#             self.preview_canvas.create_oval(
#                 cx - rad, cy - rad, cx + rad, cy + rad,
#                 fill='#ffffff', outline='',
#             )

#     def _rotate_current(self):
#         if not self.current_shape:
#             return
#         self.current_shape = rotate(self.current_shape)
#         self._draw_preview()

#     def _mirror_current(self):
#         if not self.current_shape:
#             return
#         self.current_shape = mirror(self.current_shape)
#         self._draw_preview()

#     # ==============================================================
#     #  Board interaction
#     # ==============================================================
#     def _on_canvas_click(self, event):
#         c = (event.x - MARGIN) // CELL_SIZE
#         r = (event.y - MARGIN) // CELL_SIZE
#         if not (0 <= r < ROWS and 0 <= c < COLUMNS):
#             return

#         # --- Click on a solver-overlay cell → clear only the overlay ---
#         if self.solver_overlay and self._is_solver_cell(r, c):
#             self._clear_solution_overlay()
#             self.status_label.configure(text="Solution cleared")
#             return

#         # --- Click on an occupied (user) cell → remove only that piece ---
#         if self.board[r][c] is not None:
#             self._remove_piece_at(r, c)
#             return

#         # --- Click on empty cell → try to place current piece ---
#         if not self.current_piece:
#             self.status_label.configure(text="Select a piece first")
#             return
#         if self.current_piece in self.used_pieces:
#             self.status_label.configure(
#                 text=f"Piece {self.current_piece} already placed")
#             return
#         self._try_place_piece(r, c)

#     def _try_place_piece(self, click_r, click_c):
#         anchor = self._anchor_cell()
#         if anchor is None:
#             return False
#         ar, ac = anchor
#         offset_r = click_r - ar
#         offset_c = click_c - ac

#         cells = []
#         for (dr, dc) in self.current_shape:
#             rr = offset_r + dr
#             cc = offset_c + dc
#             if not (0 <= rr < ROWS and 0 <= cc < COLUMNS):
#                 self.status_label.configure(text="Piece doesn't fit here")
#                 return False
#             if self.board[rr][cc] is not None:
#                 self.status_label.configure(text="Cell already occupied")
#                 return False
#             cells.append((rr, cc))

#         for (rr, cc) in cells:
#             self.board[rr][cc] = self.current_piece
#         self.placed_pieces.append({
#             'piece': self.current_piece,
#             'cells': cells,
#         })
#         for (rr, cc) in cells:
#             self._draw_cell(rr, cc)

#         placed_name = self.current_piece
#         self.used_pieces.add(placed_name)
#         self._update_piece_buttons()

#         unused = [n for n in PIECES.keys() if n not in self.used_pieces]
#         if unused:
#             self._select_piece(unused[0])
#             self.status_label.configure(
#                 text=f"Placed {placed_name}. Next: {unused[0]}")
#         else:
#             self.current_piece = None
#             self.current_shape = []
#             self._draw_preview()
#             self.status_label.configure(
#                 text=f"Placed {placed_name}. All pieces placed!")
#         return True

#     def _remove_piece_at(self, r, c):
#         for i, pp in enumerate(self.placed_pieces):
#             if (r, c) in pp['cells']:
#                 for rr, cc in pp['cells']:
#                     self.board[rr][cc] = None
#                     self._draw_cell(rr, cc)
#                 removed = pp['piece']
#                 self.used_pieces.discard(removed)
#                 del self.placed_pieces[i]
#                 self._update_piece_buttons()
#                 self._select_piece(removed)
#                 self.status_label.configure(text=f"Removed {removed}")
#                 return

#     # ==============================================================
#     #  Actions
#     # ==============================================================
#     def _clear_board(self):
#         self._cancel_solver()
#         self._clear_solution_overlay()

#         self.solutions = []
#         self.current_solution_index = -1
#         self.solver_done = False
#         self.solver_error = None
#         self.batch_pending = False

#         self.board = [[None] * COLUMNS for _ in range(ROWS)]
#         self.placed_pieces = []
#         self.used_pieces.clear()
#         self._draw_board()
#         self._update_piece_buttons()
#         self.current_piece = None
#         self.current_shape = []
#         self._draw_preview()
#         self._select_piece('A')
#         self.solve_button.configure(state='normal', text='Solve')
#         self.next_button.configure(state='disabled', text='Next ▶')
#         self.status_label.configure(text="Board cleared")

#     def _save_puzzle(self):
#         data = {
#             'placed_pieces': [
#                 {'piece': pp['piece'], 'cells': [list(c) for c in pp['cells']]}
#                 for pp in self.placed_pieces
#             ]
#         }
#         try:
#             with open('puzzle.json', 'w') as f:
#                 json.dump(data, f, indent=2)
#             self.status_label.configure(text="Saved to puzzle.json")
#         except Exception as e:
#             self.status_label.configure(text=f"Save error: {e}")

#     def _load_puzzle(self):
#         try:
#             with open('puzzle.json', 'r') as f:
#                 data = json.load(f)
#         except FileNotFoundError:
#             self.status_label.configure(text="No saved puzzle found")
#             return
#         except Exception as e:
#             self.status_label.configure(text=f"Load error: {e}")
#             return

#         self._cancel_solver()
#         self._clear_solution_overlay()
#         self.solutions = []
#         self.current_solution_index = -1
#         self.solver_done = False
#         self.batch_pending = False

#         self.board = [[None] * COLUMNS for _ in range(ROWS)]
#         self.placed_pieces = []
#         self.used_pieces.clear()

#         for pp in data.get('placed_pieces', []):
#             cells = [tuple(c) for c in pp['cells']]
#             piece = pp['piece']
#             for r, c in cells:
#                 self.board[r][c] = piece
#             self.placed_pieces.append({'piece': piece, 'cells': cells})
#             self.used_pieces.add(piece)

#         self._draw_board()
#         self._update_piece_buttons()

#         unused = [n for n in PIECES.keys() if n not in self.used_pieces]
#         if unused:
#             self._select_piece(unused[0])
#         else:
#             self.current_piece = None
#             self.current_shape = []
#             self._draw_preview()

#         self.solve_button.configure(state='normal', text='Solve')
#         self.next_button.configure(state='disabled', text='Next ▶')
#         self.status_label.configure(text="Loaded puzzle")

#     # ==============================================================
#     #  Solver integration
#     # ==============================================================
#     # def _on_solve(self):
#     #     # Stop any previous worker
#     #     self._cancel_solver()
#     #     self._clear_solution_overlay()

#     #     self.solutions = []
#     #     self.current_solution_index = -1
#     #     self.solver_done = False
#     #     self.solver_error = None
#     #     self.batch_pending = False

#     #     placed_snapshot = [
#     #         {'piece': pp['piece'], 'cells': list(pp['cells'])}
#     #         for pp in self.placed_pieces
#     #     ]

#     #     self.solution_queue = queue.Queue()
#     #     self.request_queue = queue.Queue()
#     #     self.cancel_event = threading.Event()

#     #     self.solve_button.configure(state='disabled', text='Solving...')
#     #     self.next_button.configure(state='disabled', text='Next ▶')
#     #     self.status_label.configure(text="Solving...")

#     #     self.solver_thread = threading.Thread(
#     #         target=self._solver_worker,
#     #         args=(placed_snapshot,
#     #               self.cancel_event,
#     #               self.request_queue,
#     #               self.solution_queue),
#     #         daemon=True,
#     #     )
#     #     self.solver_thread.start()

#     #     # Ask for the first batch
#     #     self.request_queue.put(1)
#     #     self.batch_pending = True

#     #     self.after(80, self._poll_solver)

#     def _on_solve(self):
#         self._cancel_solver()
#         self._clear_solution_overlay()

#         self.solutions = []
#         self.current_solution_index = -1
#         self.solver_done = False
#         self.solver_error = None
#         self.batch_pending = False

#         # --- NEW: try cache first ---
#         locked = self.placed_pieces
#         cached_matches = [string_to_solution(s)
#                         for s in self.cached_solutions
#                         if is_compatible(s, locked)]

#         if len(cached_matches) >= BATCH_SIZE:
#             # Enough in cache. Skip solver for now.
#             self.solutions = cached_matches
#             self.current_solution_index = 0
#             self._display_solution(self.solutions[0])
#             self.status_label.configure(
#                 text=f"{len(cached_matches)} solutions from cache"
#             )
#             self.solve_button.configure(state='normal', text='Solve')
#             self.next_button.configure(state='normal', text='Next ▶')
#             return

#         # --- Otherwise run solver normally ---
#         placed_snapshot = [
#             {'piece': pp['piece'], 'cells': list(pp['cells'])}
#             for pp in self.placed_pieces
#         ]

#         self.solution_queue = queue.Queue()
#         self.request_queue = queue.Queue()
#         self.cancel_event = threading.Event()

#         self.solve_button.configure(state='disabled', text='Solving...')
#         self.next_button.configure(state='disabled', text='Next ▶')
#         self.status_label.configure(
#             text=f"Solving... ({len(cached_matches)} cached matches)"
#         )

#         self.solver_thread = threading.Thread(
#             target=self._solver_worker,
#             args=(placed_snapshot, self.cancel_event,
#                 self.request_queue, self.solution_queue),
#             daemon=True,
#         )
#         self.solver_thread.start()
#         self.request_queue.put(1)
#         self.batch_pending = True
#         self.after(80, self._poll_solver)

#     def _cancel_solver(self):
#         if self.cancel_event is not None:
#             self.cancel_event.set()
#         if self.request_queue is not None:
#             try:
#                 self.request_queue.put_nowait(None)  # unblock worker
#             except Exception:
#                 pass
#         self.cancel_event = None
#         self.request_queue = None
#         self.solution_queue = None
#         self.batch_pending = False
    
#     # def _solver_worker(self, placed, cancel_event, request_q, output_q):
#     #     """Worker thread. Only uses local references — never touches self.*"""
#     #     try:
#     #         from solver import solve
#     #         gen = solve(placed)
#     #         while not cancel_event.is_set():
#     #             msg = request_q.get()
#     #             if msg is None or cancel_event.is_set():
#     #                 return
#     #             for _ in range(BATCH_SIZE):
#     #                 if cancel_event.is_set():
#     #                     return
#     #                 try:
#     #                     sol = next(gen)
#     #                 except StopIteration:
#     #                     output_q.put(('done', None))
#     #                     return
#     #                 if cancel_event.is_set():
#     #                     return
#     #                 output_q.put(sol)
#     #             if cancel_event.is_set():
#     #                 return
#     #             output_q.put(('batch_done', None))
#     #     except Exception as e:
#     #         try:
#     #             output_q.put(('error', str(e)))
#     #             output_q.put(('done', None))
#     #         except Exception:
#     #             pass
#     def _solver_worker(self, placed, cancel_event, request_q, output_q):
#         try:
#             from solver import solve
#             gen = solve(placed)
#             while not cancel_event.is_set():
#                 msg = request_q.get()
#                 if msg is None or cancel_event.is_set():
#                     return
#                 for _ in range(BATCH_SIZE):
#                     if cancel_event.is_set():
#                         return
#                     try:
#                         sol = next(gen)
#                     except StopIteration:
#                         output_q.put(('done', None))
#                         return

#                     # --- NEW: persist every new solution to cache ---
#                     s = solution_to_string(sol)
#                     if s not in self.cached_set:
#                         self.cached_set.add(s)
#                         self.cached_solutions.append(s)
#                         append_to_cache(s)

#                     output_q.put(sol)
#                 output_q.put(('batch_done', None))
#         except Exception as e:
#             try:
#                 output_q.put(('error', str(e)))
#                 output_q.put(('done', None))
#             except Exception:
#                 pass

#     def _poll_solver(self):
#         q = self.solution_queue
#         if q is None:
#             return

#         try:
#             while True:
#                 item = q.get_nowait()
#                 if isinstance(item, tuple):
#                     kind, payload = item
#                     if kind == 'done':
#                         self.solver_done = True
#                         self.batch_pending = False
#                     elif kind == 'batch_done':
#                         self.batch_pending = False
#                     elif kind == 'error':
#                         self.solver_error = payload
#                         self.solver_done = True
#                         self.batch_pending = False
#                 else:
#                     self.solutions.append(item)
#         except queue.Empty:
#             pass

#         # Display first solution as soon as it arrives
#         if self.current_solution_index == -1 and self.solutions:
#             self.current_solution_index = 0
#             self._display_solution(self.solutions[0])

#         self._maybe_request_more()
#         self._update_solver_ui()

#         if not self.solver_done:
#             self.after(120, self._poll_solver)

#     def _maybe_request_more(self):
#         if self.solver_done or self.batch_pending:
#             return
#         if self.request_queue is None or not self.solutions:
#             return
#         remaining = len(self.solutions) - 1 - self.current_solution_index
#         if remaining < PREFETCH_THRESHOLD:
#             self.request_queue.put(1)
#             self.batch_pending = True

#     def _update_solver_ui(self):
#         if self.solver_error:
#             self.status_label.configure(
#                 text=f"Solver error: {self.solver_error}")
#             self.solve_button.configure(state='normal', text='Solve')
#             self.next_button.configure(state='disabled', text='Next ▶')
#             return

#         if self.current_solution_index == -1:
#             if self.solver_done:
#                 self.status_label.configure(text="No solution found")
#                 self.solve_button.configure(state='normal', text='Solve')
#                 self.next_button.configure(state='disabled', text='Next ▶')
#             else:
#                 self.status_label.configure(text="Solving...")
#                 self.solve_button.configure(
#                     state='disabled', text='Solving...')
#                 self.next_button.configure(state='disabled', text='Next ▶')
#             return

#         idx = self.current_solution_index
#         total = len(self.solutions)

#         if self.solver_done:
#             status = f"Solution {idx + 1} of {total} (all found)"
#         else:
#             status = f"Solution {idx + 1}  •  {total} found so far"

#         self.status_label.configure(text=status)
#         self.solve_button.configure(state='normal', text='Solve')

#         has_more = (idx + 1 < total) or (not self.solver_done)
#         self.next_button.configure(
#             state='normal' if has_more else 'disabled',
#             text='Next ▶',
#         )

#     def _on_next_solution(self):
#         if self.current_solution_index + 1 < len(self.solutions):
#             self.current_solution_index += 1
#             self._display_solution(self.solutions[self.current_solution_index])
#             self._update_solver_ui()
#         elif not self.solver_done:
#             self.status_label.configure(text="Computing more solutions...")
#             self._maybe_request_more()
#         else:
#             self.status_label.configure(text="No more solutions")

#     # ----- Solution overlay helpers -----
#     def _display_solution(self, solution):
#         self._clear_solution_overlay()
#         self.solver_overlay = list(solution)
#         for p in solution:
#             for (r, c) in p['cells']:
#                 self.board[r][c] = p['piece']
#                 self._draw_cell(r, c)

#     def _clear_solution_overlay(self):
#         if not self.solver_overlay:
#             return
#         overlay = self.solver_overlay
#         self.solver_overlay = []
#         for p in overlay:
#             for (r, c) in p['cells']:
#                 self.board[r][c] = None
#                 self._draw_cell(r, c)


# if __name__ == '__main__':
#     app = LonposApp()
#     app.mainloop()
import customtkinter as ctk
import tkinter as tk
import json
import queue
import threading

from pieces import PIECES, rotate, mirror, all_possible_pos
from cache import (load_cache, append_to_cache, is_compatible,
                   string_to_solution, solution_to_string, CACHE_PATH)


# ---------- Config ----------
ROWS = 5
COLUMNS = 11
CELL_SIZE = 42
MARGIN = 10
PREVIEW_SIZE = 150
PIECES_PER_ROW = 4

BATCH_SIZE = 10            # solutions per batch (interactive Solve)
PREFETCH_THRESHOLD = 3     # when this few remain, request next batch

PIECE_COLORS = {
    'A': '#e74c3c', 'B': '#3498db', 'C': '#2ecc71', 'D': '#f1c40f',
    'E': '#e67e22', 'F': '#9b59b6', 'G': '#1abc9c', 'H': '#e91e63',
    'I': '#a1887f', 'J': '#95a5a6', 'K': '#34495e', 'L': '#8bc34a',
}

EMPTY_COLOR = '#4a4a4a'
CELL_OUTLINE = '#2a2a2a'
SOLVER_DOT_COLOR = '#ffffff'


class LonposApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Lonpos Solver")
        self.geometry("840x580")
        self.resizable(False, False)

        # ----- Board state -----
        self.board = [[None] * COLUMNS for _ in range(ROWS)]
        self.placed_pieces = []
        self.used_pieces = set()
        self.current_piece = None
        self.current_shape = []

        # ----- Batch solver state -----
        self.solver_thread = None
        self.solution_queue = None
        self.request_queue = None
        self.cancel_event = None
        self.batch_pending = False

        self.solutions = []
        self.current_solution_index = -1
        self.solver_done = False
        self.solver_error = None
        self.solver_overlay = []

        # ----- Solve-All state -----
        self.solve_all_thread = None
        self.solve_all_cancel = None
        self._solve_all_found = 0
        self._solve_all_new = 0
        self._solve_all_done = False
        self._solve_all_aborted = False

        # ----- Cache -----
        self.cached_solutions = load_cache()
        self.cached_set = set(self.cached_solutions)

        # ----- UI toggle -----
        self.use_cache = ctk.BooleanVar(value=True)

        self._build_ui()
        self._select_piece('A')
        self._update_cache_label()

    # ==============================================================
    #  UI Construction
    # ==============================================================
    def _build_ui(self):
        # ---------- Left: board + buttons ----------
        left_frame = ctk.CTkFrame(self)
        left_frame.pack(side="left", padx=(20, 0), pady=20, fill="y")

        canvas_w = COLUMNS * CELL_SIZE + 2 * MARGIN
        canvas_h = ROWS * CELL_SIZE + 2 * MARGIN

        self.canvas = tk.Canvas(
            left_frame,
            width=canvas_w,
            height=canvas_h,
            bg='#2b2b2b',
            highlightthickness=0,
        )
        self.canvas.pack(pady=(40, 10))
        self.canvas.bind("<Button-1>", self._on_canvas_click)

        self._draw_board()

        # --- Row 1: Clear / Save / Load | Solve / Next ---
        btn_row = ctk.CTkFrame(left_frame, fg_color="transparent")
        btn_row.pack(fill="x", pady=(10, 0), padx=MARGIN)

        ctk.CTkButton(btn_row, text="Clear", width=68,
                      command=self._clear_board).pack(side="left", padx=2)
        ctk.CTkButton(btn_row, text="Save", width=68,
                      command=self._save_puzzle).pack(side="left", padx=2)
        ctk.CTkButton(btn_row, text="Load", width=68,
                      command=self._load_puzzle).pack(side="left", padx=2)

        self.next_button = ctk.CTkButton(
            btn_row, text="Next ▶", width=75,
            fg_color="#3b7cbf", hover_color="#2c5e91",
            state="disabled", command=self._on_next_solution)
        self.next_button.pack(side="right", padx=2)

        self.solve_button = ctk.CTkButton(
            btn_row, text="Solve", width=80,
            fg_color="#2a8c4a", hover_color="#1e6b38",
            command=self._on_solve)
        self.solve_button.pack(side="right", padx=2)

        # --- Row 2: Use cache switch | Solve All ---
        btn_row2 = ctk.CTkFrame(left_frame, fg_color="transparent")
        btn_row2.pack(fill="x", pady=(6, 0), padx=MARGIN)

        self.cache_switch = ctk.CTkSwitch(
            btn_row2, text="Use cache",
            variable=self.use_cache,
            onvalue=True, offvalue=False,
            font=("Arial", 12),
        )
        self.cache_switch.pack(side="left", padx=2)

        self.solve_all_button = ctk.CTkButton(
            btn_row2, text="Solve All", width=90,
            fg_color="#8e44ad", hover_color="#6c3483",
            command=self._on_solve_all)
        self.solve_all_button.pack(side="right", padx=2)

        # ---------- Right: piece selector + preview ----------
        right_frame = ctk.CTkFrame(self)
        right_frame.pack(side="right", padx=(0, 20), pady=20, fill="y")

        ctk.CTkLabel(right_frame, text="Pieces",
                     font=("Arial", 15, "bold")).pack(pady=(10, 6))

        piece_grid = ctk.CTkFrame(right_frame, fg_color="transparent")
        piece_grid.pack(padx=10, pady=(0, 10))

        self.piece_buttons = {}
        for idx, name in enumerate(PIECES.keys()):
            r, c = divmod(idx, PIECES_PER_ROW)
            btn = ctk.CTkButton(
                piece_grid,
                text=name,
                width=58, height=40,
                fg_color=PIECE_COLORS[name],
                hover_color=self._darken(PIECE_COLORS[name]),
                text_color="white",
                font=("Arial", 14, "bold"),
                corner_radius=6,
                border_width=0,
                command=lambda n=name: self._select_piece(n),
            )
            btn.grid(row=r, column=c, padx=4, pady=4)
            self.piece_buttons[name] = btn

        ctk.CTkLabel(right_frame, text="Preview",
                     font=("Arial", 13, "bold")).pack(pady=(6, 2))

        self.preview_canvas = tk.Canvas(
            right_frame,
            width=PREVIEW_SIZE, height=PREVIEW_SIZE,
            bg='#2b2b2b',
            highlightthickness=1,
            highlightbackground='#555555',
        )
        self.preview_canvas.pack(pady=2)

        rot_row = ctk.CTkFrame(right_frame, fg_color="transparent")
        rot_row.pack(pady=(6, 2))
        ctk.CTkButton(rot_row, text="⟳  Rotate", width=88, height=30,
                      command=self._rotate_current).pack(side="left", padx=3)
        ctk.CTkButton(rot_row, text="⇋  Mirror", width=88, height=30,
                      command=self._mirror_current).pack(side="left", padx=3)

        self.status_label = ctk.CTkLabel(
            right_frame, text="",
            font=("Arial", 11),
            text_color="#cccccc",
            wraplength=240,
            justify="center",
        )
        self.status_label.pack(pady=(8, 4), padx=10)

        self.cache_info_label = ctk.CTkLabel(
            right_frame, text="",
            font=("Arial", 10),
            text_color="#888888",
        )
        self.cache_info_label.pack(pady=(0, 10))

    def _darken(self, hex_color):
        hex_color = hex_color.lstrip('#')
        r, g, b = int(hex_color[0:2], 16), int(
            hex_color[2:4], 16), int(hex_color[4:6], 16)
        r, g, b = max(0, r - 30), max(0, g - 30), max(0, b - 30)
        return f'#{r:02x}{g:02x}{b:02x}'

    def _update_cache_label(self):
        self.cache_info_label.configure(
            text=f"Cache: {len(self.cached_solutions)} solutions"
        )

    # ==============================================================
    #  Board drawing
    # ==============================================================
    def _cell_bbox(self, r, c):
        x1 = MARGIN + c * CELL_SIZE
        y1 = MARGIN + r * CELL_SIZE
        return x1, y1, x1 + CELL_SIZE, y1 + CELL_SIZE

    def _draw_board(self):
        for r in range(ROWS):
            for c in range(COLUMNS):
                self._draw_cell(r, c)

    def _draw_cell(self, r, c):
        x1, y1, x2, y2 = self._cell_bbox(r, c)
        fill = self._cell_color(r, c)
        self.canvas.delete(f"cell_{r}_{c}")
        self.canvas.create_oval(
            x1 + 2, y1 + 2, x2 - 2, y2 - 2,
            fill=fill, outline=CELL_OUTLINE, width=1,
            tags=f"cell_{r}_{c}",
        )
        if self._is_solver_cell(r, c):
            cx = (x1 + x2) / 2
            cy = (y1 + y2) / 2
            rad = (x2 - x1) * 0.12
            self.canvas.create_oval(
                cx - rad, cy - rad, cx + rad, cy + rad,
                fill=SOLVER_DOT_COLOR, outline='',
                tags=f"cell_{r}_{c}",
            )

    def _cell_color(self, r, c):
        piece = self.board[r][c]
        if piece is None:
            return EMPTY_COLOR
        return PIECE_COLORS.get(piece, '#999999')

    def _is_solver_cell(self, r, c):
        for p in self.solver_overlay:
            if (r, c) in p['cells']:
                return True
        return False

    # ==============================================================
    #  Piece selection / preview
    # ==============================================================
    def _select_piece(self, name):
        if name in self.used_pieces:
            self.status_label.configure(
                text=f"Piece {name} is already on the board")
            return
        self.current_piece = name
        self.current_shape = list(PIECES[name])
        self._update_piece_buttons()
        self._draw_preview()
        self.status_label.configure(text=f"Selected: {name}")

    def _update_piece_buttons(self):
        for n, btn in self.piece_buttons.items():
            if n in self.used_pieces:
                btn.configure(fg_color='#555555', hover_color='#444444',
                              text_color='#888888', border_width=0)
            else:
                btn.configure(fg_color=PIECE_COLORS[n],
                              hover_color=self._darken(PIECE_COLORS[n]),
                              text_color='white', border_width=0)
            if n == self.current_piece and n not in self.used_pieces:
                btn.configure(border_width=3, border_color='white')

    def _anchor_cell(self):
        if not self.current_shape:
            return None
        return min(self.current_shape)

    def _draw_preview(self):
        self.preview_canvas.delete("all")
        if not self.current_shape or not self.current_piece:
            return

        max_r = max(r for r, c in self.current_shape)
        max_c = max(c for r, c in self.current_shape)
        n_rows, n_cols = max_r + 1, max_c + 1

        pad = 15
        available = PREVIEW_SIZE - 2 * pad
        cell = min(available // max(n_rows, 1),
                   available // max(n_cols, 1), 35)
        w, h = n_cols * cell, n_rows * cell
        pad_x = (PREVIEW_SIZE - w) // 2
        pad_y = (PREVIEW_SIZE - h) // 2

        color = PIECE_COLORS.get(self.current_piece, '#888888')
        for (r, c) in self.current_shape:
            x1 = pad_x + c * cell
            y1 = pad_y + r * cell
            x2 = x1 + cell
            y2 = y1 + cell
            self.preview_canvas.create_oval(
                x1 + 2, y1 + 2, x2 - 2, y2 - 2,
                fill=color, outline='#222222', width=1,
            )

        anchor = self._anchor_cell()
        if anchor:
            ar, ac = anchor
            ax1 = pad_x + ac * cell
            ay1 = pad_y + ar * cell
            ax2 = ax1 + cell
            ay2 = ay1 + cell
            self.preview_canvas.create_oval(
                ax1 + 2, ay1 + 2, ax2 - 2, ay2 - 2,
                fill='', outline='#ffffff', width=3,
            )
            cx = (ax1 + ax2) / 2
            cy = (ay1 + ay2) / 2
            rad = cell * 0.14
            self.preview_canvas.create_oval(
                cx - rad, cy - rad, cx + rad, cy + rad,
                fill='#ffffff', outline='',
            )

    def _rotate_current(self):
        if not self.current_shape:
            return
        self.current_shape = rotate(self.current_shape)
        self._draw_preview()

    def _mirror_current(self):
        if not self.current_shape:
            return
        self.current_shape = mirror(self.current_shape)
        self._draw_preview()

    # ==============================================================
    #  Board interaction
    # ==============================================================
    def _on_canvas_click(self, event):
        c = (event.x - MARGIN) // CELL_SIZE
        r = (event.y - MARGIN) // CELL_SIZE
        if not (0 <= r < ROWS and 0 <= c < COLUMNS):
            return

        if self.solver_overlay and self._is_solver_cell(r, c):
            self._clear_solution_overlay()
            self.status_label.configure(text="Solution cleared")
            return

        if self.board[r][c] is not None:
            self._remove_piece_at(r, c)
            return

        if not self.current_piece:
            self.status_label.configure(text="Select a piece first")
            return
        if self.current_piece in self.used_pieces:
            self.status_label.configure(
                text=f"Piece {self.current_piece} already placed")
            return
        self._try_place_piece(r, c)

    def _try_place_piece(self, click_r, click_c):
        anchor = self._anchor_cell()
        if anchor is None:
            return False
        ar, ac = anchor
        offset_r = click_r - ar
        offset_c = click_c - ac

        cells = []
        for (dr, dc) in self.current_shape:
            rr = offset_r + dr
            cc = offset_c + dc
            if not (0 <= rr < ROWS and 0 <= cc < COLUMNS):
                self.status_label.configure(text="Piece doesn't fit here")
                return False
            if self.board[rr][cc] is not None:
                self.status_label.configure(text="Cell already occupied")
                return False
            cells.append((rr, cc))

        for (rr, cc) in cells:
            self.board[rr][cc] = self.current_piece
        self.placed_pieces.append({
            'piece': self.current_piece,
            'cells': cells,
        })
        for (rr, cc) in cells:
            self._draw_cell(rr, cc)

        placed_name = self.current_piece
        self.used_pieces.add(placed_name)
        self._update_piece_buttons()

        unused = [n for n in PIECES.keys() if n not in self.used_pieces]
        if unused:
            self._select_piece(unused[0])
            self.status_label.configure(
                text=f"Placed {placed_name}. Next: {unused[0]}")
        else:
            self.current_piece = None
            self.current_shape = []
            self._draw_preview()
            self.status_label.configure(
                text=f"Placed {placed_name}. All pieces placed!")
        return True

    def _remove_piece_at(self, r, c):
        for i, pp in enumerate(self.placed_pieces):
            if (r, c) in pp['cells']:
                for rr, cc in pp['cells']:
                    self.board[rr][cc] = None
                    self._draw_cell(rr, cc)
                removed = pp['piece']
                self.used_pieces.discard(removed)
                del self.placed_pieces[i]
                self._update_piece_buttons()
                self._select_piece(removed)
                self.status_label.configure(text=f"Removed {removed}")
                return

    # ==============================================================
    #  Actions
    # ==============================================================
    def _clear_board(self):
        self._cancel_solver()
        self._cancel_solve_all()
        self._clear_solution_overlay()

        self.solutions = []
        self.current_solution_index = -1
        self.solver_done = False
        self.solver_error = None
        self.batch_pending = False

        self.board = [[None] * COLUMNS for _ in range(ROWS)]
        self.placed_pieces = []
        self.used_pieces.clear()
        self._draw_board()
        self._update_piece_buttons()
        self.current_piece = None
        self.current_shape = []
        self._draw_preview()
        self._select_piece('A')
        self.solve_button.configure(state='normal', text='Solve')
        self.next_button.configure(state='disabled', text='Next ▶')
        self.status_label.configure(text="Board cleared")

    def _save_puzzle(self):
        data = {
            'placed_pieces': [
                {'piece': pp['piece'], 'cells': [list(c) for c in pp['cells']]}
                for pp in self.placed_pieces
            ]
        }
        try:
            with open('puzzle.json', 'w') as f:
                json.dump(data, f, indent=2)
            self.status_label.configure(text="Saved to puzzle.json")
        except Exception as e:
            self.status_label.configure(text=f"Save error: {e}")

    def _load_puzzle(self):
        try:
            with open('puzzle.json', 'r') as f:
                data = json.load(f)
        except FileNotFoundError:
            self.status_label.configure(text="No saved puzzle found")
            return
        except Exception as e:
            self.status_label.configure(text=f"Load error: {e}")
            return

        self._cancel_solver()
        self._cancel_solve_all()
        self._clear_solution_overlay()
        self.solutions = []
        self.current_solution_index = -1
        self.solver_done = False
        self.batch_pending = False

        self.board = [[None] * COLUMNS for _ in range(ROWS)]
        self.placed_pieces = []
        self.used_pieces.clear()

        for pp in data.get('placed_pieces', []):
            cells = [tuple(c) for c in pp['cells']]
            piece = pp['piece']
            for r, c in cells:
                self.board[r][c] = piece
            self.placed_pieces.append({'piece': piece, 'cells': cells})
            self.used_pieces.add(piece)

        self._draw_board()
        self._update_piece_buttons()

        unused = [n for n in PIECES.keys() if n not in self.used_pieces]
        if unused:
            self._select_piece(unused[0])
        else:
            self.current_piece = None
            self.current_shape = []
            self._draw_preview()

        self.solve_button.configure(state='normal', text='Solve')
        self.next_button.configure(state='disabled', text='Next ▶')
        self.status_label.configure(text="Loaded puzzle")

    # ==============================================================
    #  Batch solver (interactive Solve)
    # ==============================================================
    def _on_solve(self):
        self._cancel_solver()
        self._cancel_solve_all()
        self._clear_solution_overlay()

        self.solutions = []
        self.current_solution_index = -1
        self.solver_done = False
        self.solver_error = None
        self.batch_pending = False

        use_cache = self.use_cache.get()

        if use_cache:
            locked = self.placed_pieces
            cached_matches = [string_to_solution(s)
                              for s in self.cached_solutions
                              if is_compatible(s, locked)]

            if len(cached_matches) >= BATCH_SIZE:
                self.solutions = cached_matches
                self.current_solution_index = 0
                self._display_solution(self.solutions[0])
                self.status_label.configure(
                    text=f"{len(cached_matches)} solutions from cache"
                )
                self.solve_button.configure(state='normal', text='Solve')
                self.next_button.configure(state='normal', text='Next ▶')
                return
        else:
            cached_matches = []

        # Run solver normally
        placed_snapshot = [
            {'piece': pp['piece'], 'cells': list(pp['cells'])}
            for pp in self.placed_pieces
        ]

        self.solution_queue = queue.Queue()
        self.request_queue = queue.Queue()
        self.cancel_event = threading.Event()

        self.solve_button.configure(state='disabled', text='Solving...')
        self.next_button.configure(state='disabled', text='Next ▶')
        if use_cache:
            self.status_label.configure(
                text=f"Solving... ({len(cached_matches)} cached matches)"
            )
        else:
            self.status_label.configure(text="Solving (cache bypassed)...")

        self.solver_thread = threading.Thread(
            target=self._solver_worker,
            args=(placed_snapshot, self.cancel_event,
                  self.request_queue, self.solution_queue),
            daemon=True,
        )
        self.solver_thread.start()
        self.request_queue.put(1)
        self.batch_pending = True
        self.after(80, self._poll_solver)

    def _cancel_solver(self):
        if self.cancel_event is not None:
            self.cancel_event.set()
        if self.request_queue is not None:
            try:
                self.request_queue.put_nowait(None)
            except Exception:
                pass
        self.cancel_event = None
        self.request_queue = None
        self.solution_queue = None
        self.batch_pending = False

    def _solver_worker(self, placed, cancel_event, request_q, output_q):
        try:
            from solver import solve
            gen = solve(placed)
            while not cancel_event.is_set():
                msg = request_q.get()
                if msg is None or cancel_event.is_set():
                    return
                for _ in range(BATCH_SIZE):
                    if cancel_event.is_set():
                        return
                    try:
                        sol = next(gen)
                    except StopIteration:
                        output_q.put(('done', None))
                        return

                    # Persist new solution to cache
                    s = solution_to_string(sol)
                    if s not in self.cached_set:
                        self.cached_set.add(s)
                        self.cached_solutions.append(s)
                        append_to_cache(s)

                    output_q.put(sol)
                output_q.put(('batch_done', None))
        except Exception as e:
            try:
                output_q.put(('error', str(e)))
                output_q.put(('done', None))
            except Exception:
                pass

    def _poll_solver(self):
        q = self.solution_queue
        if q is None:
            return

        try:
            while True:
                item = q.get_nowait()
                if isinstance(item, tuple):
                    kind, payload = item
                    if kind == 'done':
                        self.solver_done = True
                        self.batch_pending = False
                    elif kind == 'batch_done':
                        self.batch_pending = False
                    elif kind == 'error':
                        self.solver_error = payload
                        self.solver_done = True
                        self.batch_pending = False
                else:
                    self.solutions.append(item)
        except queue.Empty:
            pass

        if self.current_solution_index == -1 and self.solutions:
            self.current_solution_index = 0
            self._display_solution(self.solutions[0])
            self._update_cache_label()

        self._maybe_request_more()
        self._update_solver_ui()

        if not self.solver_done:
            self.after(120, self._poll_solver)
        else:
            self._update_cache_label()

    def _maybe_request_more(self):
        if self.solver_done or self.batch_pending:
            return
        if self.request_queue is None or not self.solutions:
            return
        remaining = len(self.solutions) - 1 - self.current_solution_index
        if remaining < PREFETCH_THRESHOLD:
            self.request_queue.put(1)
            self.batch_pending = True

    def _update_solver_ui(self):
        if self.solver_error:
            self.status_label.configure(
                text=f"Solver error: {self.solver_error}")
            self.solve_button.configure(state='normal', text='Solve')
            self.next_button.configure(state='disabled', text='Next ▶')
            return

        if self.current_solution_index == -1:
            if self.solver_done:
                self.status_label.configure(text="No solution found")
                self.solve_button.configure(state='normal', text='Solve')
                self.next_button.configure(state='disabled', text='Next ▶')
            else:
                self.status_label.configure(text="Solving...")
                self.solve_button.configure(
                    state='disabled', text='Solving...')
                self.next_button.configure(state='disabled', text='Next ▶')
            return

        idx = self.current_solution_index
        total = len(self.solutions)

        if self.solver_done:
            status = f"Solution {idx + 1} of {total} (all found)"
        else:
            status = f"Solution {idx + 1}  •  {total} found so far"

        self.status_label.configure(text=status)
        self.solve_button.configure(state='normal', text='Solve')

        has_more = (idx + 1 < total) or (not self.solver_done)
        self.next_button.configure(
            state='normal' if has_more else 'disabled',
            text='Next ▶',
        )

    def _on_next_solution(self):
        if self.current_solution_index + 1 < len(self.solutions):
            self.current_solution_index += 1
            self._display_solution(self.solutions[self.current_solution_index])
            self._update_solver_ui()
        elif not self.solver_done:
            self.status_label.configure(text="Computing more solutions...")
            self._maybe_request_more()
        else:
            self.status_label.configure(text="No more solutions")

    # ==============================================================
    #  Solve All (background, exhaustive)
    # ==============================================================
    def _on_solve_all(self):
        self._cancel_solver()
        self._cancel_solve_all()
        self._clear_solution_overlay()

        self.solutions = []
        self.current_solution_index = -1
        self.solver_done = False
        self.solver_error = None
        self.batch_pending = False

        self._solve_all_found = 0
        self._solve_all_new = 0
        self._solve_all_done = False
        self._solve_all_aborted = False

        placed_snapshot = [
            {'piece': pp['piece'], 'cells': list(pp['cells'])}
            for pp in self.placed_pieces
        ]

        self.solve_all_cancel = threading.Event()
        self.solve_all_thread = threading.Thread(
            target=self._solve_all_worker,
            args=(placed_snapshot, self.solve_all_cancel),
            daemon=True,
        )
        self.solve_all_thread.start()

        self.solve_button.configure(state='disabled', text='Solve')
        self.solve_all_button.configure(state='disabled', text='Computing...')
        self.next_button.configure(state='disabled', text='Next ▶')
        self.status_label.configure(text="Computing ALL solutions...")

        self.after(300, self._poll_solve_all)

    def _cancel_solve_all(self):
        if self.solve_all_cancel is not None:
            self.solve_all_cancel.set()
        self._solve_all_aborted = True

    def _solve_all_worker(self, placed, cancel_event):
        """
        Runs in a background thread.
        Writes directly to the cache file in append mode (one open handle).
        Updates simple counters (int) that the UI can read.
        """
        from solver import solve

        found = 0
        new_saved = 0
        try:
            gen = solve(placed)
            f = open(CACHE_PATH, 'a', encoding='utf-8')
            try:
                for sol in gen:
                    if cancel_event.is_set():
                        break
                    found += 1
                    s = solution_to_string(sol)
                    if s not in self.cached_set:
                        self.cached_set.add(s)
                        self.cached_solutions.append(s)
                        f.write(json.dumps({'s': s},
                                           separators=(',', ':')) + '\n')
                        new_saved += 1
                        if new_saved % 500 == 0:
                            f.flush()
                    # Update counters so polling UI can see progress
                    self._solve_all_found = found
                    self._solve_all_new = new_saved
            finally:
                f.flush()
                f.close()
        except Exception as e:
            self.solver_error = str(e)
        finally:
            self._solve_all_done = True

    def _poll_solve_all(self):
        if self._solve_all_done:
            self._solve_all_done = False
            self.solve_all_thread = None
            self.solve_all_cancel = None

            # Re-enable buttons
            self.solve_all_button.configure(state='normal', text='Solve All')
            if not self.solver_error:
                self.solve_button.configure(state='normal', text='Solve')

            if not self._solve_all_aborted:
                if self.solver_error:
                    self.status_label.configure(
                        text=f"Solve All error: {self.solver_error}")
                else:
                    self.status_label.configure(
                        text=f"Done. Found {self._solve_all_found} "
                        f"({self._solve_all_new} new saved)")
            self._solve_all_aborted = False
            self._update_cache_label()
            return

        self.status_label.configure(
            text=f"Computing all... found: {self._solve_all_found}, "
            f"new: {self._solve_all_new}"
        )
        # Keep cache label fresh too
        if self._solve_all_new % 200 == 0:
            self._update_cache_label()
        self.after(300, self._poll_solve_all)

    # ==============================================================
    #  Solution overlay helpers
    # ==============================================================
    def _display_solution(self, solution):
        self._clear_solution_overlay()
        self.solver_overlay = list(solution)
        for p in solution:
            for (r, c) in p['cells']:
                self.board[r][c] = p['piece']
                self._draw_cell(r, c)

    def _clear_solution_overlay(self):
        if not self.solver_overlay:
            return
        overlay = self.solver_overlay
        self.solver_overlay = []
        for p in overlay:
            for (r, c) in p['cells']:
                self.board[r][c] = None
                self._draw_cell(r, c)


if __name__ == '__main__':
    app = LonposApp()
    app.mainloop()
