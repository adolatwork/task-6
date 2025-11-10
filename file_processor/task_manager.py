from typing import Dict, Optional, Any
from pathlib import Path
import logging
import uuid
from django.utils import timezone
from .models import TaskLog, TaskProgress, TaskEventLog

logger = logging.getLogger(__name__)


class TaskManagerService:
    def create_task(self, file_path: str, task_type: str, 
                    user_id: Optional[int] = None, 
                    metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Yangi taskni yaratish
        
        Args:
            file_path: Fayl yo'li
            task_type: Task turi (image, video, document)
            user_id: Foydalanuvchi ID
            metadata: Qo'shimcha metadata
        
        Returns:
            Created task ma'lumoti
        """
        try:
            if not Path(file_path).exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            
            file_info = Path(file_path)
            celery_task_id = str(uuid.uuid4())
            
            task = TaskLog.objects.create(
                celery_task_id=celery_task_id,
                task_type=task_type,
                file_name=file_info.name,
                file_size=file_info.stat().st_size,
                file_path=str(file_path),
                status="pending",
                user_id=user_id,
                metadata=metadata or {},
            )
            
            TaskEventLog.objects.create(
                task=task,
                event_type="created",
                message=f"Task created for file: {file_info.name}",
                metadata={"file_path": str(file_path), "task_type": task_type}
            )
            
            task_data = {
                "id": str(task.id),
                "celery_task_id": task.celery_task_id,
                "task_type": task.task_type,
                "file_name": task.file_name,
                "file_size": task.file_size,
                "file_path": task.file_path,
                "status": task.status,
                "user_id": task.user_id,
                "metadata": task.metadata,
                "created_at": task.created_at.isoformat(),
            }
            
            logger.info(f"Task created in database: {task.celery_task_id}")
            return task_data
            
        except Exception as e:
            logger.error(f"Error creating task: {str(e)}")
            raise
    
    def update_progress(self, celery_task_id: str, progress: int, 
                       message: str = "", data: Optional[Dict] = None) -> bool:
        """
        Task progressni yangilash
        
        Args:
            celery_task_id: Celery task ID
            progress: Progress foizi (0-100)
            message: Xabar
            data: Qo'shimcha ma'lumot
        
        Returns:
            Muvaffaqiyat yo'ki yo'q
        """
        try:
            if not 0 <= progress <= 100:
                raise ValueError("Progress must be between 0 and 100")
            
            task = TaskLog.objects.get(celery_task_id=celery_task_id)
            
            if task.status == "pending" and progress > 0:
                task.status = "processing"
                task.started_at = timezone.now()
                TaskEventLog.objects.create(
                    task=task,
                    event_type="started",
                    message="Task processing started",
                    metadata={}
                )
                task.save(update_fields=["progress", "status", "started_at"])
            else:
                task.progress = progress
                task.save(update_fields=["progress"])
            
            TaskProgress.objects.create(
                task=task,
                progress=progress,
                message=message,
                data=data or {}
            )
            
            TaskEventLog.objects.create(
                task=task,
                event_type="progress",
                message=message or f"Progress: {progress}%",
                metadata={"progress": progress, "data": data or {}}
            )
            
            logger.info(f"Progress updated: {celery_task_id} -> {progress}%")
            return True
            
        except TaskLog.DoesNotExist:
            logger.error(f"TaskLog not found for celery_task_id: {celery_task_id}")
            return False
        except Exception as e:
            logger.error(f"Error updating progress: {str(e)}")
            return False
    
    def complete_task(self, celery_task_id: str, result: Dict[str, Any]) -> bool:
        """
        Taskni tugatish
        
        Args:
            celery_task_id: Celery task ID
            result: Qayta ishlash natijalari
        
        Returns:
            Muvaffaqiyat yo'ki yo'q
        """
        try:
            task = TaskLog.objects.get(celery_task_id=celery_task_id)
            task.status = "completed"
            task.progress = 100
            task.result = result
            task.completed_at = timezone.now()
            task.save()
            
            TaskEventLog.objects.create(
                task=task,
                event_type="completed",
                message=f"Task completed successfully",
                metadata=result
            )
            
            logger.info(f"Task completed: {celery_task_id}")
            return True
            
        except TaskLog.DoesNotExist:
            logger.error(f"TaskLog not found for celery_task_id: {celery_task_id}")
            return False
        except Exception as e:
            logger.error(f"Error completing task: {str(e)}")
            return False
    
    def fail_task(self, celery_task_id: str, error_message: str, 
                  error_code: str = None, retry: bool = True) -> bool:
        """
        Taskni muvaffaqiyatsiz qilish
        
        Args:
            celery_task_id: Celery task ID
            error_message: Xato xabari
            error_code: Xato kodi
            retry: Qayta urinish mumkinmi?
        
        Returns:
            Muvaffaqiyat yo'ki yo'q
        """
        try:
            task = TaskLog.objects.get(celery_task_id=celery_task_id)
            
            if retry and task.retry_count < task.max_retries:
                task.status = "retry"
                task.retry_count += 1
            else:
                task.status = "failed"
            
            task.error_message = error_message
            task.error_code = error_code or "UNKNOWN"
            task.save()
            
            TaskEventLog.objects.create(
                task=task,
                event_type="failed",
                message=error_message,
                metadata={"error_code": error_code, "retry_count": task.retry_count}
            )
            
            logger.warning(f"Task failed: {celery_task_id} - {error_message}")
            return True
            
        except TaskLog.DoesNotExist:
            logger.error(f"TaskLog not found for celery_task_id: {celery_task_id}")
            return False
        except Exception as e:
            logger.error(f"Error failing task: {str(e)}")
            return False
    
    def cancel_task(self, celery_task_id: str) -> bool:
        """
        Taskni bekor qilish
        
        Args:
            celery_task_id: Celery task ID
        
        Returns:
            Muvaffaqiyat yo'ki yo'q
        """
        try:
            task = TaskLog.objects.get(celery_task_id=celery_task_id)
            
            if not task.is_cancellable():
                raise ValueError(f"Cannot cancel task with status: {task.status}")
            
            task.status = "cancelled"
            task.cancelled_at = timezone.now()
            task.save()
            
            TaskEventLog.objects.create(
                task=task,
                event_type="cancelled",
                message="Task cancelled by user"
            )
            
            logger.info(f"Task cancelled: {celery_task_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error cancelling task: {str(e)}")
            return False
    
    def retry_task(self, celery_task_id: str) -> bool:
        """
        Taskni qayta urinish
        
        Args:
            celery_task_id: Celery task ID
        
        Returns:
            Muvaffaqiyat yo'ki yo'q
        """
        try:
            task = TaskLog.objects.get(celery_task_id=celery_task_id)
            
            if not task.is_retryable():
                raise ValueError(f"Cannot retry task - max retries exceeded")
            
            task.status = "retry"
            task.retry_count += 1
            task.error_message = ""
            task.save()
            
            TaskEventLog.objects.create(
                task=task,
                event_type="retried",
                message=f"Retry attempt #{task.retry_count}"
            )
            
            logger.info(f"Task retry: {celery_task_id} - Attempt #{task.retry_count}")
            return True
            
        except Exception as e:
            logger.error(f"Error retrying task: {str(e)}")
            return False
    
    def get_task_status(self, celery_task_id: str) -> Optional[Dict[str, Any]]:
        """
        Task holati olish
        
        Args:
            celery_task_id: Celery task ID
        
        Returns:
            Task ma'lumoti yoki None
        """
        try:
            task = TaskLog.objects.get(celery_task_id=celery_task_id)
            
            return {
                "id": str(task.id),
                "celery_task_id": task.celery_task_id,
                "status": task.status,
                "progress": task.progress,
                "file_name": task.file_name,
                "file_size": task.file_size,
                "created_at": task.created_at.isoformat(),
                "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                "error_message": task.error_message,
                "retry_count": task.retry_count,
            }
            
        except Exception as e:
            logger.error(f"Error getting task status: {str(e)}")
            return None
    
    def get_user_tasks(self, user_id: int, status: Optional[str] = None) -> list:
        """
        Foydalanuvchi tasklariga o'qish
        
        Args:
            user_id: Foydalanuvchi ID
            status: Holat filteri (optional)
        
        Returns:
            Task list
        """
        try:
            query = TaskLog.objects.filter(user_id=user_id)
            if status:
                query = query.filter(status=status)
            return list(query.values())
            
        except Exception as e:
            logger.error(f"Error getting user tasks: {str(e)}")
            return []
