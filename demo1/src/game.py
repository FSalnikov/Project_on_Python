import pygame
import sys
import math
from .environment import Environment


class Game:

    def __init__(self, visualization_mode=True, load_genome_path=None):
        """
        Класс для создания игры "Self-Parking Car", который управляет логикой игры, визуализацией, обработкой событий и взаимодействием с окружающей средой.

        Атрибуты:
            WIDTH (int): Ширина окна игры.
            HEIGHT (int): Высота окна игры.
            screen (pygame.Surface): Объект экрана, на котором происходит отрисовка игры.
            WHITE, BLACK, BLUE, RED, GREEN, PINK (tuple): Цвета для отображения различных элементов на экране.
            env (Environment): Объект, представляющий среду, в которой происходит игра (парковочное место, барьеры, сенсоры).
            visualization_mode (bool): Флаг, указывающий, используется ли нейросеть для управления машиной.
            brain (Brain or None): Объект нейросети для принятия решений (если используется нейросеть).
            custom_rectangles (List[pygame.Rect]): Список пользовательских препятствий, добавляемых в игру.
            font (pygame.font.Font): Шрифт для отображения текста на экране.
            clock (pygame.time.Clock): Объект для контроля частоты кадров (FPS).
            running (bool): Флаг, который указывает, работает ли игра.

        Методы:
            __init__(self, visualization_mode=True, load_genome_path=None): Инициализация игры, создание экрана, настроек и объектов игры.
            handle_events(self): Обработка событий (выход из игры, клики мыши, нажатие клавиш).
            _handle_mouse_click(self, event): Обработка кликов мыши для добавления, удаления или поворота препятствий.
            update(self): Обновление состояния игры, принятие решений с использованием нейросети или ручное управление.
            draw(self): Отрисовка всех элементов игры на экране.
            _draw_car(self): Отрисовка машины в текущем положении и ориентации.
            _draw_sensors(self): Отрисовка лучей сенсоров на экране.
            _draw_info(self): Отображение информации о текущем состоянии игры (расстояние до парковки, столкновения, время и сенсоры).
            run(self): Основной игровой цикл, управляющий процессом игры (обработка событий, обновление, отрисовка, FPS).

        Исключения:
            None

        Примечания:
            Игра может работать как в режиме визуализации с нейросетью (если указан путь к геному), так и в режиме ручного управления.
        """
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
        """
            Обрабатывает все события, происходящие в игре, включая выход из игры, клики мыши и нажатия клавиш.

        Этот метод используется для того, чтобы:
        - Завершить игру при нажатии кнопки закрытия окна.
        - Позволить добавлять или удалять пользовательские препятствия по клику мыши.
        - Обрабатывать нажатия клавиш для сброса игры или выхода.

        Важные события:
            - Событие QUIT: Завершение работы игры при закрытии окна.
            - Событие MOUSEBUTTONDOWN: Обработка кликов мыши для создания/удаления препятствий.
            - Событие KEYDOWN:
                - Клавиша "0": Сброс состояния игры.
                - Клавиша ESCAPE: Выход из игры.

        Принимает:
            Нет параметров.

        Возвращает:
            Нет (метод обновляет состояние игры в реальном времени, но ничего не возвращает).
        """
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
        """
        Обрабатывает клики мыши для добавления, удаления или поворота препятствий.

        Этот метод выполняет следующие действия в зависимости от типа нажатой кнопки мыши:
        - Левый клик (button == 1): Если был клик по существующему препятствию, оно удаляется. Если клик не попал в препятствие, создается новое.
        - Правый клик (button == 3): Поворот выбранного препятствия на 90 градусов.

        Параметры:
            event (pygame.event.Event): Событие, содержащее информацию о нажатии кнопки мыши, включая позицию и тип кнопки.

        Возвращает:
            Нет (метод обновляет состояние игры в реальном времени, но ничего не возвращает).
        """
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
        """
        Обновляет состояние игры. В зависимости от режима работы, выполняет обновление с использованием
        нейронной сети или вручную, обрабатывая входные данные от игрока.

        Если режим визуализации активен и загружен нейронный мозг (brain), метод будет:
        - Получать состояние среды с помощью метода `get_state()` объекта `env`.
        - Принимать решение от нейронной сети на основе сенсоров.
        - Выполнять действие с помощью метода `step()` объекта `env`.

        В противном случае, в режиме ручного управления (без нейронной сети):
        - Получает текущее состояние клавиш с помощью `pygame.key.get_pressed()`.
        - В зависимости от нажатых клавиш выполняет действия:
          - Стрелка вверх (`K_UP`) увеличивает скорость машины.
          - Стрелка вниз (`K_DOWN`) уменьшает скорость машины.
          - Стрелка влево (`K_LEFT`) поворачивает колеса влево.
          - Стрелка вправо (`K_RIGHT`) поворачивает колеса вправо.
          - Пробел (`K_SPACE`) отключает двигатель.
        - После определения действия, выполняется шаг в среде с помощью метода `step()` объекта `env`.

        Параметры:
            Нет (метод обновляет внутреннее состояние игры).

        Возвращает:
            Нет (метод обновляет состояние игры в реальном времени, но ничего не возвращает).
        """
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
        """
    Отрисовывает все элементы игры на экране: парковочное место, барьеры, пользовательские препятствия, машину, сенсоры и информацию.

    Метод выполняет следующие шаги:
    - Очищает экран, заполняя его белым цветом.
    - Отрисовывает парковочное место с помощью `pygame.draw.rect`.
    - Отрисовывает барьеры, которые могут быть частью среды (например, другие объекты на поле).
    - Отрисовывает пользовательские препятствия, добавленные игроком.
    - Отрисовывает машину в текущем положении и с текущей ориентацией.
    - Отрисовывает сенсоры (если активирован режим визуализации).
    - Отображает информацию о текущем состоянии игры, такую как расстояние до парковки, количество столкновений и время.
    - Обновляет экран, чтобы отобразить изменения.

    Параметры:
        Нет (метод выполняет отрисовку всех элементов на экране).

    Возвращает:
        Нет (метод отрисовывает все элементы на экране, но ничего не возвращает).
    """
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
        """
        Отрисовывает машину на экране с учетом текущего положения и ориентации.

        Метод выполняет следующие шаги:
        - Использует текущие данные о позиции и угле поворота машины, чтобы отобразить ее на экране.
        - Поворачивает изображение машины с использованием метода `pygame.transform.rotate`, чтобы оно соответствовало текущему углу поворота.
        - Отображает машину в центре ее текущей позиции с помощью метода `blit`.

        Параметры:
            Нет (метод использует данные, хранящиеся в объекте класса).

        Возвращает:
            Нет (метод выполняет отрисовку машины, но ничего не возвращает).
        """
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
        """
        Отрисовывает сенсоры машины на экране.

        Метод рисует линии, которые представляют собой лучи сенсоров, исходящие от текущей позиции машины.
        Каждый сенсор направлен под углом, который увеличивается на 45 градусов для каждого следующего сенсора.
        Длина линии зависит от измеренного расстояния для каждого сенсора.

        Параметры:
            Нет (метод использует данные, хранящиеся в объекте класса).

        Возвращает:
            Нет (метод выполняет отрисовку сенсоров, но ничего не возвращает).
        """
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
        """
        Отображает информацию о текущем состоянии игры на экране.

        Метод отображает несколько ключевых показателей:
        - Расстояние до парковки.
        - Количество столкновений.
        - Время, прошедшее с начала игры.
        - Значения сенсоров.
        - Сообщение об успешной парковке, если она была выполнена корректно.

        Параметры:
            Нет (метод использует данные, хранящиеся в объекте класса).

        Возвращает:
            Нет (метод выполняет отрисовку информации, но ничего не возвращает).
        """
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
        """
        Основной игровой цикл.

        Этот метод управляет основным циклом игры, который выполняется до тех пор,
        пока флаг `self.running` не будет установлен в `False`. В цикле обрабатываются
        события, обновляется состояние игры, выполняется отрисовка и устанавливается
        ограничение по частоте кадров.

        Параметры:
            Нет (метод использует данные, хранящиеся в объекте класса).

        Возвращает:
            Нет (метод выполняет бесконечный цикл, пока не будет завершен).
        """
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
