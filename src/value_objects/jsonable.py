import abc
import json


class Jsonable():
    def __init__(self):
        pass

    @abc.abstractmethod
    def to_json(self):
        pass

    def dump_json(self, dict):
        return json.dumps(dict)
