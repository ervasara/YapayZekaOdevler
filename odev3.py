from collections import deque
import heapq
import tkinter as tk
from tkinter import ttk

GRID = [
    "####################",
    "#S.....#...........#",
    "#.###..#..#####.##.#",
    "#...#..#.......#...#",
    "###.#.#####.###.#.##",
    "#...#.....#.....#..#",
    "#.#####.#.#####.##.#",
    "#.....#.#.....#....#",
    "#.###.#.###.#.####.#",
    "#.....#.....#....G.#",
    "####################",
]
WALL = '#'

# -------------------------
# Grid helper
# -------------------------
def parse_grid(grid):
    start = goal = None
    for r, row in enumerate(grid):
        for c, ch in enumerate(row):
            if ch == 'S':
                start = (r, c)
            elif ch == 'G':
                goal = (r, c)
    return start, goal

def in_bounds(grid, r, c):
    return 0 <= r < len(grid) and 0 <= c < len(grid[0])

def neighbors(grid, pos):
    r, c = pos
    for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
        nr, nc = r+dr, c+dc
        if in_bounds(grid, nr, nc) and grid[nr][nc] != WALL:
            yield (nr, nc)

def reconstruct_path(came_from, start, goal):
    if goal not in came_from:
        return None
    path = []
    cur = goal
    while cur is not None:
        path.append(cur)
        cur = came_from[cur]
    path.reverse()
    return path

# -------------------------
# Tkinter GUI Visualizer
# -------------------------
class GridGUI:
    def __init__(self, root, grid):
        self.root = root
        self.grid = grid
        self.R = len(grid)
        self.C = len(grid[0])

        self.cell_size = 28
        self.canvas = tk.Canvas(root, width=self.C*self.cell_size, height=self.R*self.cell_size)
        self.canvas.grid(row=0, column=0, padx=10, pady=10, rowspan=10)

        self.info = tk.StringVar(value="Hazır")
        ttk.Label(root, textvariable=self.info, font=("Arial", 12)).grid(row=0, column=1, sticky="w", padx=10)

        self.algo = tk.StringVar(value="UCS")
        ttk.Label(root, text="Algoritma:").grid(row=1, column=1, sticky="w", padx=10)
        ttk.Combobox(root, textvariable=self.algo, values=["UCS", "IDS", "BiDS"], state="readonly", width=10)\
            .grid(row=2, column=1, sticky="w", padx=10)

        self.speed = tk.IntVar(value=30)  # ms
        ttk.Label(root, text="Hız (ms):").grid(row=3, column=1, sticky="w", padx=10)
        ttk.Scale(root, from_=1, to=200, variable=self.speed, orient="horizontal", length=160)\
            .grid(row=4, column=1, sticky="w", padx=10)

        self.btn_start = ttk.Button(root, text="Başlat", command=self.start)
        self.btn_start.grid(row=5, column=1, sticky="we", padx=10, pady=5)

        self.btn_reset = ttk.Button(root, text="Reset", command=self.reset)
        self.btn_reset.grid(row=6, column=1, sticky="we", padx=10, pady=5)

        self.rects = {}
        self.draw_base()

        self.running = False
        self.steps = None  # generator
        self.start_pos, self.goal_pos = parse_grid(grid)

    def draw_base(self):
        self.canvas.delete("all")
        self.rects.clear()

        for r in range(self.R):
            for c in range(self.C):
                x1 = c*self.cell_size
                y1 = r*self.cell_size
                x2 = x1 + self.cell_size
                y2 = y1 + self.cell_size

                ch = self.grid[r][c]
                color = "white"
                if ch == WALL: color = "black"
                if ch == 'S': color = "green"
                if ch == 'G': color = "red"

                rid = self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="gray")
                self.rects[(r,c)] = rid

    def paint(self, pos, color):
        if pos in (self.start_pos, self.goal_pos):
            return
        self.canvas.itemconfig(self.rects[pos], fill=color)

    def paint_path(self, path):
        if not path: return
        for p in path[1:-1]:
            self.paint(p, "purple")

    def reset(self):
        self.running = False
        self.steps = None
        self.info.set("Resetlendi")
        self.draw_base()

    def start(self):
        if self.running:
            return
        self.reset()
        self.running = True

        algo = self.algo.get()
        if algo == "UCS":
            self.steps = ucs_steps(self.grid, self.start_pos, self.goal_pos)
        elif algo == "IDS":
            self.steps = ids_steps(self.grid, self.start_pos, self.goal_pos, max_depth=100)
        else:
            self.steps = bids_steps(self.grid, self.start_pos, self.goal_pos)

        self.tick()

    def tick(self):
        if not self.running or self.steps is None:
            return

        try:
            event = next(self.steps)
        except StopIteration:
            self.running = False
            self.info.set("Bitti")
            return

        etype = event["type"]

        # UCS / IDS ortak olaylar
        if etype == "visit":
            self.paint(event["pos"], "lightblue")
        elif etype == "frontier":
            self.paint(event["pos"], "khaki")
        elif etype == "current":
            self.paint(event["pos"], "orange")

        # BiDS özel
        elif etype == "visit_f":
            self.paint(event["pos"], "deepskyblue")
        elif etype == "visit_b":
            self.paint(event["pos"], "pink")
        elif etype == "meeting":
            self.paint(event["pos"], "gold")

        elif etype == "info":
            self.info.set(event["text"])

        elif etype == "done":
            self.info.set(event["text"])
            if event.get("path"):
                self.paint_path(event["path"])
            self.running = False
            return

        self.root.after(self.speed.get(), self.tick)

# -------------------------
# UCS (step generator)
# -------------------------
def ucs_steps(grid, start, goal):
    frontier = []
    heapq.heappush(frontier, (0, start))
    came_from = {start: None}
    cost_so_far = {start: 0}
    expanded = 0
    in_frontier = {start}

    yield {"type":"info", "text":"UCS başladı"}

    while frontier:
        cost, current = heapq.heappop(frontier)
        expanded += 1

        yield {"type":"current", "pos": current}
        yield {"type":"visit", "pos": current}

        if current == goal:
            path = reconstruct_path(came_from, start, goal)
            yield {"type":"done", "text":f"UCS bitti | expanded={expanded} | path_len={len(path)}", "path": path}
            return

        for nxt in neighbors(grid, current):
            new_cost = cost_so_far[current] + 1
            if nxt not in cost_so_far or new_cost < cost_so_far[nxt]:
                cost_so_far[nxt] = new_cost
                came_from[nxt] = current
                heapq.heappush(frontier, (new_cost, nxt))
                if nxt not in in_frontier:
                    in_frontier.add(nxt)
                    yield {"type":"frontier", "pos": nxt}

    yield {"type":"done", "text":f"UCS çözüm yok | expanded={expanded}", "path": None}

# -------------------------
# IDS (step generator)
# -------------------------
def ids_steps(grid, start, goal, max_depth=100):
    expanded = 0
    yield {"type":"info", "text":"IDS başladı"}

    def dls(cur, limit, visited_path, came_from):
        nonlocal expanded
        expanded += 1
        yield {"type":"current", "pos": cur}
        yield {"type":"visit", "pos": cur}

        if cur == goal:
            return True

        if limit == 0:
            return False

        for nxt in neighbors(grid, cur):
            if nxt in visited_path:
                continue
            visited_path.add(nxt)
            came_from[nxt] = cur
            found = yield from dls(nxt, limit-1, visited_path, came_from)
            if found:
                return True
            visited_path.remove(nxt)

        return False

    for depth in range(max_depth+1):
        yield {"type":"info", "text":f"IDS depth={depth} | expanded={expanded}"}
        visited_path = {start}
        came_from = {start: None}

        found = yield from dls(start, depth, visited_path, came_from)
        if found:
            path = reconstruct_path(came_from, start, goal)
            yield {"type":"done", "text":f"IDS bitti | expanded={expanded} | path_len={len(path)}", "path": path}
            return

    yield {"type":"done", "text":f"IDS çözüm yok | expanded={expanded}", "path": None}

# -------------------------
# BiDS (step generator)
# -------------------------
def bids_steps(grid, start, goal):
    if start == goal:
        yield {"type":"done", "text":"Start = Goal", "path":[start]}
        return

    frontier_f = deque([start])
    frontier_b = deque([goal])

    parents_f = {start: None}
    parents_b = {goal: None}

    visited_f = {start}
    visited_b = {goal}

    expanded = 0
    yield {"type":"info", "text":"BiDS başladı"}

    while frontier_f and frontier_b:
        # forward layer
        for _ in range(len(frontier_f)):
            cur = frontier_f.popleft()
            expanded += 1
            yield {"type":"visit_f", "pos": cur}

            for nxt in neighbors(grid, cur):
                if nxt not in visited_f:
                    visited_f.add(nxt)
                    parents_f[nxt] = cur
                    frontier_f.append(nxt)

                    if nxt in visited_b:
                        meeting = nxt
                        yield {"type":"meeting", "pos": meeting}
                        path = reconstruct_bids_path(parents_f, parents_b, meeting)
                        yield {"type":"done", "text":f"BiDS bitti | expanded={expanded} | path_len={len(path)}", "path": path}
                        return

        # backward layer
        for _ in range(len(frontier_b)):
            cur = frontier_b.popleft()
            expanded += 1
            yield {"type":"visit_b", "pos": cur}

            for nxt in neighbors(grid, cur):
                if nxt not in visited_b:
                    visited_b.add(nxt)
                    parents_b[nxt] = cur
                    frontier_b.append(nxt)

                    if nxt in visited_f:
                        meeting = nxt
                        yield {"type":"meeting", "pos": meeting}
                        path = reconstruct_bids_path(parents_f, parents_b, meeting)
                        yield {"type":"done", "text":f"BiDS bitti | expanded={expanded} | path_len={len(path)}", "path": path}
                        return

    yield {"type":"done", "text":f"BiDS çözüm yok | expanded={expanded}", "path": None}

def reconstruct_bids_path(parents_f, parents_b, meeting):
    # start -> meeting
    path1 = []
    cur = meeting
    while cur is not None:
        path1.append(cur)
        cur = parents_f[cur]
    path1.reverse()

    # meeting -> goal
    path2 = []
    cur = parents_b[meeting]
    while cur is not None:
        path2.append(cur)
        cur = parents_b[cur]

    return path1 + path2

# -------------------------
# Run GUI
# -------------------------
def main():
    root = tk.Tk()
    root.title("Search Algorithms Visualizer (UCS / IDS / BiDS)")
    app = GridGUI(root, GRID)
    root.mainloop()

if __name__ == "__main__":
    main()
