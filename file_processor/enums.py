from enum import Enum


class TaskStatus(str, Enum):
    """Task holati enumaratsiyasi"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRY = "retry"


class TaskType(str, Enum):
    """Qo'llab-quvatlanadigan fayl turlari"""
    IMAGE = "image"
    VIDEO = "video"
    DOCUMENT = "document"
    ARCHIVE = "archive"


class ProcessorPriority(int, Enum):
    """Processor prioriteti"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3


MAX_RETRIES = 3
TASK_TIMEOUT = 3600  # 1 soat
CHUNK_SIZE = 1024 * 1024  # 1MB


class ErrorCode(str, Enum):
    """Xatolar klassifikatsiyasi"""
    FILE_NOT_FOUND = "FILE_NOT_FOUND"
    INVALID_FORMAT = "INVALID_FORMAT"
    PROCESSING_ERROR = "PROCESSING_ERROR"
    TIMEOUT = "TIMEOUT"
    STORAGE_ERROR = "STORAGE_ERROR"
    PERMISSION_DENIED = "PERMISSION_DENIED"