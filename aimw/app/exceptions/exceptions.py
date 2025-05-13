class BaseException(Exception):
    def __init__(self, name: str):
        self.name = name


class ConfigException(BaseException):
    pass


class EmptyConfigException(BaseException):
    def __init__(self, param_name: str,
                 message: str = "parameter is not defined."):
        self.param_name = param_name
        self.message = message
        super().__init__(message)

    def __str__(self):
        return f"'{self.param_name}' {self.message}"


class ValueConfigException(BaseException):
    def __init__(self, param_name: str,
                 message: str = "parameter is not defined."):
        self.param_name = param_name
        self.message = message
        super().__init__(message)

    def __str__(self):
        return f"'{self.param_name}' {self.message}"
