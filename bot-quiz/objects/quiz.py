import random

from utils.config import load_csv_question


class Quiz:
    def __init__(self, themes: list[str], number_question: int):
        self.themes = themes
        self.number_question = number_question
        self.questions = []
        self.current = 0

    def init_quiz(self) -> None:
        data = load_csv_question()
        selected = []
        for row in data:
            if row['theme'] in self.themes:
                selected.append(row)

        nb_random = min(self.number_question, len(selected))
        self.questions = random.sample(selected, nb_random)

    def load(self, dict_config: dict) -> None:
        self.themes = dict_config['themes']
        self.questions = dict_config['questions']
        self.current = dict_config['current']

    def save(self) -> dict:
        return {
            'themes': self.themes,
            'questions': self.questions,
            'current': self.current,
        }

    def next_question(self) -> [str, dict]:
        if self.current < len(self.questions) - 1:
            return f"___Question n°{self.current+1}___",  self.questions[self.current]
        elif self.current == len(self.questions) - 1:
            return f"___Dernière question___", self.questions[self.current]
        return "", {}

    def valid_question(self) -> None:
        self.current += 1
