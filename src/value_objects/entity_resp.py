from src.value_objects.jsonable import Jsonable


class EntityResp(Jsonable):
    status = None
    entity = None

    def __init__(self, status, entity=None):
        Jsonable.__init__(self)
        self.status = status
        self.entity = entity

    def to_json(self):
        if not self.entity:
            return self.dump_json({'status': self.status.to_dict()})

        return self.dump_json({'entity': self.entity, 'status': self.status.to_dict()})
