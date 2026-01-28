import pygame
import random
import time

# --- Sabitler ---
BOARD_SIZE = 8
SQUARE_SIZE = 60
BOARD_PIXEL_SIZE = BOARD_SIZE * SQUARE_SIZE
SCREEN_WIDTH = BOARD_PIXEL_SIZE + 200 # Sağ taraf için boşluk
SCREEN_HEIGHT = BOARD_PIXEL_SIZE

# Renkler
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
LIGHT_SQUARE = (200, 200, 200)
DARK_SQUARE = (100, 100, 100)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
BUTTON_COLOR = (150, 150, 250)
TEXT_COLOR = (255, 255, 255)

class QueensProblem:
    def __init__(self, size=8):
        self.size = size

    def get_h(self, state):
        attacks = 0
        for i in range(self.size):
            for j in range(i + 1, self.size):
                if state[i] == state[j]:
                    attacks += 1
                if abs(state[i] - state[j]) == abs(i - j):
                    attacks += 1
        return attacks

    def get_neighbors(self, state):
        neighbors = []
        for col in range(self.size):
            original_row = state[col]
            for row in range(self.size):
                if original_row != row:
                    neighbor = list(state)
                    neighbor[col] = row
                    neighbors.append(tuple(neighbor))
        return neighbors



def steepest_ascent_hill_climbing_gen(problem):
    current = tuple(random.randint(0, 7) for _ in range(8))
    steps = 0
    yield current, steps, problem.get_h(current) # İlk durum

    while True:
        neighbors = problem.get_neighbors(current)
        if not neighbors: # Hiç komşu yoksa 
            break
        
        best_neighbor = min(neighbors, key=lambda s: problem.get_h(s))
        
        if problem.get_h(best_neighbor) >= problem.get_h(current):
            break # Yerel optimuma takıldı veya çözüldü
        
        current = best_neighbor
        steps += 1
        yield current, steps, problem.get_h(current) # Her adım

    return current, steps, problem.get_h(current) # Son durum

def stochastic_hill_climbing_gen(problem):
    current = tuple(random.randint(0, 7) for _ in range(8))
    steps = 0
    yield current, steps, problem.get_h(current) # İlk durum

    while True:
        current_h = problem.get_h(current)
        neighbors = problem.get_neighbors(current)
        better_neighbors = [s for s in neighbors if problem.get_h(s) < current_h]
        
        if not better_neighbors:
            break # Yerel optimuma takıldı veya çözüldü
        
        current = random.choice(better_neighbors)
        steps += 1
        yield current, steps, problem.get_h(current) # Her adım

    return current, steps, problem.get_h(current) # Son durum

def random_restart_hill_climbing_gen(problem):
    total_steps = 0
    restarts = 0
    
    while True:
        # Steepest Ascent'i iç döngü olarak kullanıyorum
        sa_generator = steepest_ascent_hill_climbing_gen(problem)
        for state, steps_in_restart, h_val in sa_generator:
            yield state, total_steps + steps_in_restart, h_val 
        
        # Generator'ın son değeri (bir sonraki yield'e kadar beklemek yerine)
        final_sa_state, final_sa_steps, final_sa_h_val = state, steps_in_restart, h_val 

        total_steps += final_sa_steps
        if final_sa_h_val == 0:
            break 
        
        restarts += 1
        # Yeni bir başlangıç durumu 
        problem.current_state = tuple(random.randint(0, 7) for _ in range(8))
   
        yield problem.current_state, total_steps, problem.get_h(problem.current_state)

    return final_sa_state, total_steps, final_sa_h_val # Son durum

# Arayüz 

def draw_board(screen, board_state):
    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):
            color = LIGHT_SQUARE if (row + col) % 2 == 0 else DARK_SQUARE
            pygame.draw.rect(screen, color, (col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))
            
            # Vezir çiz
            if board_state[col] == row:
                pygame.draw.circle(screen, BLACK, 
                                   (col * SQUARE_SIZE + SQUARE_SIZE // 2, 
                                    row * SQUARE_SIZE + SQUARE_SIZE // 2), 
                                   SQUARE_SIZE // 3)
                pygame.draw.circle(screen, WHITE, 
                                   (col * SQUARE_SIZE + SQUARE_SIZE // 2, 
                                    row * SQUARE_SIZE + SQUARE_SIZE // 2), 
                                   SQUARE_SIZE // 3 - 5)

def draw_text(screen, text, x, y, color, font_size=20):
    font = pygame.font.Font(None, font_size)
    text_surface = font.render(text, True, color)
    screen.blit(text_surface, (x, y))

def draw_button(screen, text, rect, color, text_color):
    pygame.draw.rect(screen, color, rect)
    pygame.draw.rect(screen, BLACK, rect, 2) # Kenarlık
    font = pygame.font.Font(None, 24)
    text_surface = font.render(text, True, text_color)
    text_rect = text_surface.get_rect(center=rect.center)
    screen.blit(text_surface, text_rect)

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("8-Vezir Hill Climbing Visualizer")
    clock = pygame.time.Clock()
    
    problem = QueensProblem()
    
    # Algoritma seçimi için butonlar
    sa_button_rect = pygame.Rect(BOARD_PIXEL_SIZE + 20, 50, 160, 40)
    st_button_rect = pygame.Rect(BOARD_PIXEL_SIZE + 20, 100, 160, 40)
    rr_button_rect = pygame.Rect(BOARD_PIXEL_SIZE + 20, 150, 160, 40)
    
    current_algorithm = None
    algorithm_generator = None
    current_state = tuple(random.randint(0, 7) for _ in range(8))
    current_steps = 0
    current_h_val = problem.get_h(current_state)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if sa_button_rect.collidepoint(event.pos):
                    current_algorithm = "Steepest-Ascent"
                    algorithm_generator = steepest_ascent_hill_climbing_gen(problem)
                    current_state = tuple(random.randint(0, 7) for _ in range(8)) # Yeni başlangıç
                    current_steps = 0
                    current_h_val = problem.get_h(current_state)

                elif st_button_rect.collidepoint(event.pos):
                    current_algorithm = "Stochastic"
                    algorithm_generator = stochastic_hill_climbing_gen(problem)
                    current_state = tuple(random.randint(0, 7) for _ in range(8)) # Yeni başlangıç
                    current_steps = 0
                    current_h_val = problem.get_h(current_state)

                elif rr_button_rect.collidepoint(event.pos):
                    current_algorithm = "Random-Restart"
                    algorithm_generator = random_restart_hill_climbing_gen(problem)
                    current_state = tuple(random.randint(0, 7) for _ in range(8)) # Yeni başlangıç
                    current_steps = 0
                    current_h_val = problem.get_h(current_state)

        screen.fill(BLUE) # Arka plan
        draw_board(screen, current_state)

        
        draw_button(screen, "Steepest-Ascent", sa_button_rect, BUTTON_COLOR, TEXT_COLOR)
        draw_button(screen, "Stochastic", st_button_rect, BUTTON_COLOR, TEXT_COLOR)
        draw_button(screen, "Random-Restart", rr_button_rect, BUTTON_COLOR, TEXT_COLOR)

        draw_text(screen, f"Algoritma: {current_algorithm if current_algorithm else 'Yok'}", BOARD_PIXEL_SIZE + 20, 250, WHITE)
        draw_text(screen, f"Heuristic (Saldırı): {current_h_val}", BOARD_PIXEL_SIZE + 20, 280, WHITE)
        draw_text(screen, f"Adım Sayısı: {current_steps}", BOARD_PIXEL_SIZE + 20, 310, WHITE)
        
        
        if algorithm_generator:
            try:
                current_state, current_steps, current_h_val = next(algorithm_generator)
                time.sleep(0.1) 
            except StopIteration:
                algorithm_generator = None 

        pygame.display.flip()
        clock.tick(60) 

    pygame.quit()

if __name__ == "__main__":
    main()