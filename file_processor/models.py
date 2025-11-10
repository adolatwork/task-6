from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid


class TaskLog(models.Model):
    """
    Asosiy task model - barcha background tasklarni kuzatish
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    celery_task_id = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
        help_text="Celery task ID"
    )
    
    task_type = models.CharField(max_length=50, db_index=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ("pending", "Pending"),
            ("processing", "Processing"),
            ("completed", "Completed"),
            ("failed", "Failed"),
            ("cancelled", "Cancelled"),
            ("retry", "Retry"),
        ],
        default="pending",
        db_index=True
    )
    
    file_name = models.CharField(max_length=500)
    file_size = models.BigIntegerField(default=0, validators=[MinValueValidator(0)])
    file_path = models.TextField()
    
    progress = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Progress percentage 0-100"
    )
    
    result = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)
    error_code = models.CharField(max_length=50, blank=True)
    
    retry_count = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    max_retries = models.IntegerField(default=3, validators=[MinValueValidator(0)])
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    
    user_id = models.IntegerField(null=True, blank=True)
    tags = models.JSONField(default=list, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "-created_at"]),
            models.Index(fields=["user_id", "status"]),
            models.Index(fields=["celery_task_id"]),
        ]
    
    def __str__(self):
        return f"{self.file_name} - {self.status}"
    
    def get_elapsed_time(self):
        """O'tgan vaqtni hisoblash"""
        if self.completed_at:
            end_time = self.completed_at
        else:
            end_time = timezone.now()
        
        if self.started_at:
            return (end_time - self.started_at).total_seconds()
        return None
    
    def is_cancellable(self):
        """Task bekor qilinishi mumkinmi?"""
        return self.status in ["pending", "processing", "retry"]
    
    def is_retryable(self):
        """Qayta urinish mumkin bo'lmadimi?"""
        return (
            self.status in ["failed", "retry"] and
            self.retry_count < self.max_retries
        )


class TaskProgress(models.Model):
    """
    Task progress history - har bir o'zgarishni kuzatish
    """
    id = models.BigAutoField(primary_key=True)
    task = models.ForeignKey(TaskLog, on_delete=models.CASCADE, related_name="progress_history")
    
    progress = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    message = models.TextField(blank=True)
    data = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["task", "created_at"]),
        ]
    
    def __str__(self):
        return f"{self.task.file_name} - {self.progress}%"


class TaskEventLog(models.Model):
    """
    Task event logging - audit trail
    """
    id = models.BigAutoField(primary_key=True)
    task = models.ForeignKey(TaskLog, on_delete=models.CASCADE, related_name="events")
    
    EVENT_TYPES = [
        ("created", "Created"),
        ("started", "Started"),
        ("progress", "Progress"),
        ("paused", "Paused"),
        ("resumed", "Resumed"),
        ("completed", "Completed"),
        ("failed", "Failed"),
        ("cancelled", "Cancelled"),
        ("retried", "Retried"),
    ]
    
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    message = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["task", "event_type"]),
        ]
