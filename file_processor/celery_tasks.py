from celery import shared_task, Task
from celery.utils.log import get_task_logger

from .processor_factory import ProcessorRegistry, ProcessorFactory
from .task_manager import TaskManagerService

logger = get_task_logger(__name__)
task_manager = TaskManagerService()


class BaseTask(Task):
    """
    Base Celery task - Error handling va retry logic
    """
    
    autoretry_for = (Exception,)
    max_retries = 3
    default_retry_delay = 60
    
    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Qayta urinish bo'lganda"""
        logger.warning(f"Task retry: {task_id} - {str(exc)}")
        task_manager.update_progress(task_id, -1, f"Retrying: {str(exc)}")
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Muvaffaqiyatsiz bo'lganda"""
        logger.error(f"Task failed: {task_id} - {str(exc)}")
        task_manager.fail_task(task_id, str(exc), error_code="CELERY_ERROR")
    
    def on_success(self, result, task_id, args, kwargs):
        """Muvaffaqiyatli bo'lganda"""
        logger.info(f"Task completed: {task_id}")


class FileProcessingTask(BaseTask):
    """
    Fayl qayta ishlash task - Single Responsibility Principle
    Faqat fayl qayta ishlash bilan shug'ullanadi
    """
    
    name = "tasks.file_processing"
    
    def run(self, celery_task_id: str, file_path: str, task_type: str, **kwargs):
        """
        Faylni qayta ishlash
        
        Args:
            celery_task_id: Task ID
            file_path: Fayl yo'li
            task_type: Task turi
            **kwargs: Qo'shimcha parametrlar
        """
        try:
            logger.info(f"Processing file: {file_path} (Type: {task_type})")
            
            task_manager.update_progress(celery_task_id, 10, "Initializing...")
            
            ProcessorRegistry.initialize()
            
            processor = ProcessorFactory.get_processor(task_type)
            
            task_manager.update_progress(celery_task_id, 25, "Validating file...")
            
            if not processor.validate(file_path):
                raise ValueError(f"File validation failed: {file_path}")
            
            task_manager.update_progress(celery_task_id, 50, "Processing file...")
            
            result = processor.process(file_path, **kwargs)
            
            task_manager.update_progress(celery_task_id, 90, "Finalizing...")
            
            task_manager.complete_task(celery_task_id, result)
            
            task_manager.update_progress(celery_task_id, 100, "Completed!")
            
            logger.info(f"File processing completed: {celery_task_id}")
            return result
            
        except Exception as e:
            logger.error(f"File processing error: {str(e)}")
            task_manager.fail_task(celery_task_id, str(e), retry=True)
            
            if self.request.retries < self.max_retries:
                raise self.retry(exc=e)
            else:
                return {"success": False, "error": str(e)}


class BulkFileProcessingTask(BaseTask):
    """
    Ko'p faylni qayta ishlash task - Single Responsibility Principle
    """
    
    name = "tasks.bulk_file_processing"
    
    def run(self, celery_task_id: str, file_paths: list, task_type: str, **kwargs):
        """
        Ko'p faylni qayta ishlash
        
        Args:
            celery_task_id: Task ID
            file_paths: Fayl yo'llarining ro'yxati
            task_type: Task turi
        """
        try:
            total_files = len(file_paths)
            processed = 0
            results = []
            
            logger.info(f"Starting bulk processing: {total_files} files")
            
            ProcessorRegistry.initialize()
            processor = ProcessorFactory.get_processor(task_type)
            
            for idx, file_path in enumerate(file_paths):
                try:
                    progress = int((idx / total_files) * 100)
                    message = f"Processing file {idx + 1}/{total_files}: {file_path}"
                    task_manager.update_progress(celery_task_id, progress, message)
                    
                    if processor.validate(file_path):
                        result = processor.process(file_path, **kwargs)
                        results.append({
                            "file": file_path,
                            "status": "success",
                            "result": result
                        })
                        processed += 1
                    else:
                        results.append({
                            "file": file_path,
                            "status": "failed",
                            "error": "Validation failed"
                        })
                
                except Exception as e:
                    logger.warning(f"Error processing file {file_path}: {str(e)}")
                    results.append({
                        "file": file_path,
                        "status": "failed",
                        "error": str(e)
                    })
            
            final_result = {
                "total": total_files,
                "processed": processed,
                "failed": total_files - processed,
                "results": results
            }
            
            task_manager.complete_task(celery_task_id, final_result)
            logger.info(f"Bulk processing completed: {processed}/{total_files}")
            
            return final_result
            
        except Exception as e:
            logger.error(f"Bulk processing error: {str(e)}")
            task_manager.fail_task(celery_task_id, str(e))
            
            if self.request.retries < self.max_retries:
                raise self.retry(exc=e)
            else:
                return {"success": False, "error": str(e)}


@shared_task(base=FileProcessingTask, bind=True)
def process_file(self, celery_task_id: str, file_path: str, task_type: str, **kwargs):
    """
    Faylni qayta ishlash uchun shared task
    """
    return FileProcessingTask().run(celery_task_id, file_path, task_type, **kwargs)


@shared_task(base=BulkFileProcessingTask, bind=True)
def process_bulk_files(self, celery_task_id: str, file_paths: list, task_type: str, **kwargs):
    """
    Ko'p faylni qayta ishlash uchun shared task
    """
    return BulkFileProcessingTask().run(celery_task_id, file_paths, task_type, **kwargs)
