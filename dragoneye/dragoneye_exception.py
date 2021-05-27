class DragoneyeException(Exception):
    def __init__(self, message, error: str = None):
        super().__init__(message)
        self.error: str = error
