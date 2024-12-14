from src.environment import Environment
from src.genetic_algorithm import GeneticAlgorithm
from src.brain import Brain
from src.game import Game
import os
import json
import pygame


class Trainer:
    """
        Класс для обучения и эволюции агентов с использованием генетического алгоритма.

        Этот класс управляет процессом тренировки нейросетевых агентов в среде для выполнения задачи парковки.
        Он использует генетический алгоритм для эволюции популяции агентов, оценки их фитнеса,
        а также сохранения лучших геномов для дальнейшего использования.

        Атрибуты:
            env (Environment): Среда, в которой обучаются агенты.
            ga (GeneticAlgorithm): Генетический алгоритм, управляющий популяцией агентов.
            best_fitness (float): Лучший фитнес среди агентов на данный момент.
            visualization_frequency (int): Частота визуализации результатов (каждое n-е поколение).
            results_dir (str): Путь к директории для сохранения лучших геномов.

        Методы:
            __init__(self): Инициализация тренера, создание среды и генетического алгоритма, создание директории для сохранения результатов.
            evaluate_genome(self, genome, visualize=False): Оценка фитнеса одного генома. Создает мозг для заданного генома, выполняет его в среде и вычисляет награду.
            save_genome(self, genome, generation, fitness): Сохранение лучшего генома в файл с указанием поколения и его фитнес-оценки.
            train(self, generations=50): Основной цикл обучения, выполняющий тренировки и эволюцию популяции агентов на протяжении указанного числа поколений.

        Исключения:
            ValueError: Если геном не соответствует нужному формату.

        Примечания:
            В процессе обучения тренер оценивает каждый геном в популяции, эволюционирует популяцию,
            сохраняет результаты и выводит статистику о процессе обучения.
    """

    def __init__(self):
        """Инициализация тренера.

                В этом методе создаются:
                - Среда для обучения агентов (Environment).
                - Генетический алгоритм (GeneticAlgorithm).
                - Директория для сохранения результатов (если она не существует).
        """
        self.env = Environment()
        self.ga = GeneticAlgorithm(
            population_size=50,      # Уменьшаем размер популяции
            genome_length=180,
            mutation_rate=0.03,      # Увеличиваем вероятность мутации
            elite_size=5            # Уменьшаем количество элитных особей
        )
        self.best_fitness = float('-inf')
        self.visualization_frequency = 5

        # Создание директории для сохранения результатов
        self.results_dir = "results"
        os.makedirs(self.results_dir, exist_ok=True)

    def evaluate_genome(self, genome, visualize=False):
        """Оценка фитнеса одного генома.

        Этот метод создает мозг, представляющий геном, и выполняет его в среде,
        чтобы вычислить общую награду (fitness). Если параметр visualize установлен в True,
        то процесс будет визуализироваться.

        Args:
            genome (list): Геном, который нужно оценить. Это список значений, представляющий
                нейронные сети, которые будут обучаться.
            visualize (bool): Если True, то процесс будет визуализироваться в реальном времени
                с помощью Pygame.

        Returns:
            float: Итоговая награда (fitness), полученная от взаимодействия с окружением.
                Высокие значения означают более эффективное поведение агента.
        """
        brain = Brain(genome)
        total_reward = 0
        max_steps = 1000

        # Сброс среды
        state = self.env.reset()

        # Инициализация визуализации
        game = None
        if visualize:
            pygame.init()  # Убедимся, что pygame инициализирован
            game = Game(visualization_mode=True)
            game.env = self.env
            clock = pygame.time.Clock()

        for step in range(max_steps):
            # Проверка на коллизию или завершение
            if state['collision'] or self.env.episode_finished:
                break

            # Получение действия от мозга
            action = brain.make_decision(state['sensors'])

            # Выполнение действия в среде
            next_state, reward, done, _ = self.env.step(action)

            total_reward += reward
            state = next_state

            if visualize:
                # Обработка событий pygame
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        return total_reward

                # Обновление экрана
                game.screen.fill((255, 255, 255))  # Очистка экрана
                game.draw()
                pygame.display.flip()
                clock.tick(60)

                if done:
                    break

        # Очистка после завершения оценки
        if visualize:
            # Показываем результат на короткое время
            pygame.time.wait(100)
            pygame.display.flip()

        # Принудительный сброс среды
        self.env.reset()

        return total_reward

    def save_genome(self, genome, generation, fitness):
        """Сохранение генома в файл.

        Этот метод сохраняет лучший геном на каждом поколении в текстовый файл с именем,
        который включает в себя номер поколения и его фитнес-оценку.

        Args:
            genome (list): Геном, который нужно сохранить в файл.
            generation (int): Номер текущего поколения.
            fitness (float): Фитнес-оценка данного генома.
        """
        filename = f"{self.results_dir}/genome_gen_{generation}_fit_{fitness:.2f}.txt"
        with open(filename, 'w') as f:
            f.write(','.join(map(str, genome)))

    def train(self, generations=50):
        """Основной цикл обучения, выполняющий тренировки и эволюцию популяции.

        Этот метод отвечает за тренировку агентов в течение указанного числа поколений.
        В каждом поколении:
        - Каждый геном оценивается на основе своего поведения в среде.
        - Обновляется лучшая фитнес-оценка.
        - Популяция эволюционирует с использованием результатов оценки.

        Args:
            generations (int): Количество поколений для тренировки. По умолчанию 50.
        """
        print("Starting training...")
        best_fitness_overall = float('-inf')

        for generation in range(generations):
            print(f"\nGeneration {generation + 1}/{generations}")

            fitness_scores = []
            best_fitness_current = float('-inf')

            # Оценка каждого генома в популяции
            for i, genome in enumerate(self.ga.get_population()):
                # Очистка консоли и вывод прогресса
                print(
                    f"\rEvaluating genome {i + 1}/{len(self.ga.get_population())}", end="")

                # Визуализируем только лучшую особь предыдущего поколения
                visualize = (i == 0 and generation > 0)

                # Оценка генома
                fitness = self.evaluate_genome(genome, visualize)
                fitness_scores.append(fitness)

                # Обновление лучшего результата
                if fitness > best_fitness_current:
                    best_fitness_current = fitness

                # Принудительная очистка памяти pygame
                if visualize:
                    pygame.quit()
                    pygame.init()

            # Обновление лучшего результата за все время
            if best_fitness_current > best_fitness_overall:
                best_fitness_overall = best_fitness_current
                # Сохранение лучшего генома
                best_genome = self.ga.get_population()[
                    fitness_scores.index(best_fitness_current)]
                self.save_genome(
                    best_genome,
                    generation + 1,
                    best_fitness_current)

            # Вывод статистики
            avg_fitness = sum(fitness_scores) / len(fitness_scores)
            print(f"\nGeneration {generation + 1} stats:")
            print(f"Best Fitness: {best_fitness_current:.2f}")
            print(f"Average Fitness: {avg_fitness:.2f}")
            print(f"Best Overall Fitness: {best_fitness_overall:.2f}")

            # Эволюция популяции
            self.ga.evolve(fitness_scores)

            # Небольшая пауза между поколениями
            pygame.time.wait(100)


if __name__ == "__main__":
    trainer = Trainer()
    trainer.train(generations=50)  # Запуск обучения на 50 поколений
