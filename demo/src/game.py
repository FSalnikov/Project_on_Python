import pygame
import sys
import math
from .environment import Environment
from .brain import Brain

class Game:
    def __init__(self, visualization_mode=True, load_genome_path=None):
        # Инициализация pygame
        pygame.init()
        
        # Настройки окна
        self.WIDTH = 800
        self.HEIGHT = 600
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        pygame.display.set_caption("Self-Parking Car")

        # Цвета
        self.WHITE = (255, 255, 255)
        self.BLACK = (0, 0, 0)
        self.BLUE = (0, 0, 255)
        self.RED = (255, 0, 0)
        self.GREEN = (0, 255, 0)
        self.PINK = (255, 105, 180)

        # Создание среды
        self.env = Environment()
        
        # Настройка режима визуализации
        self.visualization_mode = visualization_mode
        self.brain = None
        if visualization_mode and load_genome_path:
            with open(load_genome_path, 'r') as f:
                genome = list(map(int, f.read().split(",")))
                self.brain = Brain(genome)

        # Игровые объекты
        self.custom_rectangles = []
        self.font = pygame.font.Font(None, 36)
        self.clock = pygame.time.Clock()

        # Флаг работы игры
        self.running = True

    def handle_events(self):
        """Обработка событий"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            # Обработка кликов мыши для создания препятствий
            if event.type == pygame.MOUSEBUTTONDOWN:
                self._handle_mouse_click(event)

            # Обработка клавиш
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_0:  # Сброс игры
                    self.env.reset()
                if event.key == pygame.K_ESCAPE:  # Выход
                    self.running = False

    def _handle_mouse_click(self, event):
        """Обработка кликов мыши"""
        mouse_pos = event.pos
        clicked_rect = None

        # Проверка клика по существующему препятствию
        for rect in self.custom_rectangles:
            if rect.collidepoint(mouse_pos):
                clicked_rect = rect
                break

        if event.button == 1:  # Левый клик
            if clicked_rect:
                self.custom_rectangles.remove(clicked_rect)
            else:
                # Создание нового препятствия
                new_rect = pygame.Rect(
                    mouse_pos[0] - self.env.rectangle_width // 2,
                    mouse_pos[1] - self.env.rectangle_height // 2,
                    self.env.rectangle_width,
                    self.env.rectangle_height
                )
                self.custom_rectangles.append(new_rect)

        elif event.button == 3:  # Правый клик
            if clicked_rect:
                # Поворот препятствия
                new_rect = pygame.Rect(
                    clicked_rect.x,
                    clicked_rect.y,
                    clicked_rect.height,
                    clicked_rect.width
                )
                self.custom_rectangles.remove(clicked_rect)
                self.custom_rectangles.append(new_rect)

    def update(self):
        """Обновление состояния игры"""
        if self.visualization_mode and self.brain:
            # Получение состояния среды
            state = self.env.get_state()
            # Получение действия от мозга
            action = self.brain.make_decision(state['sensors'])
            # Выполнение действия
            self.env.step(action)
        else:
            # Ручное управление
            keys = pygame.key.get_pressed()
            action = {'engine': 0, 'wheels': 0}
            
            if keys[pygame.K_UP]:
                action['engine'] = 1
            if keys[pygame.K_DOWN]:
                action['engine'] = -1
            if keys[pygame.K_LEFT]:
                action['wheels'] = -1
            if keys[pygame.K_RIGHT]:
                action['wheels'] = 1
            if keys[pygame.K_SPACE]:
                action['engine'] = 0
                
            self.env.step(action)

    def draw(self):
        """Отрисовка игры"""
        # Очистка экрана
        self.screen.fill(self.WHITE)

        # Отрисовка парковочного места
        pygame.draw.rect(self.screen, self.BLACK, self.env.parking_spot)

        # Отрисовка барьеров
        for barrier in self.env.barriers:
            pygame.draw.rect(self.screen, self.BLACK, barrier)

        # Отрисовка пользовательских препятствий
        for rect in self.custom_rectangles:
            pygame.draw.rect(self.screen, self.PINK, rect)

        # Отрисовка машины
        self._draw_car()

        # Отрисовка сенсоров
        if self.visualization_mode:
            self._draw_sensors()

        # Отрисовка информации
        self._draw_info()

        # Обновление экрана
        pygame.display.flip()

    def _draw_car(self):
        """Отрисовка машины"""
        # Отрисовка основного прямоугольника машины
        rotated_car = pygame.transform.rotate(
            self.env.rectangle_surf, 
            -self.env.current_state['rotation']
        )
        car_rect = rotated_car.get_rect(
            center=(
                self.env.current_state['car_pos_x'],
                self.env.current_state['car_pos_y']
            )
        )
        self.screen.blit(rotated_car, car_rect)

    def _draw_sensors(self):
        """Отрисовка сенсоров"""
        for i, distance in enumerate(self.env.ray_distances):
            angle = i * 45 + self.env.current_state['rotation']
            start_pos = (
                self.env.current_state['car_pos_x'],
                self.env.current_state['car_pos_y']
            )
            end_pos = (
                start_pos[0] + distance * math.cos(math.radians(angle)),
                start_pos[1] + distance * math.sin(math.radians(angle))
            )
            pygame.draw.line(self.screen, self.GREEN, start_pos, end_pos)

    def _draw_info(self):
        """Отрисовка информации"""
        # Отображение расстояния до парковки
        distance_text = self.font.render(
            f"Distance: {self.env.average_distance:.2f}", 
            True, 
            self.BLACK
        )
        self.screen.blit(distance_text, (10, 10))

        # Отображение количества столкновений
        collision_text = self.font.render(
            f"Collisions: {self.env.current_state['collision_counter']}", 
            True, 
            self.BLACK
        )
        self.screen.blit(collision_text, (10, 50))


        # Отображение времени
        time_text = self.font.render(
            f"Time: {self.env.current_state['time_elapsed']:.2f}s",
            True,
            self.BLACK
        )
        self.screen.blit(time_text, (10, 90))

        # Отображение значений сенсоров
        sensors_text = self.font.render(
            f"Sensors: {self.env.ray_distances}",
            True,
            self.BLACK
        )
        self.screen.blit(
            sensors_text,
            (self.WIDTH - sensors_text.get_width() - 10, 
             self.HEIGHT - sensors_text.get_height() - 10)
        )

        # Отображение сообщения об успешной парковке
        if self.env._is_parked_correctly():
            success_text = self.font.render(
                "Parked Successfully!",
                True,
                self.GREEN
            )
            self.screen.blit(
                success_text,
                (self.WIDTH // 2 - success_text.get_width() // 2, 50)
            )

    def run(self):
        """Основной игровой цикл"""
        while self.running:
            # Обработка событий
            self.handle_events()
            
            # Обновление состояния
            self.update()
            
            # Отрисовка
            self.draw()
            
            # Ограничение FPS
            self.clock.tick(60)

        # Завершение работы
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    # Пример запуска в режиме визуализации с загруженным геномом
    game = Game(
        visualization_mode=True,
        load_genome_path="results/best_genome.txt"
    )
    game.run()