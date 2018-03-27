from src.value_objects.jsonable import Jsonable


class Status(Jsonable):
    def __init__(self, success, content):
        Jsonable.__init__(self)
        self.success = success
        self.content = content

    def to_dict(self):
        return {'success': self.success, 'content': self.content}

    def to_json(self):
        return self.dump_json({'status': self.to_dict()})
