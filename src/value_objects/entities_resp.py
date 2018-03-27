from src.value_objects.jsonable import Jsonable


class EntitiesResp(Jsonable):
    status = None
    entities = None

    def __init__(self, status, entities=None):
        Jsonable.__init__(self)
        self.status = status
        self.entities = entities

    def to_json(self):
        if not self.entities:
            return self.dump_json({'status': self.status.to_dict()})

        return self.dump_json({'entities': self.entities, 'status': self.status.to_dict()})
