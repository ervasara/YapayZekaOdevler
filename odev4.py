from __future__ import annotations
import tkinter as tk
import threading
import heapq
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict, Set

Pos = Tuple[int, int]

MAP = [
    "###################",
    "#P....#.....#.....#",
    "#.###.#.###.#.###.#",
    "#.....#...#.#...#.#",
    "###.#####.#.###.#.#",
    "#...#.....#.....#.#",
    "#.#.#.#########.#.#",
    "#.#.#.....#.....#.#",
    "#.#.#####.#.###.#.#",
    "#...#.....#...#...#",
    "#.###.###.###.###.#",
    "#.....#....G..#..F#",
    "###################",
]

DIRS = [(0, 1), (0, -1), (1, 0), (-1, 0)]


def parse_map(lines: List[str]):
    rows, cols = len(lines), len(lines[0])
    walls: Set[Pos] = set()
    pellets: Set[Pos] = set()
    start: Optional[Pos] = None
    goal: Optional[Pos] = None
    ghost: Optional[Pos] = None

    for r in range(rows):
        for c in range(cols):
            ch = lines[r][c]
            if ch == "#":
                walls.add((r, c))
            elif ch == ".":
                pellets.add((r, c))
            elif ch == "P":
                start = (r, c)
            elif ch == "F":
                goal = (r, c)
            elif ch == "G":
                ghost = (r, c)

    if start is None or goal is None:
        raise ValueError("Map must include 'P' and 'F'.")
    return rows, cols, walls, pellets, start, goal, ghost


ROWS, COLS, WALLS, PELLETS, START, GOAL, GHOST_START = parse_map(MAP)


def in_bounds(p: Pos) -> bool:
    return 0 <= p[0] < ROWS and 0 <= p[1] < COLS


def passable(p: Pos) -> bool:
    return p not in WALLS


def neighbors(p: Pos) -> List[Pos]:
    out = []
    for dr, dc in DIRS:
        np = (p[0] + dr, p[1] + dc)
        if in_bounds(np) and passable(np):
            out.append(np)
    return out


def manhattan(a: Pos, b: Pos) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


# ---------------- RBFS ----------------
def rbfs_search(start: Pos, goal: Pos) -> Optional[List[Pos]]:
    def recurse(node: Pos, g: int, f_node: float, f_limit: float,
                path: List[Pos], in_path: Set[Pos]) -> Tuple[Optional[List[Pos]], float]:

        if node == goal:
            return path, f_node

        succ = []
        for nb in neighbors(node):
            if nb in in_path:
                continue
            g2 = g + 1
            f2 = max(g2 + manhattan(nb, goal), f_node)
            succ.append([nb, g2, f2])

        if not succ:
            return None, float("inf")

        while True:
            succ.sort(key=lambda x: x[2])
            best = succ[0]

            if best[2] > f_limit:
                return None, best[2]

            alternative = succ[1][2] if len(succ) > 1 else float("inf")
            new_limit = min(f_limit, alternative)

            nb, g2, f2 = best
            in_path.add(nb)
            res_path, new_f = recurse(nb, g2, f2, new_limit, path + [nb], in_path)
            in_path.remove(nb)

            best[2] = new_f

            if res_path is not None:
                return res_path, new_f

    start_f = manhattan(start, goal)
    path, _ = recurse(start, 0, start_f, float("inf"), [start], {start})
    return path


# ---------------- SMA* (practical) ----------------
@dataclass(order=True)
class PQItem:
    f: float
    neg_g: int
    state: Pos = field(compare=False)
    g: int = field(compare=False)
    parent: Optional[Pos] = field(compare=False, default=None)


def reconstruct(came_from: Dict[Pos, Pos], end: Pos) -> List[Pos]:
    cur = end
    out = [cur]
    while cur in came_from:
        cur = came_from[cur]
        out.append(cur)
    out.reverse()
    return out


def sma_star_search(start: Pos, goal: Pos, max_nodes: int = 500) -> Optional[List[Pos]]:
    def f_value(state: Pos, g: int, parent_f: float) -> float:
        return max(parent_f, g + manhattan(state, goal))

    open_heap: List[PQItem] = []
    open_f: Dict[Pos, float] = {}
    closed_g: Dict[Pos, int] = {}
    came_from: Dict[Pos, Pos] = {}

    start_f = manhattan(start, goal)
    heapq.heappush(open_heap, PQItem(start_f, 0, start, 0, None))
    open_f[start] = start_f

    def prune_one():
        if not open_f:
            return
        worst_state = max(open_f, key=lambda s: open_f[s])
        del open_f[worst_state]

    while open_heap:
        item = heapq.heappop(open_heap)
        cur = item.state

        if cur not in open_f or open_f[cur] != item.f:
            continue

        del open_f[cur]
        closed_g[cur] = item.g

        if cur == goal:
            return reconstruct(came_from, cur)

        while (len(open_f) + len(closed_g)) >= max_nodes:
            prune_one()
            if not open_f and not open_heap:
                return None
            if (len(open_f) + len(closed_g)) < max_nodes:
                break

        parent_f = item.f
        for nb in neighbors(cur):
            g2 = item.g + 1

            if nb in closed_g and closed_g[nb] <= g2:
                continue

            f2 = f_value(nb, g2, parent_f)

            if nb in open_f and open_f[nb] <= f2:
                continue

            came_from[nb] = cur
            open_f[nb] = f2
            heapq.heappush(open_heap, PQItem(f2, -g2, nb, g2, cur))

    return None


# -------- ASCII çıktı üretimi --------
def ascii_grid(path: Optional[List[Pos]]) -> str:
    path_set = set(path or [])
    lines = []
    for r in range(ROWS):
        row_chars = []
        for c in range(COLS):
            p = (r, c)
            if p in WALLS:
                ch = "#"
            else:
                ch = "."
            if p in path_set and p not in (START, GOAL):
                ch = "*"
            if p == START:
                ch = "S"
            if p == GOAL:
                ch = "G"
            row_chars.append(ch)
        lines.append(" ".join(row_chars))
    return "\n".join(lines)


# ================= GUI =================
class PacmanApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Pac-Man (RBFS & SMA*) — UI + Trail + Output")

        self.T = 28
        self.w = COLS * self.T
        self.h = ROWS * self.T

        self.canvas = tk.Canvas(root, width=self.w, height=self.h, bg="black", highlightthickness=0)
        self.canvas.grid(row=0, column=0, columnspan=6, padx=12, pady=12)

        self.status = tk.StringVar(value="Hazır. RBFS/SMA* ile F hedefine git.")
        tk.Label(root, textvariable=self.status, anchor="w").grid(row=1, column=0, columnspan=6, sticky="ew", padx=12)

        tk.Button(root, text="RBFS", command=lambda: self.run_search("RBFS")).grid(row=2, column=0, padx=6, pady=8, sticky="ew")
        tk.Button(root, text="SMA*", command=lambda: self.run_search("SMA")).grid(row=2, column=1, padx=6, pady=8, sticky="ew")

        self.mem_var = tk.IntVar(value=450)
        tk.Label(root, text="SMA* max_nodes").grid(row=2, column=2, padx=6, sticky="e")
        tk.Entry(root, textvariable=self.mem_var, width=7).grid(row=2, column=3, padx=6, sticky="w")

        tk.Button(root, text="Reset", command=self.reset).grid(row=2, column=4, padx=6, pady=8, sticky="ew")
        tk.Button(root, text="Çıkış", command=root.destroy).grid(row=2, column=5, padx=6, pady=8, sticky="ew")

        # ---- OUTPUT panel (konsol gibi) ----
        self.out = tk.Text(root, height=12, width=90, bg="#0f0f0f", fg="#e6e6e6",
                           insertbackground="#e6e6e6", wrap="none")
        self.out.grid(row=3, column=0, columnspan=6, padx=12, pady=(0, 12), sticky="nsew")
        self.out.config(state="disabled")

        # allow resizing
        root.grid_rowconfigure(3, weight=1)
        root.grid_columnconfigure(5, weight=1)

        self.search_running = False

        self.wall_ids: Dict[Pos, int] = {}
        self.pellet_ids: Dict[Pos, int] = {}
        self.food_id: Optional[int] = None
        self.pac_id: Optional[int] = None

        self.trail_ids: Dict[Pos, int] = {}
        self.trail_color = "#00bcd4"

        self.pac_pos: Pos = START
        self.pac_dir: Pos = (0, 1)
        self.mouth_open = True

        self.draw_world()
        self.reset()

    def log(self, text: str):
        self.out.config(state="normal")
        self.out.insert("end", text + "\n")
        self.out.see("end")
        self.out.config(state="disabled")

    def clear_log(self):
        self.out.config(state="normal")
        self.out.delete("1.0", "end")
        self.out.config(state="disabled")

    def cell_center(self, p: Pos) -> Tuple[float, float]:
        r, c = p
        return (c * self.T + self.T / 2, r * self.T + self.T / 2)

    def draw_world(self):
        self.canvas.delete("all")
        self.wall_ids.clear()
        self.pellet_ids.clear()
        self.trail_ids.clear()
        self.food_id = None
        self.pac_id = None

        # walls
        for r in range(ROWS):
            for c in range(COLS):
                p = (r, c)
                x1, y1 = c * self.T, r * self.T
                x2, y2 = x1 + self.T, y1 + self.T
                if p in WALLS:
                    self.wall_ids[p] = self.canvas.create_rectangle(
                        x1, y1, x2, y2, fill="#0b2cff", outline="#00136b", width=2
                    )

        # pellets
        for p in PELLETS:
            cx, cy = self.cell_center(p)
            self.pellet_ids[p] = self.canvas.create_oval(
                cx - 3, cy - 3, cx + 3, cy + 3, fill="white", outline=""
            )

        # goal (food)
        cx, cy = self.cell_center(GOAL)
        self.food_id = self.canvas.create_oval(cx - 7, cy - 7, cx + 7, cy + 7, fill="#ffd54a", outline="")

        # pacman
        self.pac_id = self.canvas.create_arc(0, 0, 0, 0, start=25, extent=310, fill="yellow", outline="")
        self.draw_pacman(START, (0, 1), True)

    def draw_pacman(self, pos: Pos, direction: Pos, mouth_open: bool):
        cx, cy = self.cell_center(pos)
        R = self.T * 0.42
        x1, y1, x2, y2 = cx - R, cy - R, cx + R, cy + R

        if direction == (0, 1):
            start_ang = 25
        elif direction == (0, -1):
            start_ang = 205
        elif direction == (-1, 0):
            start_ang = 115
        else:
            start_ang = 295

        extent = 310 if mouth_open else 359
        self.canvas.coords(self.pac_id, x1, y1, x2, y2)
        self.canvas.itemconfig(self.pac_id, start=start_ang, extent=extent)

    def paint_trail(self, pos: Pos):
        if pos in WALLS or pos in (START, GOAL):
            return
        if pos in self.trail_ids:
            return
        r, c = pos
        pad = 4
        x1 = c * self.T + pad
        y1 = r * self.T + pad
        x2 = (c + 1) * self.T - pad
        y2 = (r + 1) * self.T - pad
        self.trail_ids[pos] = self.canvas.create_rectangle(
            x1, y1, x2, y2, fill=self.trail_color, outline="", stipple="gray25"
        )
        self.canvas.tag_raise(self.pac_id)
        if self.food_id is not None:
            self.canvas.tag_raise(self.food_id)

    def reset(self):
        self.search_running = False
        self.pac_pos = START
        self.pac_dir = (0, 1)
        self.mouth_open = True
        self.draw_world()
        self.clear_log()
        self.status.set("Reset ✅ (RBFS/SMA* çalıştırınca altta çıktı da gözükecek)")

    def run_search(self, which: str):
        if self.search_running:
            return
        self.search_running = True
        self.status.set(f"{which} hesaplanıyor...")

        start_pos = self.pac_pos

        def worker():
            try:
                if which == "RBFS":
                    path = rbfs_search(start_pos, GOAL)
                else:
                    max_nodes = int(self.mem_var.get())
                    path = sma_star_search(start_pos, GOAL, max_nodes=max_nodes)
            except Exception as e:
                path = None
                self.root.after(0, lambda: self.status.set(f"Hata: {e}"))

            self.root.after(0, lambda: self.show_output_and_animate(path, which))

        threading.Thread(target=worker, daemon=True).start()

    def show_output_and_animate(self, path: Optional[List[Pos]], which: str):
        # GUI output (konsol tarzı)
        self.log(f"=== {which} ===")
        self.log(f"Path: {path}")
        self.log(ascii_grid(path))
        self.log("")  # boş satır

        # (istersen terminale de bas)
        print(f"=== {which} ===")
        print("Path:", path)
        print(ascii_grid(path))
        print()

        self.animate_path(path, which)

    def animate_path(self, path: Optional[List[Pos]], title: str):
        if not path:
            self.status.set(f"{title}: Yol bulunamadı.")
            self.search_running = False
            return

        self.status.set(f"{title}: Yol bulundu. Adım={len(path)-1}. Animasyon + trail...")

        def step(i: int):
            if i >= len(path):
                self.status.set(f"{title}: Bitti ✅")
                self.search_running = False
                return

            cur = path[i]
            if i > 0:
                prev = path[i - 1]
                self.paint_trail(prev)
                self.pac_dir = (cur[0] - prev[0], cur[1] - prev[1])

            self.pac_pos = cur
            self.mouth_open = not self.mouth_open
            self.draw_pacman(self.pac_pos, self.pac_dir, self.mouth_open)

            if cur in self.pellet_ids:
                self.canvas.delete(self.pellet_ids[cur])
                del self.pellet_ids[cur]

            self.root.after(70, lambda: step(i + 1))

        step(0)


if __name__ == "__main__":
    root = tk.Tk()
    PacmanApp(root)
    root.mainloop()

