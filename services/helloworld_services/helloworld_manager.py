from models.service_meta_class import MetaService

class SrvHelloWolrd(metaclass=MetaService):
    def __init__(self):
        pass
    def get_content(self):
        return ['Hello Prototype1.', 'Hello Prototype2.', 'Hello Prototype3.']