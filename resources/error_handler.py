class APIException(Exception):
    def __init__(self, status_code: int, error_msg: str):
        self.status_code = status_code
        self.content = {
            "code": self.status_code,
            "error_msg": error_msg,
            "result": "",
        }
