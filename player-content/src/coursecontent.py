import json
from random import randint


class _CourseContent:
    _instance = None

    def __new__(cls):
        if not cls._instance:
            cls._instance = super().__new__(cls)

        return cls._instance

    def __init__(self):
        self.f = open("course-content.json", mode="r")
        self.content = json.load(self.f)

    def fetchcontent(self, module: str, level: int) -> dict:
        #_module = module.lower()

       # if _module not in self.content:
        #    raise Exception(f"module '{module}' is not in questions bank")
        coursedict = []

        for i in self.content['courses']:
            if i['level'] == level:
                coursedict.append(i)

        for a in coursedict:
            found = [c for c in a['content'] if c["id"] == module]
            return found[0]



