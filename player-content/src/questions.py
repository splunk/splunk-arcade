import json
from random import randint


class _Questions:
    _instance = None

    def __new__(cls):
        if not cls._instance:
            cls._instance = super().__new__(cls)

        return cls._instance

    def __init__(self):
        self.f = open("questions.json", mode="r")
        self.content = json.load(self.f)

    def random_question_for_module(self, module: str, seen_questions: [str]) -> dict:
        _module = module.lower()

        if _module not in self.content:
            raise Exception(f"module '{module}' is not in questions bank")

        if len(seen_questions) == len(self.content[_module]):
            return {}

        while True:
            maybe_question = self.content[_module][randint(0, len(self.content[_module]) - 1)]
            if maybe_question not in seen_questions:
                return maybe_question
