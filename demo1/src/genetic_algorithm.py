import random
import math
from typing import List, Tuple, Callable
import numpy as np


class GeneticAlgorithm:
    """
        Класс генетического алгоритма для решения задач оптимизации.

        Атрибуты:
            population_size (int): Размер популяции (по умолчанию 100).
            genome_length (int): Длина генома (по умолчанию 180).
            mutation_rate (float): Шанс мутации для каждого гена (по умолчанию 0.01).
            elite_size (int): Количество элитных особей, которые сохраняются без изменений (по умолчанию 10).
            tournament_size (int): Размер турнира для выбора родителей (по умолчанию 5).

        Методы:
            __init__: Инициализация генетического алгоритма.
            _initialize_population: Создание начальной популяции.
            _select_parent: Выбор родителя через турнирный отбор.
            _crossover: Операция скрещивания двух родителей.
            _mutate: Применение мутации к геному.
            evolve: Эволюция популяции на основе фитнес-оценок.
            get_best_genome: Получение лучшего генома.
            get_population: Получение текущей популяции.
            get_generation: Получение номера текущего поколения.
            get_stats: Получение статистики эволюции.
    """

    def __init__(self,
                 population_size: int = 100,
                 genome_length: int = 180,
                 mutation_rate: float = 0.01,
                 elite_size: int = 10,
                 tournament_size: int = 5):
        """
        Инициализация генетического алгоритма.

        Параметры:
            population_size (int): Размер популяции (по умолчанию 100).
            genome_length (int): Длина генома (по умолчанию 180).
            mutation_rate (float): Шанс мутации для каждого гена (по умолчанию 0.01).
            elite_size (int): Количество элитных особей, которые сохраняются без изменений (по умолчанию 10).
            tournament_size (int): Размер турнира для выбора родителей (по умолчанию 5).
        """
        self.population_size = population_size
        self.genome_length = genome_length
        self.mutation_rate = mutation_rate
        self.elite_size = elite_size
        self.tournament_size = tournament_size

        self.population = self._initialize_population()
        self.generation = 0
        self.best_fitness = float('-inf')
        self.best_genome = None

    def _initialize_population(self) -> List[List[int]]:
        """
        Создание начальной популяции.

        Возвращает:
            List[List[int]]: Список геномов, каждый из которых представляет собой список случайных битов.
        """
        return [
            [random.randint(0, 1) for _ in range(self.genome_length)]
            for _ in range(self.population_size)
        ]

    def _select_parent(self, fitness_scores: List[float]) -> List[int]:
        """
        Выбор родителя через турнирный отбор.

        Параметры:
            fitness_scores (List[float]): Список фитнес-оценок текущих особей популяции.

        Возвращает:
            List[int]: Геном выбранного родителя.
        """
        tournament = random.sample(
            list(
                enumerate(fitness_scores)),
            self.tournament_size)
        winner_idx = max(tournament, key=lambda x: x[1])[0]
        return self.population[winner_idx]

    def _crossover(
            self, parent1: List[int], parent2: List[int]) -> Tuple[List[int], List[int]]:
        """
        Скрещивание двух родителей.

        Использует двухточечный кроссовер, чтобы создать два потомка.

        Параметры:
            parent1 (List[int]): Геном первого родителя.
            parent2 (List[int]): Геном второго родителя.

        Возвращает:
            Tuple[List[int], List[int]]: Два генома потомков.
        """
        if len(parent1) != len(parent2):
            raise ValueError("Parents must have same length")

        # Выбор двух точек кроссовера
        point1, point2 = sorted(random.sample(range(len(parent1)), 2))

        # Создание потомков
        child1 = parent1[:point1] + parent2[point1:point2] + parent1[point2:]
        child2 = parent2[:point1] + parent1[point1:point2] + parent2[point2:]

        return child1, child2

    def _mutate(self, genome: List[int]) -> List[int]:
        """
        Мутация генома.

        Этот метод изменяет случайные биты генома с вероятностью `mutation_rate`, а также может мутировать соседние биты.

        Параметры:
            genome (List[int]): Геном, который будет мутировать.

        Возвращает:
            List[int]: Мутированный геном.
        """
        mutated = genome.copy()
        for i in range(len(mutated)):
            if random.random() < self.mutation_rate:
                mutated[i] = 1 - mutated[i]  # Инверсия бита
                # Добавляем шанс мутации соседних генов
                if i > 0 and random.random() < 0.3:
                    mutated[i - 1] = 1 - mutated[i - 1]
                if i < len(mutated) - 1 and random.random() < 0.3:
                    mutated[i + 1] = 1 - mutated[i + 1]
        return mutated

    def evolve(self, fitness_scores: List[float]
               ) -> Tuple[List[List[int]], int]:
        """
        Эволюция популяции.

        Создается новое поколение на основе текущих фитнес-оценок. Элитные особи сохраняются, а остальные проходят через турнирный отбор, скрещивание и мутацию.

        Параметры:
            fitness_scores (List[float]): Список фитнес-оценок текущих особей популяции.

        Возвращает:
            Tuple[List[List[int]], int]: Новое поколение и номер текущего поколения.
        """
        # Нормализация фитнес-скоров
        min_fitness = min(fitness_scores)
        max_fitness = max(fitness_scores)

        if max_fitness != min_fitness:
            normalized_fitness = [
                (f - min_fitness) / (max_fitness - min_fitness) for f in fitness_scores]
        else:
            normalized_fitness = [
                1.0 / len(fitness_scores)] * len(fitness_scores)

        # Создание нового поколения
        new_population = []

        # Сохранение элиты
        elite_indices = sorted(range(len(fitness_scores)),
                               key=lambda i: fitness_scores[i],
                               reverse=True)[:self.elite_size]
        for idx in elite_indices:
            new_population.append(self.population[idx])

        # Создание остального поколения
        while len(new_population) < self.population_size:
            # Выбор родителей с помощью турнирного отбора
            parent1 = self._select_parent(normalized_fitness)
            parent2 = self._select_parent(normalized_fitness)

            # Скрещивание
            child1, child2 = self._crossover(parent1, parent2)

            # Мутация
            child1 = self._mutate(child1)
            if len(new_population) < self.population_size:
                new_population.append(child1)

            if len(new_population) < self.population_size:
                child2 = self._mutate(child2)
                new_population.append(child2)

        self.population = new_population
        self.generation += 1

        return self.population, self.generation

    def get_best_genome(self) -> List[int]:
        """
        Получение лучшего генома.

        Возвращает:
            List[int]: Геном с наивысшей фитнес-оценкой.
        """
        return self.best_genome

    def get_population(self) -> List[List[int]]:
        """
        Получение текущей популяции.

        Возвращает:
            List[List[int]]: Список геномов текущей популяции.
        """
        return self.population

    def get_generation(self) -> int:
        """
        Получение номера текущего поколения.

        Возвращает:
            int: Номер текущего поколения.
        """
        return self.generation

    def get_stats(self) -> dict:
        """
        Получение статистики эволюции.

        Возвращает:
            dict: Словарь с информацией о текущем поколении, лучшем фитнесе и других параметрах.
        """
        return {
            'generation': self.generation,
            'best_fitness': self.best_fitness,
            'population_size': self.population_size,
            'mutation_rate': self.mutation_rate,
            'elite_size': self.elite_size
        }
