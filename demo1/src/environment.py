import pygame
import math
from typing import Dict, Tuple, List, Optional


class Environment:
    """
        Класс, представляющий игровую среду, в которой происходит симуляция движения автомобиля и его парковки.

        Этот класс управляет всеми аспектами окружения, включая создание окна игры, барьеров, парковочного места,
        а также вычисление и обновление состояния автомобиля. Он также обрабатывает данные с сенсоров автомобиля
        для оценки окружающей среды и принятия решений.

        Атрибуты:
            WIDTH (int): Ширина окна игры (800 пикселей).
            HEIGHT (int): Высота окна игры (600 пикселей).
            car_rect (pygame.Rect): Прямоугольник, представляющий машину.
            parking_spot (pygame.Rect): Прямоугольник, представляющий парковочное место.
            barriers (List[pygame.Rect]): Список барьеров, ограничивающих пространство для движения автомобиля.
            custom_rectangles (List[pygame.Rect]): Список пользовательских препятствий, добавляемых в игру.
            current_state (Dict): Текущее состояние автомобиля и окружающей среды, включая позицию, скорость и угол поворота.
            ray_distances (List[float]): Список расстояний от сенсоров до препятствий.
            distance_to_parking (float): Расстояние от автомобиля до ближайшей точки на парковке.
            average_distance (float): Среднее расстояние от углов машины до парковочного места.
            episode_finished (bool): Флаг, указывающий завершение эпизода.
            max_episode_steps (int): Максимальное количество шагов в эпизоде.
            current_step (int): Текущий шаг в эпизоде.
            best_distance (float): Лучшее расстояние до парковки.
            current_fitness (float): Текущий показатель фитнеса, отражающий успех парковки.

        Методы:
            __init__(self): Инициализация среды, создание начального состояния и настроек окна.
            _create_barriers(self) -> List[pygame.Rect]: Создание барьеров по периметру окна.
            reset(self) -> Dict: Сброс состояния среды в начальное состояние.
            _ray_distance(self, start_point: Tuple[float, float], angle: float, barriers: List[pygame.Rect], max_distance: int) -> float:
                Расчет расстояния луча до препятствия.
            _update_sensors(self): Обновление показаний сенсоров автомобиля.
            _distance(self, point1: Tuple[float, float], point2: Tuple[float, float]) -> float:
                Расчет расстояния между двумя точками.
            _point_inside_rect(self, point: Tuple[float, float], rect: pygame.Rect) -> bool:
                Проверка, находится ли точка внутри прямоугольника.
            _nearest_point_on_rect(self, rect: pygame.Rect, point: Tuple[float, float]) -> Tuple[float, float]:
                Нахождение ближайшей точки на прямоугольнике от заданной точки.
            _update_parking_distance(self): Обновление расстояния до парковочного места.
            get_state(self) -> Dict: Получение текущего состояния среды, включая данные о сенсорах, позиции машины, расстоянии до парковки и т.д.

        Исключения:
            ValueError: Если длина генома или других входных данных неверна.
    """

    def __init__(self):
        """
        Инициализация среды.

        Создает начальное состояние, инициализирует размеры окна, машины, барьеры,
        парковочное место и другие параметры, такие как максимальная скорость,
        ускорение и замедление.
        """

        # Константы окна
        self.WIDTH = 800
        self.HEIGHT = 600

        # Константы машины
        self.CAR_SIZE = 50 // 5
        self.MAX_SPEED = 5 / 2
        self.MAX_SPEED_BACKWARD = self.MAX_SPEED / 2
        self.ACCELERATION = 0.05 / 2
        self.DECELERATION = 0.05 / 2
        self.MIN_TURN_SPEED = 0.1

        # Размеры прямоугольника машины
        self.rectangle_width = self.CAR_SIZE * 2 * 1.5 // 2 * 2
        self.rectangle_height = self.CAR_SIZE * 3 * 1.5 // 2 * 2

        # Инициализация поверхностей pygame
        self.rectangle_surf = pygame.Surface(
            (self.rectangle_width, self.rectangle_height),
            pygame.SRCALPHA
        )
        self.rectangle_surf.fill((255, 0, 0))  # RED
        self.rectangle_surf = pygame.transform.rotate(self.rectangle_surf, 90)

        # Создание парковочного места
        self.parking_spot = pygame.Rect(
            600, 200,
            int(150 // 3 * 2 / 1.5),
            int(100 // 3 * 2 / 1.5)
        )

        # Создание барьеров
        self.barrier_thickness = int(10 // 3 * 2 / 1.5)
        self.barriers = self._create_barriers()

        # Инициализация rect для машины
        self.car_rect = pygame.Rect(0, 0, self.CAR_SIZE, self.CAR_SIZE)
        self.rotated_collision_rect = None

        # Список пользовательских препятствий
        self.custom_rectangles = []

        # Начальное состояние
        self.initial_state = {
            'car_pos_x': 100.0,
            'car_pos_y': 300.0,
            'car_speed': 0,
            'rotation': 0,
            'collision_counter': 0,
            'time_elapsed': 0
        }

        # Текущее состояние
        self.current_state = self.initial_state.copy()

        # Параметры эпизода
        self.episode_finished = False
        self.max_episode_steps = 1000
        self.current_step = 0

        # Параметры фитнеса и датчиков
        self.best_distance = float('inf')
        self.current_fitness = 0
        self.ray_distances = [0] * 8
        self.average_distance = float('inf')

    def _create_barriers(self) -> List[pygame.Rect]:
        """
        Создание барьеров по периметру окна.

        Возвращает список прямоугольников, представляющих барьеры, которые ограничивают
        область, в которой может двигаться автомобиль.

        Returns:
            List[pygame.Rect]: Список барьеров, окружающих окно.
        """
        return [
            # Верхний барьер
            pygame.Rect(0, 0, self.WIDTH, self.barrier_thickness),
            # Левый барьер
            pygame.Rect(0, 0, self.barrier_thickness, self.HEIGHT),
            # Нижний барьер
            pygame.Rect(0, self.HEIGHT - self.barrier_thickness,
                        self.WIDTH, self.barrier_thickness),
            # Правый барьер
            pygame.Rect(self.WIDTH - self.barrier_thickness, 0,
                        self.barrier_thickness, self.HEIGHT)
        ]

    def reset(self) -> Dict:
        """ Сброс среды в начальное состояние.

        Возвращает начальное состояние среды и сбрасывает параметры эпизода, такие как
        счетчик шагов, коллизии и фитнес.

        Returns:
            Dict: Начальное состояние с данными о сенсорах, позиции машины, скорости и других параметрах.
        """
        self.current_state = self.initial_state.copy()
        self.episode_finished = False
        self.current_step = 0
        self.best_distance = float('inf')
        self.current_fitness = 0
        self._update_sensors()
        return self.get_state()

    def _ray_distance(self, start_point: Tuple[float, float],
                      angle: float, barriers: List[pygame.Rect],
                      max_distance: int) -> float:
        """
        Расчет расстояния луча до препятствия.

        Проверяет, есть ли препятствия на пути луча, начиная с заданной точки и под заданным углом.
        Возвращает расстояние до первого столкновения или максимальное расстояние, если
        препятствия не найдено.

        Args:
            start_point (Tuple[float, float]): Начальная точка луча.
            angle (float): Угол, под которым луч будет двигаться.
            barriers (List[pygame.Rect]): Список препятствий для проверки на коллизии.
            max_distance (int): Максимальное расстояние, на которое будет двигаться луч.

        Returns:
            float: Расстояние до ближайшего препятствия или максимальное расстояние.
        """
        x, y = start_point
        dx = math.cos(math.radians(angle))
        dy = math.sin(math.radians(angle))

        for i in range(int(max_distance)):
            x += dx
            y += dy
            point = (x, y)

            # Проверка на столкновение с препятствиями
            for barrier in barriers:
                if self._point_inside_rect(point, barrier):
                    return i

            # Проверка выхода за границы
            if (x < 0 or x > self.WIDTH or
                    y < 0 or y > self.HEIGHT):
                return i

        return max_distance

    def _update_sensors(self):
        """
        Обновление показаний сенсоров.

        Сенсоры используются для измерения расстояний до объектов в 8 различных направлениях
        вокруг машины. Эти данные используются для расчета награды и проверки столкновений.
        """
        ray_angles = [0, 45, 90, 135, 180, 225, 270, 315]
        self.ray_distances = []

        # Получение центра машины
        start_point = (
            self.current_state['car_pos_x'],
            self.current_state['car_pos_y']
        )

        # Расчет расстояний для каждого луча
        for angle in ray_angles:
            adjusted_angle = angle + self.current_state['rotation']
            dist = self._ray_distance(
                start_point,
                adjusted_angle,
                self.barriers + self.custom_rectangles,
                150
            )
            self.ray_distances.append(round(dist))

        self._update_parking_distance()

    def _distance(self, point1: Tuple[float, float],
                  point2: Tuple[float, float]) -> float:
        """
        Расчет расстояния между двумя точками.

        Args:
            point1 (Tuple[float, float]): Первая точка.
            point2 (Tuple[float, float]): Вторая точка.

        Returns:
            float: Расстояние между точками.
        """
        return math.sqrt(
            (point1[0] - point2[0]) ** 2 +
            (point1[1] - point2[1]) ** 2
        )

    def _point_inside_rect(self, point: Tuple[float, float],
                           rect: pygame.Rect) -> bool:
        """
        Проверяет, находится ли точка внутри прямоугольника.

        Args:
            point (Tuple[float, float]): Координаты точки, которые необходимо проверить.
                                         Представляют собой кортеж из двух значений (x, y).
            rect (pygame.Rect): Прямоугольник, в котором проверяется расположение точки.
                                Это объект pygame.Rect, содержащий координаты прямоугольника.

        Returns:
            bool: Возвращает True, если точка находится внутри прямоугольника, и False в противном случае.
        """
        x, y = point
        return (rect.left <= x <= rect.right and
                rect.top <= y <= rect.bottom)

    def _nearest_point_on_rect(self, rect: pygame.Rect,
                               point: Tuple[float, float]) -> Tuple[float, float]:
        """
        Находит ближайшую точку на прямоугольнике от заданной точки.

        Args:
            rect (pygame.Rect): Прямоугольник, от которого ищется ближайшая точка.
                                 Это объект pygame.Rect, содержащий координаты прямоугольника.
            point (Tuple[float, float]): Координаты точки, от которой ищется ближайшая точка на прямоугольнике.
                                         Представляют собой кортеж из двух значений (x, y).

        Returns:
            Tuple[float, float]: Координаты ближайшей точки на прямоугольнике.
                                  Представляет собой кортеж из двух значений (x, y)
        """
        x, y = point
        nearest_x = max(rect.left, min(x, rect.right))
        nearest_y = max(rect.top, min(y, rect.bottom))
        return (nearest_x, nearest_y)

    def _update_parking_distance(self):
        """
        Обновляет расстояние до парковочного места и вычисляет среднее расстояние
        от углов объекта до парковки.

        Функция сначала вычисляет расстояние от центра объекта до ближайшей точки парковки,
        а затем рассчитывает среднее расстояние от каждого из углов объекта до парковки.

        Если объект не имеет корректного прямоугольника для коллизий (None), функция не выполняет вычислений.

        Процесс обновления состоит из двух частей:
        1. Расчет расстояния от центра объекта до ближайшей точки на парковке.
        2. Расчет расстояний от углов объекта до парковки, с последующим вычислением среднего значения.

        Attributes:
            distance_to_parking (float): Расстояние от центра объекта до ближайшей точки на парковке.
            average_distance (float): Среднее расстояние от углов объекта до ближайшей точки на парковке.
        """
        if self.rotated_collision_rect is None:
            return

        # Расчет расстояния от центра до парковки
        rect_center = self.rotated_collision_rect.center
        nearest_point = self._nearest_point_on_rect(
            self.parking_spot, rect_center)
        self.distance_to_parking = self._distance(rect_center, nearest_point)

        # Расчет среднего расстояния от углов до парковки
        corners = [
            (self.rotated_collision_rect.left, self.rotated_collision_rect.top),
            (self.rotated_collision_rect.right, self.rotated_collision_rect.top),
            (self.rotated_collision_rect.right,
             self.rotated_collision_rect.bottom),
            (self.rotated_collision_rect.left, self.rotated_collision_rect.bottom)
        ]
        corner_distances = [
            self._distance(
                corner, self._nearest_point_on_rect(
                    self.parking_spot, corner))
            for corner in corners
        ]
        self.average_distance = sum(corner_distances) / len(corner_distances)

    def get_state(self) -> Dict:
        """
        Получение текущего состояния среды.

        Функция собирает информацию о текущем состоянии машины и окружающей среды,
        включая данные сенсоров, расстояние до парковочного места, состояние коллизий,
        позицию, угол поворота и скорость автомобиля.

        Возвращаемое состояние включает:
        - `sensors`: Дистанции, полученные от сенсоров (например, расстояния до объектов перед машиной).
        - `distance_to_parking`: Среднее расстояние от машины до ближайшего парковочного места.
        - `collision`: Флаг, указывающий, произошло ли столкновение (если количество столкновений больше 0).
        - `position`: Позиция машины в координатах (x, y).
        - `rotation`: Угол поворота автомобиля.
        - `speed`: Текущая скорость машины.

        Returns:
            Dict: Состояние машины и окружающей среды.
        """
        return {
            'sensors': self.ray_distances,
            'distance_to_parking': self.average_distance,
            'collision': self.current_state['collision_counter'] > 0,
            'position': (self.current_state['car_pos_x'],
                         self.current_state['car_pos_y']),
            'rotation': self.current_state['rotation'],
            'speed': self.current_state['car_speed']
        }

    def step(self, action: Dict) -> Tuple[Dict, float, bool, Dict]:
        """
        Выполнение шага в среде.

        Функция принимает действие, выполняет его в среде, обновляет состояние и сенсоры,
        рассчитывает награду, проверяет, завершён ли эпизод, и возвращает обновлённое состояние.

        Аргументы:
            action (Dict): Словарь, содержащий действия для машины.
                - 'engine' (int): Управление двигателем, может быть -1 (задний ход), 0 (стоп), 1 (вперёд).
                - 'wheels' (int): Управление колесами, может быть -1 (поворот влево), 0 (прямо), 1 (поворот вправо).

        Возвращает:
            Tuple[Dict, float, bool, Dict]:
                - Dict: Обновлённое состояние среды (см. метод `get_state`).
                - float: Награда за выполненное действие (рассчитывается методом `_calculate_reward`).
                - bool: Флаг завершения эпизода, True, если эпизод завершён.
                - Dict: Дополнительная информация (пустой словарь по умолчанию).
        """
        if self.episode_finished:
            return self.get_state(), 0, True, {}

        # Применение действия
        self._apply_action(action)
        self.current_step += 1

        # Обновление сенсоров
        self._update_sensors()

        # Получение нового состояния
        new_state = self.get_state()

        # Расчет награды
        reward = self._calculate_reward(new_state)

        # Проверка завершения эпизода
        done = self._check_episode_end(new_state)

        return new_state, reward, done, {}

    def _apply_action(self, action: Dict):
        """
        Применение действия к машине.

        Эта функция принимает действие, управляет скоростью и поворотом машины в зависимости от переданных сигналов,
        а также обновляет её позицию.

        Аргументы:
            action (Dict): Словарь с двумя ключами:
                - 'engine' (int): Сигнал управления двигателем. Может быть:
                    - 1: ускорение,
                    - -1: торможение (задний ход),
                    - 0: отсутствие изменения скорости.
                - 'wheels' (int): Сигнал управления поворотом. Может быть:
                    - 1: поворот вправо,
                    - -1: поворот влево,
                    - 0: прямое движение.

        Обновляет:
            - `car_speed` (float): Скорость машины.
            - `rotation` (float): Угол поворота машины.
            - Позицию машины (обновляется через метод `_update_position`).
        """
        # Получение сигналов управления
        engine_signal = action['engine']
        wheel_signal = action['wheels']

        # Обработка сигнала двигателя
        if engine_signal == 1:
            self.current_state['car_speed'] = min(
                self.current_state['car_speed'] + self.ACCELERATION,
                self.MAX_SPEED
            )
        elif engine_signal == -1:
            self.current_state['car_speed'] = max(
                self.current_state['car_speed'] - self.DECELERATION,
                -self.MAX_SPEED_BACKWARD
            )

        # Обработка сигнала поворота
        if abs(self.current_state['car_speed']) >= self.MIN_TURN_SPEED:
            self.current_state['rotation'] = (
                self.current_state['rotation'] + wheel_signal
            ) % 360

        # Обновление позиции
        self._update_position()

    def _update_position(self):
        """
        Обновление позиции машины.

        Эта функция рассчитывает новую позицию машины на основе её текущей скорости и угла поворота.
        Она также обновляет прямоугольники, отвечающие за коллизию, и проверяет, произошла ли коллизия.
        Если коллизия не обнаружена, обновляются координаты машины.

        Обновляет:
            - `car_pos_x` (float): Новая координата X машины.
            - `car_pos_y` (float): Новая координата Y машины.
            - `car_rect` (pygame.Rect): Обновляется центр прямоугольника машины.
            - `rotated_collision_rect` (pygame.Rect): Обновляется прямоугольник коллизии с учётом поворота.

        Выполняет:
            - Поворот прямоугольника коллизии.
            - Проверку на коллизии с помощью метода `_check_collisions`.
            - Обновление позиции машины, если коллизий не было и скорость не равна нулю.
        """
        # Расчет новой позиции
        new_car_pos_x = (self.current_state['car_pos_x'] +
                         self.current_state['car_speed'] *
                         math.cos(math.radians(self.current_state['rotation'])))
        new_car_pos_y = (self.current_state['car_pos_y'] +
                         self.current_state['car_speed'] *
                         math.sin(math.radians(self.current_state['rotation'])))

        # Обновление rect'ов
        self.car_rect.centerx = int(new_car_pos_x)
        self.car_rect.centery = int(new_car_pos_y)

        # Поворот прямоугольника коллизии
        rotated_rectangle = pygame.transform.rotate(
            self.rectangle_surf,
            -self.current_state['rotation']
        )
        self.rotated_collision_rect = rotated_rectangle.get_rect(
            center=self.car_rect.center
        )

        # Проверка коллизий
        collision_detected = self._check_collisions()

        # Обновление позиции если нет коллизии
        if not collision_detected and self.current_state['car_speed'] != 0:
            self.current_state['car_pos_x'] = new_car_pos_x
            self.current_state['car_pos_y'] = new_car_pos_y

    def _check_collisions(self) -> bool:
        """
        Проверка коллизий с барьерами, пользовательскими препятствиями и границами экрана.

        Эта функция проверяет, сталкивается ли коллизионный прямоугольник машины (с учётом её поворота)
        с любыми барьерами, пользовательскими препятствиями или границами экрана.

        Выполняет:
            - Проверку на коллизии с барьерами, прерывая выполнение при первой коллизии.
            - Проверку на коллизии с пользовательскими препятствиями.
            - Проверку, не выходит ли машина за пределы экрана.
            - Если коллизия обнаружена, останавливает движение машины (устанавливает её скорость в 0).

        Обновляет:
            - `collision_counter` (int): Увеличивает счётчик коллизий, если они были обнаружены.

        Возвращает:
            bool: `True`, если коллизия была обнаружена, иначе `False`.
        """
        collision_detected = False

        # Проверка коллизий с барьерами
        for barrier in self.barriers:
            if self.rotated_collision_rect.colliderect(barrier):
                self.current_state['car_speed'] = 0
                collision_detected = True
                break

        # Проверка коллизий с пользовательскими препятствиями
        for rect in self.custom_rectangles:
            if self.rotated_collision_rect.colliderect(rect):
                self.current_state['car_speed'] = 0
                collision_detected = True
                break

        # Проверка границ экрана
        if (self.rotated_collision_rect.left < 0 or
            self.rotated_collision_rect.right > self.WIDTH or
            self.rotated_collision_rect.top < 0 or
                self.rotated_collision_rect.bottom > self.HEIGHT):
            self.current_state['car_speed'] = 0
            collision_detected = True

        # Обновление счетчика коллизий
        if collision_detected:
            self.current_state['collision_counter'] += 1

        return collision_detected

    def _calculate_reward(self, state: Dict) -> float:
        """
        Вычисление награды за текущий шаг в процессе парковки.

        Функция вычисляет награду в зависимости от различных факторов:
        - Столкновение с барьерами или препятствиями.
        - Приближение к цели (парковочному месту).
        - Успешная парковка.
        - Время, затраченное на движение.

        Штрафы и награды:
            - Если произошло столкновение, начисляется штраф в размере 100.
            - Если машина приближается к парковке, награда пропорциональна уменьшению расстояния до цели.
            - Если парковка выполнена корректно, начисляется награда в 1000.
            - Каждый шаг в игре имеет небольшой штраф за время (0.1).

        Обновления:
            - Обновляется значение `best_distance`, если текущее расстояние до парковки меньше предыдущего.
            - Обновляется общий показатель фитнеса (`current_fitness`), добавляя текущую награду.

        Аргументы:
            state (Dict): Словарь с текущим состоянием машины и окружающей среды, включающий:
                - 'collision' (bool): Столкнулась ли машина с препятствием.
                - 'distance_to_parking' (float): Текущее расстояние до парковки.

        Возвращает:
            float: Награду за текущий шаг.
        """
        reward = 0

        # Штраф за столкновение
        if state['collision']:
            reward -= 100

        # Награда за приближение к цели
        current_distance = state['distance_to_parking']
        if current_distance < self.best_distance:
            reward += (self.best_distance - current_distance) * 10
            self.best_distance = current_distance

        # Награда за успешную парковку
        if self._is_parked_correctly():
            reward += 1000

        # Небольшой штраф за время
        reward -= 0.1

        self.current_fitness += reward
        return reward

    def _is_parked_correctly(self) -> bool:
        """
        Проверка правильности парковки.

        Эта функция проверяет, правильно ли припаркована машина в парковочном месте.
        Для этого проверяются два основных условия:
        - Машина полностью находится внутри парковочного места.
        - Машина правильно ориентирована (в пределах допустимого углового отклонения).

        Условия правильной парковки:
            1. Прямоугольник машины полностью находится внутри парковочного места.
            2. Угол поворота машины находится в пределах допустимого отклонения от целевого угла (по умолчанию целевой угол равен 0 градусам, что соответствует парковке в прямом направлении).

        Аргументы:
            Нет.

        Возвращает:
            bool: `True`, если машина припаркована правильно, иначе `False`.
        """
        if not self.rotated_collision_rect:
            return False

        if self.parking_spot.colliderect(self.rotated_collision_rect):
            # Проверка полного нахождения в парковочном месте
            if (self.rotated_collision_rect.left >= self.parking_spot.left and
                self.rotated_collision_rect.right <= self.parking_spot.right and
                self.rotated_collision_rect.top >= self.parking_spot.top and
                    self.rotated_collision_rect.bottom <= self.parking_spot.bottom):

                # Дополнительная проверка правильности ориентации
                # Допустимое отклонение от правильного угла в градусах
                angle_threshold = 10
                target_angle = 0  # или другой целевой угол парковки
                current_angle = self.current_state['rotation'] % 360

                # Проверка, находится ли текущий угол в пределах допустимого
                # отклонения
                angle_diff = min(
                    abs(current_angle - target_angle),
                    abs(current_angle - (target_angle + 360))
                )

                if angle_diff <= angle_threshold:
                    return True

        return False

    def get_fitness(self) -> float:
        """
        Получение итогового значения фитнеса.

        Эта функция возвращает текущую сумму наград и штрафов, накопленных за все шаги,
        которые были выполнены в процессе выполнения задачи. Значение фитнеса отражает
        эффективность поведения агента в среде.

        Аргументы:
            Нет.

        Возвращает:
            float: Текущее значение фитнеса.
        """
        return self.current_fitness

    def _check_episode_end(self, state: Dict) -> bool:
        """
        Проверка условий завершения эпизода.

        Эта функция проверяет, достигнуты ли условия завершения эпизода, такие как:
        1. Столкновение автомобиля (collision).
        2. Превышение максимального количества шагов эпизода.
        3. Успешная парковка автомобиля.

        Если хотя бы одно из этих условий выполнено, эпизод завершен.

        Аргументы:
            state (Dict): Текущее состояние агента, включая информацию о столкновениях, расстоянии до парковки и другие параметры.

        Возвращает:
            bool: True, если эпизод завершен, иначе False.
        """
        if (state['collision'] or
            self.current_step >= self.max_episode_steps or
                self._is_parked_correctly()):
            self.episode_finished = True
            return True
        return False

    def add_custom_rectangle(self, rect: pygame.Rect):
        """
        Добавление пользовательского препятствия.

        Эта функция добавляет пользовательское прямоугольное препятствие в список препятствий.
        Пользовательские препятствия могут использоваться для проверки коллизий в процессе
        движения автомобиля.

        Аргументы:
            rect (pygame.Rect): Прямоугольник, представляющий новое препятствие. Это должен быть
                                объект типа pygame.Rect, который определяет размеры и позицию препятствия.
        """
        self.custom_rectangles.append(rect)

    def remove_custom_rectangle(self, rect: pygame.Rect):
        """
        Удаление пользовательского препятствия.

        Эта функция удаляет указанное пользовательское препятствие из списка препятствий.
        Если прямоугольник присутствует в списке, он будет удален.

        Аргументы:
            rect (pygame.Rect): Прямоугольник, представляющий препятствие, которое необходимо удалить.
                                Это должен быть объект типа pygame.Rect, который определяет размеры и позицию препятствия.

        Примечания:
            Если переданный прямоугольник отсутствует в списке, операция удаления не выполняется.
        """
        if rect in self.custom_rectangles:
            self.custom_rectangles.remove(rect)

    def get_render_data(self) -> Dict:
        """
        Получение данных для отрисовки.

        Эта функция возвращает словарь с данными, которые могут быть использованы для отрисовки текущего состояния машины
        и окружающей среды. Это включает в себя позицию машины, ее угол поворота, количество столкновений, время,
        данные сенсоров, расстояние до парковки и информацию о парковке.

        Возвращаемое значение:
            Dict: Словарь с данными для отрисовки, включающий:
                - 'car_pos' (tuple): Позиция машины (x, y).
                - 'rotation' (float): Текущий угол поворота машины.
                - 'collision_count' (int): Количество столкновений.
                - 'time' (float): Время, прошедшее с начала эпизода.
                - 'ray_distances' (list): Дистанции, полученные с сенсоров.
                - 'distance_to_parking' (float): Среднее расстояние до парковочного места.
                - 'rectangles' (list): Список пользовательских прямоугольников (препятствий).
                - 'is_parked' (bool): Флаг, указывающий, припаркована ли машина правильно.
        """
        return {
            'car_pos': (self.current_state['car_pos_x'],
                        self.current_state['car_pos_y']),
            'rotation': self.current_state['rotation'],
            'collision_count': self.current_state['collision_counter'],
            'time': self.current_state['time_elapsed'],
            'ray_distances': self.ray_distances,
            'distance_to_parking': self.average_distance,
            'rectangles': self.custom_rectangles,
            'is_parked': self._is_parked_correctly()
        }
