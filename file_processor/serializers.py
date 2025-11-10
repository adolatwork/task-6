from rest_framework import serializers


class TaskProgressSerializer(serializers.Serializer):
    """
    Task progress ma'lumoti - Read-only serializer
    """
    progress = serializers.IntegerField(min_value=0, max_value=100)
    message = serializers.CharField(required=False, allow_blank=True)
    created_at = serializers.DateTimeField()


class TaskEventLogSerializer(serializers.Serializer):
    """
    Task event log serializer
    """
    event_type = serializers.CharField()
    message = serializers.CharField()
    created_at = serializers.DateTimeField()


class TaskDetailSerializer(serializers.Serializer):
    """
    Detailed task ma'lumoti - API response
    """
    id = serializers.UUIDField()
    celery_task_id = serializers.CharField()
    
    task_type = serializers.CharField()
    status = serializers.CharField()
    
    file_name = serializers.CharField()
    file_size = serializers.IntegerField()
    
    progress = serializers.IntegerField()
    
    result = serializers.JSONField(required=False)
    error_message = serializers.CharField(required=False)
    error_code = serializers.CharField(required=False)
    
    retry_count = serializers.IntegerField()
    max_retries = serializers.IntegerField()
    
    created_at = serializers.DateTimeField()
    started_at = serializers.DateTimeField(required=False, allow_null=True)
    completed_at = serializers.DateTimeField(required=False, allow_null=True)
    cancelled_at = serializers.DateTimeField(required=False, allow_null=True)
    
    user_id = serializers.IntegerField(required=False)
    tags = serializers.ListField(required=False)
    metadata = serializers.JSONField(required=False)
    
    elapsed_time = serializers.SerializerMethodField()
    is_cancellable = serializers.SerializerMethodField()
    is_retryable = serializers.SerializerMethodField()
    
    def get_elapsed_time(self, obj) -> float:
        """O'tgan vaqtni hisoblash"""
        return obj.get_elapsed_time()
    
    def get_is_cancellable(self, obj) -> bool:
        """Bekor qilinishi mumkinmi?"""
        return obj.is_cancellable()
    
    def get_is_retryable(self, obj) -> bool:
        """Qayta urinishi mumkinmi?"""
        return obj.is_retryable()


class TaskListSerializer(serializers.Serializer):
    """
    Task ro'yxati - Summary ma'lumoti
    """
    id = serializers.UUIDField()
    celery_task_id = serializers.CharField()
    task_type = serializers.CharField()
    status = serializers.CharField()
    file_name = serializers.CharField()
    file_size = serializers.IntegerField()
    progress = serializers.IntegerField()
    created_at = serializers.DateTimeField()
    completed_at = serializers.DateTimeField(required=False, allow_null=True)


class CreateTaskSerializer(serializers.Serializer):
    """
    Yangi task yaratish - Input serializer
    """
    file_path = serializers.CharField(
        help_text="Qayta ishlash uchun fayl yo'li"
    )
    task_type = serializers.ChoiceField(
        choices=["image", "video", "document"],
        help_text="Fayl turi"
    )
    metadata = serializers.JSONField(
        required=False,
        default=dict,
        help_text="Qo'shimcha metadata"
    )
    
    def validate_file_path(self, value):
        """Fayl yo'lini validatsiya qilish"""
        from pathlib import Path
        if not Path(value).exists():
            raise serializers.ValidationError("File does not exist")
        return value


class CancelTaskSerializer(serializers.Serializer):
    """
    Task bekor qilish - Input serializer
    """
    reason = serializers.CharField(
        required=False,
        help_text="Bekor qilish sababi"
    )


class RetryTaskSerializer(serializers.Serializer):
    """
    Task qayta urinish - Input serializer
    """
    force = serializers.BooleanField(
        default=False,
        help_text="Zoralicha qayta urinish"
    )


class BulkCreateTaskSerializer(serializers.Serializer):
    """
    Ko'p task yaratish - Input serializer
    """
    file_paths = serializers.ListField(
        child=serializers.CharField(),
        help_text="Fayl yo'llarining ro'yxati"
    )
    task_type = serializers.ChoiceField(
        choices=["image", "video", "document"],
        help_text="Fayl turi"
    )
    parallel = serializers.BooleanField(
        default=True,
        help_text="Parallel qayta ishlash"
    )


class TaskStatsSerializer(serializers.Serializer):
    """
    Task statistikasi - Summary
    """
    total_tasks = serializers.IntegerField()
    pending_tasks = serializers.IntegerField()
    processing_tasks = serializers.IntegerField()
    completed_tasks = serializers.IntegerField()
    failed_tasks = serializers.IntegerField()
    cancelled_tasks = serializers.IntegerField()
    
    average_processing_time = serializers.FloatField()
    success_rate = serializers.FloatField()
