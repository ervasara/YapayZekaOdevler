import pygame
from settings import *
import random

try:
    PACMAN_IMG = pygame.image.load("images/pacman.png")
    PACMAN_IMG = pygame.transform.scale(PACMAN_IMG, (TILE_SIZE - 4, TILE_SIZE - 4))
except Exception as e:
    print("Pacman resmi yüklenemedi:", e)
    PACMAN_IMG = None

try:
    GHOST_IMG = pygame.image.load("images/ghost_red.png")
    GHOST_IMG = pygame.transform.scale(GHOST_IMG, (TILE_SIZE - 4, TILE_SIZE - 4))
except Exception as e:
    print("Ghost resmi yüklenemedi:", e)
    GHOST_IMG = None

# POWER MODE için mavi / scared ghost
try:
    GHOST_POWER_IMG = pygame.image.load("images/ghost_green.png")
    GHOST_POWER_IMG = pygame.transform.scale(GHOST_POWER_IMG, (TILE_SIZE - 4, TILE_SIZE - 4))
except Exception as e:
    print("Power ghost resmi yüklenemedi:", e)
    GHOST_POWER_IMG = None




class Wall(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((TILE_SIZE, TILE_SIZE))
        self.image.fill(BLUE)
        self.rect = self.image.get_rect()
        self.rect.x = x * TILE_SIZE
        self.rect.y = y * TILE_SIZE


class Food(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        
        self.image = pygame.Surface((8, 8))
        self.image.fill(GREEN)
        self.rect = self.image.get_rect()
        self.rect.center = (
            x * TILE_SIZE + TILE_SIZE // 2,
            y * TILE_SIZE + TILE_SIZE // 2,
        )


class PowerUp(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        
        self.image = pygame.Surface((20, 20))
        self.image.fill(WHITE)
        self.rect = self.image.get_rect()
        self.rect.center = (
            x * TILE_SIZE + TILE_SIZE // 2,
            y * TILE_SIZE + TILE_SIZE // 2,
        )


class Pacman(pygame.sprite.Sprite):
    def __init__(self, x, y, game):
        super().__init__()
        self.game = game

        if PACMAN_IMG is not None:
            self.image = PACMAN_IMG.copy()
        else:
            self.image = pygame.Surface((TILE_SIZE - 4, TILE_SIZE - 4))
            self.image.fill(YELLOW)

        self.rect = self.image.get_rect()
        self.rect.x = x * TILE_SIZE
        self.rect.y = y * TILE_SIZE

        self.x = x
        self.y = y
        self.vx = 0
        self.vy = 0
        self.speed = 5
        self.ai_speed = 3
        self.score = 0

    def get_keys(self):
        
        self.vx, self.vy = 0, 0
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            self.vx = -self.speed
        elif keys[pygame.K_RIGHT]:
            self.vx = self.speed
        elif keys[pygame.K_UP]:
            self.vy = -self.speed
        elif keys[pygame.K_DOWN]:
            self.vy = self.speed

    def move_by_ai(self, direction):
        
        self.vx, self.vy = 0, 0
        step = getattr(self, "ai_speed", self.speed)
        if direction == "LEFT":
            self.vx = -step
        elif direction == "RIGHT":
            self.vx = step
        elif direction == "UP":
            self.vy = -step
        elif direction == "DOWN":
            self.vy = step

    def collide_with_walls(self, dx=0, dy=0) -> bool:
        temp_rect = self.rect.move(dx, dy)
        for wall in self.game.walls:
            if temp_rect.colliderect(wall.rect):
                return True
        return False

    def update(self, is_computer):
        
        if not is_computer:
            self.get_keys()
        

        
        if self.vx != 0:
            self.rect.y = (self.rect.y // TILE_SIZE) * TILE_SIZE
        
        if self.vy != 0:
            self.rect.x = (self.rect.x // TILE_SIZE) * TILE_SIZE

        if not self.collide_with_walls(self.vx, 0):
            self.rect.x += self.vx
        else:
            self.vx = 0
        
        if not self.collide_with_walls(0, self.vy):
            self.rect.y += self.vy
        else:
            self.vy = 0

        
        self.x = self.rect.x // TILE_SIZE
        self.y = self.rect.y // TILE_SIZE


class Ghost(pygame.sprite.Sprite):
    def __init__(self, x, y, game):
        super().__init__()
        self.game = game

        # Normal ve power sprite'larını referans olarak sakla
        if GHOST_IMG is not None:
            self.normal_image = GHOST_IMG.copy()
        else:
            self.normal_image = pygame.Surface((TILE_SIZE - 4, TILE_SIZE - 4))
            self.normal_image.fill(RED)

        if GHOST_POWER_IMG is not None:
            self.power_image = GHOST_POWER_IMG.copy()
        else:
            # Power sprite yoksa fallback: mavi kare
            self.power_image = pygame.Surface((TILE_SIZE - 4, TILE_SIZE - 4))
            self.power_image.fill((0, 0, 255))

        # Başlangıçta normal görünüm
        self.image = self.normal_image
        self.rect = self.image.get_rect()
        self.rect.x = x * TILE_SIZE
        self.rect.y = y * TILE_SIZE

        self.speed = 2
        self.direction = random.choice(["UP", "DOWN", "LEFT", "RIGHT"])
        self.move_timer = 0

    def collide_with_walls(self, dx=0, dy=0) -> bool:
        temp_rect = self.rect.move(dx, dy)
        for wall in self.game.walls:
            if temp_rect.colliderect(wall.rect):
                return True
        return False

    def update(self, is_computer):
        # Power mode'a göre sprite + hız seç
        if self.game.power_mode:
            self.image = self.power_image
            self.speed = 1
        else:
            self.image = self.normal_image
            self.speed = 2

        self.move_timer += 1
        if self.move_timer > 30:  # ~0.5 saniyede bir yön değiştir
            self.direction = random.choice(["UP", "DOWN", "LEFT", "RIGHT"])
            self.move_timer = 0

        dx, dy = 0, 0
        if self.direction == "UP":
            dy = -self.speed
        elif self.direction == "DOWN":
            dy = self.speed
        elif self.direction == "LEFT":
            dx = -self.speed
        elif self.direction == "RIGHT":
            dx = self.speed

        # X ekseni
        if not self.collide_with_walls(dx, 0):
            self.rect.x += dx
        else:
            self.direction = random.choice(["UP", "DOWN", "LEFT", "RIGHT"])

        # Y ekseni
        if not self.collide_with_walls(0, dy):
            self.rect.y += dy
        else:
            self.direction = random.choice(["UP", "DOWN", "LEFT", "RIGHT"])

