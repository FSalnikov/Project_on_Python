import pygame
import math
from typing import Dict, Tuple, List, Optional

class Environment:
    def __init__(self):
        """Инициализация среды"""
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
        """Создание барьеров по периметру окна"""
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
        """Сброс среды в начальное состояние"""
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
        """Расчет расстояния луча до препятствия"""
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
        """Обновление показаний сенсоров"""
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
        """Расчет расстояния между двумя точками"""
        return math.sqrt(
            (point1[0] - point2[0]) ** 2 +
            (point1[1] - point2[1]) ** 2
        )

    def _point_inside_rect(self, point: Tuple[float, float],
                          rect: pygame.Rect) -> bool:
        """Проверка находится ли точка внутри прямоугольника"""
        x, y = point
        return (rect.left <= x <= rect.right and
                rect.top <= y <= rect.bottom)

    def _nearest_point_on_rect(self, rect: pygame.Rect,
                              point: Tuple[float, float]) -> Tuple[float, float]:
        """Поиск ближайшей точки на прямоугольнике"""
        x, y = point
        nearest_x = max(rect.left, min(x, rect.right))
        nearest_y = max(rect.top, min(y, rect.bottom))
        return (nearest_x, nearest_y)
    



    def _update_parking_distance(self):
        """Обновление расстояния до парковочного места"""
        if self.rotated_collision_rect is None:
            return
            
        # Расчет расстояния от центра до парковки
        rect_center = self.rotated_collision_rect.center
        nearest_point = self._nearest_point_on_rect(self.parking_spot, rect_center)
        self.distance_to_parking = self._distance(rect_center, nearest_point)

        # Расчет среднего расстояния от углов до парковки
        corners = [
            (self.rotated_collision_rect.left, self.rotated_collision_rect.top),
            (self.rotated_collision_rect.right, self.rotated_collision_rect.top),
            (self.rotated_collision_rect.right, self.rotated_collision_rect.bottom),
            (self.rotated_collision_rect.left, self.rotated_collision_rect.bottom)
        ]
        corner_distances = [
            self._distance(corner, self._nearest_point_on_rect(self.parking_spot, corner))
            for corner in corners
        ]
        self.average_distance = sum(corner_distances) / len(corner_distances)

    def get_state(self) -> Dict:
        """Получение текущего состояния среды"""
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
        Выполнение шага в среде
        Args:
            action: словарь с ключами 'engine' и 'wheels',
                   значения: -1, 0, или 1
        Returns:
            состояние, награда, флаг завершения, доп. информация
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
        """Применение действия к машине"""
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
        """Обновление позиции машины"""
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
        """Проверка коллизий"""
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
        """Вычисление награды за текущий шаг"""
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
        """Проверка правильности парковки"""
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
                
                # Проверка, находится ли текущий угол в пределах допустимого отклонения
                angle_diff = min(
                    abs(current_angle - target_angle),
                    abs(current_angle - (target_angle + 360))
                )
                
                if angle_diff <= angle_threshold:
                    return True
        
        return False

    def get_fitness(self) -> float:
        """Получение итогового значения фитнеса"""
        return self.current_fitness

    def _check_episode_end(self, state: Dict) -> bool:
        """Проверка условий завершения эпизода"""
        if (state['collision'] or 
            self.current_step >= self.max_episode_steps or 
            self._is_parked_correctly()):
            self.episode_finished = True
            return True
        return False

    def add_custom_rectangle(self, rect: pygame.Rect):
        """Добавление пользовательского препятствия"""
        self.custom_rectangles.append(rect)

    def remove_custom_rectangle(self, rect: pygame.Rect):
        """Удаление пользовательского препятствия"""
        if rect in self.custom_rectangles:
            self.custom_rectangles.remove(rect)

    def get_render_data(self) -> Dict:
        """Получение данных для отрисовки"""
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