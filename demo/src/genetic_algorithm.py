import random
import math
from typing import List, Tuple, Callable
import numpy as np

class GeneticAlgorithm:
    def __init__(self, 
                 population_size: int = 100,
                 genome_length: int = 180,
                 mutation_rate: float = 0.01,
                 elite_size: int = 10,
                 tournament_size: int = 5):
        """
        Инициализация генетического алгоритма
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
        """Создание начальной популяции"""
        return [
            [random.randint(0, 1) for _ in range(self.genome_length)]
            for _ in range(self.population_size)
        ]

    def _select_parent(self, fitness_scores: List[float]) -> List[int]:
        """Выбор родителя через турнирный отбор"""
        tournament = random.sample(list(enumerate(fitness_scores)), self.tournament_size)
        winner_idx = max(tournament, key=lambda x: x[1])[0]
        return self.population[winner_idx]

    def _crossover(self, parent1: List[int], parent2: List[int]) -> Tuple[List[int], List[int]]:
        """
        Скрещивание двух родителей
        Использует двухточечный кроссовер
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
        """Мутация генома"""
        mutated = genome.copy()
        for i in range(len(mutated)):
            if random.random() < self.mutation_rate:
                mutated[i] = 1 - mutated[i]  # Инверсия бита
                # Добавляем шанс мутации соседних генов
                if i > 0 and random.random() < 0.3:
                    mutated[i-1] = 1 - mutated[i-1]
                if i < len(mutated)-1 and random.random() < 0.3:
                    mutated[i+1] = 1 - mutated[i+1]
        return mutated

    def evolve(self, fitness_scores: List[float]) -> Tuple[List[List[int]], int]:
        """Эволюция популяции"""
        # Нормализация фитнес-скоров
        min_fitness = min(fitness_scores)
        max_fitness = max(fitness_scores)
    
        if max_fitness != min_fitness:
            normalized_fitness = [(f - min_fitness) / (max_fitness - min_fitness) for f in fitness_scores]
        else:
            normalized_fitness = [1.0/len(fitness_scores)] * len(fitness_scores)

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
        """Получение лучшего генома"""
        return self.best_genome

    def get_population(self) -> List[List[int]]:
        """Получение текущей популяции"""
        return self.population

    def get_generation(self) -> int:
        """Получение номера текущего поколения"""
        return self.generation

    def get_stats(self) -> dict:
        """Получение статистики"""
        return {
            'generation': self.generation,
            'best_fitness': self.best_fitness,
            'population_size': self.population_size,
            'mutation_rate': self.mutation_rate,
            'elite_size': self.elite_size
        }