from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Q
import logging
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes

from .serializers import (
    TaskDetailSerializer,
    TaskListSerializer,
    CreateTaskSerializer,
    CancelTaskSerializer,
    RetryTaskSerializer,
    BulkCreateTaskSerializer,
)
from .celery_tasks import process_file, process_bulk_files
from .task_manager import TaskManagerService
from .models import TaskLog

logger = logging.getLogger(__name__)
task_manager = TaskManagerService()


@extend_schema_view(
    list=extend_schema(
        summary="List all tasks",
        description="Retrieve a paginated list of tasks with optional filtering by status, task_type, date range, and search.",
        tags=["Tasks"],
        parameters=[
            OpenApiParameter(
                name='status',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Filter by task status',
                enum=['pending', 'processing', 'completed', 'failed', 'cancelled', 'retry'],
            ),
            OpenApiParameter(
                name='task_type',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Filter by task type',
                enum=['image', 'video', 'document'],
            ),
            OpenApiParameter(
                name='from_date',
                type=OpenApiTypes.DATETIME,
                location=OpenApiParameter.QUERY,
                description='Filter tasks created from this date (ISO format)',
            ),
            OpenApiParameter(
                name='to_date',
                type=OpenApiTypes.DATETIME,
                location=OpenApiParameter.QUERY,
                description='Filter tasks created until this date (ISO format)',
            ),
            OpenApiParameter(
                name='search',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Search by file name or task ID',
            ),
        ],
    ),
    retrieve=extend_schema(
        summary="Retrieve a task",
        description="Get detailed information about a specific task including progress history and event logs.",
        tags=["Tasks"],
    ),
)
class TaskViewSet(viewsets.ModelViewSet):
    """
    Task API ViewSet - CRUD va dopolnitel'nye operatsii
    Dependency Injection pattern - services to'g'ri inject qilinadi
    """
    
    serializer_class = TaskDetailSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """
        Foydalanuvchining tasklarini olish
        Filtering by status, task_type, date range
        """
        queryset = TaskLog.objects.filter(user_id=self.request.user.id)
        
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
        
        task_type = self.request.query_params.get('task_type')
        if task_type:
            queryset = queryset.filter(task_type=task_type)
        
        from_date = self.request.query_params.get('from_date')
        to_date = self.request.query_params.get('to_date')
        
        if from_date:
            queryset = queryset.filter(created_at__gte=from_date)
        if to_date:
            queryset = queryset.filter(created_at__lte=to_date)
        
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(file_name__icontains=search) |
                Q(celery_task_id__icontains=search)
            )
        
        return queryset.order_by('-created_at')
    
    def list(self, request, *args, **kwargs):
        """
        Tasklarni ro'yxatini olish
        
        Query parameters:
            - status: pending, processing, completed, failed, cancelled
            - task_type: image, video, document
            - from_date: Start date (ISO format)
            - to_date: End date (ISO format)
            - search: Search by file name or task ID
            - page: Page number
            - page_size: Items per page
        """
        queryset = self.filter_queryset(self.get_queryset())
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = TaskListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = TaskListSerializer(queryset, many=True)
        return Response(serializer.data)
    
    def retrieve(self, request, pk=None):
        """
        Alohida task ma'lumoti olish
        
        Include:
            - Progress history
            - Event logs
        """
        task = get_object_or_404(TaskLog, pk=pk, user_id=request.user.id)
        serializer = TaskDetailSerializer(task)
        return Response(serializer.data)
    
    @extend_schema(
        summary="Create a new task",
        description="Create a new file processing task. The task will be queued for asynchronous processing.",
        request=CreateTaskSerializer,
        responses={
            201: TaskDetailSerializer,
            400: OpenApiTypes.OBJECT,
            500: OpenApiTypes.OBJECT,
        },
        examples=[
            OpenApiExample(
                'Create image task',
                value={
                    "file_path": "/path/to/image.jpg",
                    "task_type": "image",
                    "metadata": {"quality": "high", "format": "jpeg"}
                },
                request_only=True,
            ),
        ],
        tags=["Tasks"],
    )
    @action(detail=False, methods=['post'])
    def create_task(self, request):
        """
        Yangi task yaratish
        
        POST /api/tasks/create_task/
        {
            "file_path": "/path/to/file.jpg",
            "task_type": "image",
            "metadata": {}
        }
        """
        serializer = CreateTaskSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            task_data = task_manager.create_task(
                file_path=serializer.validated_data['file_path'],
                task_type=serializer.validated_data['task_type'],
                user_id=request.user.id,
                metadata=serializer.validated_data.get('metadata', {})
            )
            
            process_file.delay(
                celery_task_id=task_data['celery_task_id'],
                file_path=task_data['file_path'],
                task_type=task_data['task_type']
            )
            
            return Response(
                task_data,
                status=status.HTTP_201_CREATED
            )
        
        except Exception as e:
            logger.error(f"Error creating task: {str(e)}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary="Cancel a task",
        description="Cancel a running or pending task. Only tasks with status 'pending', 'processing', or 'retry' can be cancelled.",
        request=CancelTaskSerializer,
        responses={
            200: OpenApiTypes.OBJECT,
            400: OpenApiTypes.OBJECT,
            500: OpenApiTypes.OBJECT,
        },
        examples=[
            OpenApiExample(
                'Cancel task',
                value={"reason": "User requested cancellation"},
                request_only=True,
            ),
            OpenApiExample(
                'Success response',
                value={"status": "cancelled"},
                response_only=True,
            ),
        ],
        tags=["Tasks"],
    )
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        Taskni bekor qilish
        
        POST /api/tasks/{id}/cancel/
        """
        task = get_object_or_404(TaskLog, pk=pk, user_id=request.user.id)
        serializer = CancelTaskSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        if not task.is_cancellable():
            return Response(
                {"error": f"Cannot cancel task with status: {task.status}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from celery.app import current_app
            current_app.control.revoke(task.celery_task_id, terminate=True)
            
            task_manager.cancel_task(task.celery_task_id)
            
            return Response(
                {"status": "cancelled"},
                status=status.HTTP_200_OK
            )
        
        except Exception as e:
            logger.error(f"Error cancelling task: {str(e)}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary="Retry a failed task",
        description="Retry a failed task. Use 'force=True' to retry even if max retries have been exceeded.",
        request=RetryTaskSerializer,
        responses={
            200: OpenApiTypes.OBJECT,
            400: OpenApiTypes.OBJECT,
            500: OpenApiTypes.OBJECT,
        },
        examples=[
            OpenApiExample(
                'Retry task',
                value={"force": False},
                request_only=True,
            ),
            OpenApiExample(
                'Success response',
                value={"status": "retrying"},
                response_only=True,
            ),
        ],
        tags=["Tasks"],
    )
    @action(detail=True, methods=['post'])
    def retry(self, request, pk=None):
        """
        Taskni qayta urinish
        
        POST /api/tasks/{id}/retry/
        """
        task = get_object_or_404(TaskLog, pk=pk, user_id=request.user.id)
        serializer = RetryTaskSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        force = serializer.validated_data.get('force', False)
        
        if not force and not task.is_retryable():
            return Response(
                {"error": "Cannot retry task - max retries exceeded"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            task_manager.retry_task(task.celery_task_id)
            
            process_file.delay(
                celery_task_id=task.celery_task_id,
                file_path=task.file_path,
                task_type=task.task_type
            )
            
            return Response(
                {"status": "retrying"},
                status=status.HTTP_200_OK
            )
        
        except Exception as e:
            logger.error(f"Error retrying task: {str(e)}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary="Get task progress summary",
        description="Get a summary of all tasks grouped by status (pending, processing, completed, failed).",
        responses={
            200: OpenApiTypes.OBJECT,
            500: OpenApiTypes.OBJECT,
        },
        examples=[
            OpenApiExample(
                'Progress summary',
                value={
                    "pending": 5,
                    "processing": 2,
                    "completed": 100,
                    "failed": 3,
                    "total": 110
                },
                response_only=True,
            ),
        ],
        tags=["Tasks"],
    )
    @action(detail=False, methods=['get'])
    def progress(self, request):
        """
        Barcha tasklarning progress summary
        
        GET /api/tasks/progress/
        """
        try:
            pending = TaskLog.objects.filter(
                user_id=request.user.id,
                status="pending"
            ).count()
            
            processing = TaskLog.objects.filter(
                user_id=request.user.id,
                status="processing"
            ).count()
            
            completed = TaskLog.objects.filter(
                user_id=request.user.id,
                status="completed"
            ).count()
            
            failed = TaskLog.objects.filter(
                user_id=request.user.id,
                status="failed"
            ).count()
            
            return Response({
                "pending": pending,
                "processing": processing,
                "completed": completed,
                "failed": failed,
                "total": pending + processing + completed + failed
            })
        
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary="Create multiple tasks",
        description="Create multiple file processing tasks in bulk. Tasks can be processed in parallel or sequentially.",
        request=BulkCreateTaskSerializer,
        responses={
            201: OpenApiTypes.OBJECT,
            400: OpenApiTypes.OBJECT,
            500: OpenApiTypes.OBJECT,
        },
        examples=[
            OpenApiExample(
                'Bulk create tasks',
                value={
                    "file_paths": ["/path/to/file1.jpg", "/path/to/file2.jpg", "/path/to/file3.jpg"],
                    "task_type": "image",
                    "parallel": True
                },
                request_only=True,
            ),
            OpenApiExample(
                'Success response',
                value={
                    "celery_task_id": "550e8400-e29b-41d4-a716-446655440000",
                    "status": "processing",
                    "files_count": 3
                },
                response_only=True,
            ),
        ],
        tags=["Tasks"],
    )
    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        """
        Ko'p task yaratish
        
        POST /api/tasks/bulk_create/
        {
            "file_paths": ["/path/1", "/path/2"],
            "task_type": "image",
            "parallel": true
        }
        """
        serializer = BulkCreateTaskSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            import uuid
            celery_task_id = str(uuid.uuid4())
            
            process_bulk_files.delay(
                celery_task_id=celery_task_id,
                file_paths=serializer.validated_data['file_paths'],
                task_type=serializer.validated_data['task_type']
            )
            
            return Response(
                {
                    "celery_task_id": celery_task_id,
                    "status": "processing",
                    "files_count": len(serializer.validated_data['file_paths'])
                },
                status=status.HTTP_201_CREATED
            )
        
        except Exception as e:
            logger.error(f"Error creating bulk tasks: {str(e)}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
