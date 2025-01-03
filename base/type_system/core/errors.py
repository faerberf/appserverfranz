# Custom exception classes.
class ValidationError(Exception):
    def __init__(self, message, error_code=None, field=None, value=None, type_name=None):
        super().__init__(message)
        self.error_code = error_code
        self.field = field
        self.value = value
        self.type_name = type_name

    def __str__(self):
        return f"ValidationError: {self.message} (type: {self.type_name}, field: {self.field}, value: {self.value}, code: {self.error_code})"