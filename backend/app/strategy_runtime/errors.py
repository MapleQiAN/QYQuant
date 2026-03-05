class StrategyRuntimeError(Exception):
    def __init__(self, message, details=None):
        super().__init__(message)
        self.message = message
        self.details = details


def as_response(error):
    return {"code": 40000, "message": error.message, "details": error.details}

