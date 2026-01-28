import pygame
import sys
import random

from settings import *
from sprites import *
from agents import UtilityAgent


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Pacman AI - Utility Agent")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("arial", 20)
        self.running = True

        
        self.all_sprites = pygame.sprite.Group()
        self.walls = pygame.sprite.Group()
        self.food = pygame.sprite.Group()
        self.powerups = pygame.sprite.Group()
        self.ghosts = pygame.sprite.Group()

        self.player: Pacman | None = None

        
        self.is_computer = False
        self.agent = UtilityAgent(self)

       
        self.last_ai_cell = None
        self.stuck_frames = 0


        
        self.start_time = None
        self.elapsed_time = 0.0

        
        self.power_mode = False
        self.power_mode_end = 0

        
        try:
            pygame.mixer.init()
            self.eat_sound = pygame.mixer.Sound("sounds/pacman_chomp.wav")
            self.power_sound = pygame.mixer.Sound("sounds/pacman_extrapac.wav")
            self.death_sound = pygame.mixer.Sound("sounds/pacman_death.wav")
        except Exception as e:
            print("Ses yüklenemedi:", e)
            self.eat_sound = None
            self.power_sound = None
            self.death_sound = None

    def create_map(self):
        
        for row, tiles in enumerate(GAME_MAP):
            for col, tile in enumerate(tiles):
                if tile == 1:
                    wall = Wall(col, row)
                    self.all_sprites.add(wall)
                    self.walls.add(wall)
                elif tile == 0:
                    food = Food(col, row)
                    self.all_sprites.add(food)
                    self.food.add(food)
                elif tile == 2:
                    power = PowerUp(col, row)
                    self.all_sprites.add(power)
                    self.powerups.add(power)
                elif tile == 4:
                    ghost = Ghost(col, row, self)
                    self.all_sprites.add(ghost)
                    self.ghosts.add(ghost)
                elif tile == 3:
                    self.player = Pacman(col, row, self)
                    self.all_sprites.add(self.player)

    def show_start_menu(self):
        waiting = True
        while waiting:
            self.screen.fill(BLACK)
            title = self.font.render("PAC-MAN AI PROJESI", True, YELLOW)
            info1 = self.font.render("1 - Oyuncu (Sen Oynarsin)", True, WHITE)
            info2 = self.font.render("2 - Bilgisayar (AI Ajan)", True, WHITE)
            info3 = self.font.render("ESC - Cikis", True, WHITE)

            self.screen.blit(
                title,
                (WIDTH // 2 - title.get_width() // 2, HEIGHT // 2 - 80),
            )
            self.screen.blit(
                info1,
                (WIDTH // 2 - info1.get_width() // 2, HEIGHT // 2 - 20),
            )
            self.screen.blit(
                info2,
                (WIDTH // 2 - info2.get_width() // 2, HEIGHT // 2 + 10),
            )
            self.screen.blit(
                info3,
                (WIDTH // 2 - info3.get_width() // 2, HEIGHT // 2 + 40),
            )

            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_1:
                        self.is_computer = False
                        waiting = False
                    elif event.key == pygame.K_2:
                        self.is_computer = True
                        waiting = False
                    elif event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()

    def run(self):
        
        self.start_time = pygame.time.get_ticks()
        while self.running:
            self.clock.tick(FPS)
            self.events()
            self.update()
            self.draw()

        self.show_game_over()

    def events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

        
        if self.is_computer and self.player:
            action = self.agent.get_action(
                self.player,
                self.ghosts,     
                self.food,       
                self.powerups    
            )
            if action:
                self.player.move_by_ai(action)



    def random_legal_move(self):
        """Pac-Man için duvar olmayan rastgele bir yön seçer."""
        moves = {
            "UP": (0, -1),
            "DOWN": (0, 1),
            "LEFT": (-1, 0),
            "RIGHT": (1, 0),
        }

        px = self.player.rect.x // TILE_SIZE
        py = self.player.rect.y // TILE_SIZE

        legal = []
        for name, (dx, dy) in moves.items():
            nx, ny = px + dx, py + dy

            
            if (
                0 <= ny < len(GAME_MAP)
                and 0 <= nx < len(GAME_MAP[0])
                and GAME_MAP[ny][nx] != 1  
            ):
                legal.append(name)

        if legal:
            return random.choice(legal)
        return None
            




    def update(self):
        
        if self.start_time is not None:
            now = pygame.time.get_ticks()
            self.elapsed_time = (now - self.start_time) / 1000.0

        
        if self.power_mode and pygame.time.get_ticks() > self.power_mode_end:
            self.power_mode = False

        
        self.all_sprites.update(self.is_computer)

        
        hits_food = pygame.sprite.spritecollide(self.player, self.food, True)
        for _ in hits_food:
            self.player.score += 10
            if self.eat_sound:
                self.eat_sound.play()

        
        hits_power = pygame.sprite.spritecollide(self.player, self.powerups, True)
        for _ in hits_power:
            self.power_mode = True
            self.power_mode_end = pygame.time.get_ticks() + 2000  
            if self.power_sound:
                self.power_sound.play()

        
        hits_ghost = pygame.sprite.spritecollide(self.player, self.ghosts, False)
        if hits_ghost:
            if self.power_mode:
                
                for g in hits_ghost:
                    g.kill()
                    self.player.score += 200
            else:
                
                if self.death_sound:
                    self.death_sound.play()
                print("YAKALANDIN! Skor:", self.player.score)
                self.running = False

        
        if len(self.food) == 0 and self.running:
            print("TÜM YEMEKLER YENDI! Skor:", self.player.score)
            self.running = False

    def draw(self):
        self.screen.fill(BLACK)
        self.all_sprites.draw(self.screen)

        
        score_text = self.font.render(f"Skor: {self.player.score}", True, WHITE)
        self.screen.blit(score_text, (10, 10))

        
        time_text = self.font.render(f"Süre: {self.elapsed_time:.1f} sn", True, WHITE)
        self.screen.blit(time_text, (10, 35))

        
        mode = "Bilgisayar (AI)" if self.is_computer else "Oyuncu"
        mode_text = self.font.render(f"Mod: {mode}", True, WHITE)
        self.screen.blit(mode_text, (10, 60))

        
        if self.power_mode:
            p_text = self.font.render("POWER MODE!", True, YELLOW)
            self.screen.blit(
                p_text,
                (WIDTH // 2 - p_text.get_width() // 2, 10),
            )

        pygame.display.flip()

    def show_game_over(self):
        
        waiting = True
        while waiting:
            self.screen.fill(BLACK)

            title = self.font.render("GAME OVER", True, RED)
            self.screen.blit(title, (WIDTH // 2 - 60, HEIGHT // 2 - 80))

            mode = "Bilgisayar (AI)" if self.is_computer else "Oyuncu"
            mode_text = self.font.render(f"Mod: {mode}", True, WHITE)
            self.screen.blit(mode_text, (WIDTH // 2 - 120, HEIGHT // 2 - 40))

            score_text = self.font.render(
                f"Skor: {self.player.score}", True, WHITE
            )
            self.screen.blit(score_text, (WIDTH // 2 - 120, HEIGHT // 2 - 10))

            time_text = self.font.render(
                f"Süre: {self.elapsed_time:4.1f} sn", True, WHITE
            )
            self.screen.blit(time_text, (WIDTH // 2 - 120, HEIGHT // 2 + 20))

            info_text = self.font.render(
                "Cikmak icin ESC veya pencereyi kapat.", True, WHITE
            )
            self.screen.blit(info_text, (WIDTH // 2 - 200, HEIGHT // 2 + 60))

            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    waiting = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        waiting = False

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    game = Game()
    game.create_map()
    game.show_start_menu()
    game.run()
