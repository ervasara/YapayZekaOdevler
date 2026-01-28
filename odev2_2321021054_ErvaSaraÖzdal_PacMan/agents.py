import random
from collections import deque
from settings import *


class UtilityAgent:
    def __init__(self, game):
        self.game = game
        self.last_action = None  

    def get_action(self, player, ghosts, foods, powerups):
  

        
        px = player.rect.x // TILE_SIZE
        py = player.rect.y // TILE_SIZE

        
        blocked = set()
        for y, row in enumerate(GAME_MAP):
            for x, tile in enumerate(row):
                if tile == 1:      
                    blocked.add((x, y))

        
        if not self.game.power_mode:
            for g in ghosts:
                gx = g.rect.x // TILE_SIZE
                gy = g.rect.y // TILE_SIZE
                blocked.add((gx, gy))

        
        targets = []
        if powerups:
            for p in powerups:
                tx = p.rect.x // TILE_SIZE
                ty = p.rect.y // TILE_SIZE
                targets.append((tx, ty))
        else:
            for f in foods:
                tx = f.rect.x // TILE_SIZE
                ty = f.rect.y // TILE_SIZE
                targets.append((tx, ty))

        
        if not targets:
            action = self.random_legal_move(px, py, blocked)
            self.last_action = action
            return action

        
        first_step = self.bfs_first_step((px, py), targets, blocked)

        if first_step is None:
            
            action = self.random_legal_move(px, py, blocked)
            self.last_action = action
            return action

        nx, ny = first_step
        dx = nx - px
        dy = ny - py

        if dx == -1:
            action = "LEFT"
        elif dx == 1:
            action = "RIGHT"
        elif dy == -1:
            action = "UP"
        elif dy == 1:
            action = "DOWN"
        else:
            action = None

        self.last_action = action
        return action

    def random_legal_move(self, px, py, blocked):
  
        moves = {
            "UP": (0, -1),
            "DOWN": (0, 1),
            "LEFT": (-1, 0),
            "RIGHT": (1, 0),
        }

        legal = []
        h = len(GAME_MAP)
        w = len(GAME_MAP[0])

        for name, (dx, dy) in moves.items():
            nx, ny = px + dx, py + dy
            if 0 <= nx < w and 0 <= ny < h and (nx, ny) not in blocked:
                legal.append(name)

        if not legal:
            return None

        
        opposite = {"UP": "DOWN", "DOWN": "UP", "LEFT": "RIGHT", "RIGHT": "LEFT"}
        if self.last_action and opposite.get(self.last_action) in legal and len(legal) > 1:
            legal.remove(opposite[self.last_action])

        return random.choice(legal)

    def bfs_first_step(self, start, targets, blocked):
       
        w = len(GAME_MAP[0])
        h = len(GAME_MAP)

        from collections import deque
        q = deque()
        q.append(start)
        visited = {start: None}
        target_set = set(targets)

        dirs = [(1, 0), (-1, 0), (0, 1), (0, -1)]

        found = None

        while q:
            x, y = q.popleft()

            if (x, y) in target_set:
                found = (x, y)
                break

            for dx, dy in dirs:
                nx, ny = x + dx, y + dy
                if (
                    0 <= nx < w
                    and 0 <= ny < h
                    and (nx, ny) not in blocked
                    and (nx, ny) not in visited
                ):
                    visited[(nx, ny)] = (x, y)
                    q.append((nx, ny))

        if found is None:
            return None

        
        cur = found
        prev = visited[cur]
        while prev is not None and prev != start:
            cur = prev
            prev = visited[cur]

        if prev is None:  
            return None

        return cur
