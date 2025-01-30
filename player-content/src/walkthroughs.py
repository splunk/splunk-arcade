import json


class _Walkthroughs:
    _instance = None

    def __new__(cls):
        if not cls._instance:
            cls._instance = super().__new__(cls)

        return cls._instance

    def __init__(self):
        self.f = open("walkthroughs.json", mode="r")
        self.content = json.load(self.f)

    def get_module_stage(self, module: str, stage: int) -> dict:
        _module = module.lower()

        if _module not in self.content:
            raise Exception(f"module '{module}' is not in walkthroughs bank")

        return self.content[_module][stage]
