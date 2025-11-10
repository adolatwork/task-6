from abc import ABC, abstractmethod
from typing import Dict, Any
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class ProcessorInterface(ABC):
    """
    Abstrakty processor interface - Interface Segregation Principle
    Faqat zarur bo'lgan metodlarni aniqlash
    """
    
    @abstractmethod
    def validate(self, file_path: str) -> bool:
        """Faylni validatsiya qilish"""
        pass
    
    @abstractmethod
    def process(self, file_path: str, **kwargs) -> Dict[str, Any]:
        """Faylni qayta ishlash"""
        pass
    
    @abstractmethod
    def get_supported_formats(self) -> list:
        """Qo'llab-quvatlanadigan formatlarni olish"""
        pass


class BaseProcessor(ProcessorInterface):
    """
    Asosiy processor - Single Responsibility Principle
    Umumiy amallarni bajarish
    """
    
    def __init__(self, max_file_size: int = 1024 * 1024 * 100):
        """
        Args:
            max_file_size: Maksimal fayl hajmi (default 100MB)
        """
        self.max_file_size = max_file_size
        self.logger = logger
    
    def validate(self, file_path: str) -> bool:
        """Faylni asosiy validatsiya"""
        path = Path(file_path)
        
        if not path.exists():
            self.logger.error(f"File not found: {file_path}")
            return False
        
        if not path.is_file():
            self.logger.error(f"Not a file: {file_path}")
            return False
        
        if not self._is_supported_format(file_path):
            self.logger.error(f"Unsupported format: {file_path}")
            return False
        
        if path.stat().st_size > self.max_file_size:
            self.logger.error(f"File too large: {file_path}")
            return False
        
        return True
    
    def _is_supported_format(self, file_path: str) -> bool:
        """Format to'g'ri yoki yo'qligini tekshirish"""
        extension = Path(file_path).suffix.lower()
        return extension in self.get_supported_formats()
    
    @abstractmethod
    def process(self, file_path: str, **kwargs) -> Dict[str, Any]:
        """Qayta ishlash - child klassalar tomonidan amalga oshiriladi"""
        pass
    
    @abstractmethod
    def get_supported_formats(self) -> list:
        """Qo'llab-quvatlanadigan formatlar"""
        pass
    
    def _read_file_chunks(self, file_path: str, chunk_size: int = 1024 * 1024):
        """Faylni bo'laklar bo'yicha o'qish - memory efficient"""
        path = Path(file_path)
        
        with open(path, 'rb') as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                yield chunk
    
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """Fayl haqida asosiy ma'lumot"""
        path = Path(file_path)
        
        return {
            "name": path.name,
            "size": path.stat().st_size,
            "extension": path.suffix,
            "path": str(path),
        }
