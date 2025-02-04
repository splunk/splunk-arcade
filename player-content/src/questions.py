import json
import os
from random import choice, randint, random

from redis import StrictRedis


class _Questions:
    _instance = None

    def __new__(cls):
        if not cls._instance:
            cls._instance = super().__new__(cls)

        return cls._instance

    def __init__(self):
        self.f = open("questions.json", mode="r")
        self.content = json.load(self.f)
        self.redis = StrictRedis(
            host=os.getenv("REDIS_HOST", "cache"),
            port=6379,
            db=0,
            decode_responses=True,
        )

    def _get_random_generated_question_for_module(
        self,
        module: str,
        player_name: str,
    ) -> dict|None:
        key_namespace = f"content:quiz:{module}:{player_name}:*"

        found_keys = self.redis.keys(pattern=key_namespace)
        if not found_keys:
            return None

        random_key = choice(found_keys)

        loaded_content = self.redis.hgetall(random_key)
        loaded_content["choices"] = json.loads(loaded_content["choices"])

        return loaded_content


    def random_question_for_module(
        self, module: str, seen_questions: [str], player_name: str
    ) -> dict:
        _module = module.lower()

        if _module not in self.content:
            # in the future we may need/want to check dynamic questions as we may not even have
            # "static" questions, but for now this is a safe check to ensure we dont try to load
            # a question for some module (game) that doesnt exist
            raise Exception(f"module '{module}' is not in questions bank")

        if len(seen_questions) == len(self.content[_module]):
            return {}

        while True:
            if random() < 0.1:
                # for now, 10% of the time we'll try to use a ai gen question
                maybe_question = self._get_random_generated_question_for_module(
                    module=_module,
                    player_name=player_name,
                )
            else:
                maybe_question = self.content[_module][randint(0, len(self.content[_module]) - 1)]

            if maybe_question and maybe_question["question"] not in seen_questions:
                if "link" in maybe_question:
                    maybe_question["link"] = maybe_question["link"].replace(
                        "__PLAYER_NAME__", player_name
                    )

                return maybe_question
