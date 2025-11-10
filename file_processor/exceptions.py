class TaskException(Exception):
    """Asosiy task istisnosi"""
    def __init__(self, message: str, error_code: str = None, details: dict = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class FileNotFoundError(TaskException):
    """Fayl topilmadi"""
    pass


class InvalidFormatError(TaskException):
    """Noto'g'ri fayl formati"""
    pass


class ProcessingError(TaskException):
    """Qayta ishlashda xato"""
    pass


class StorageError(TaskException):
    """Saqlashda xato"""
    pass


class PermissionError(TaskException):
    """Ruxsat yo'q"""
    pass


class TimeoutError(TaskException):
    """Vaqt tugadi"""
    pass


class TaskCancelledError(TaskException):
    """Task bekor qilindi"""
    pass


class RetryableError(TaskException):
    """Qayta urinish mumkin bo'lgan xato"""
    pass
