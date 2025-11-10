from typing import Dict, Type, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class ProcessorFactory:
    """
    Processor yaratish fabrikasi - Factory Pattern
    Dependency Injection va Abstraction bilan
    """
    
    _processors: Dict[str, Type] = {}
    
    @classmethod
    def register(cls, file_type: str, processor_class: Type):
        """
        Yangi processor turini registratsiya qilish
        
        Args:
            file_type: Fayl turi (image, video, document)
            processor_class: Processor class
        
        Example:
            ProcessorFactory.register("image", ImageProcessor)
        """
        cls._processors[file_type.lower()] = processor_class
        logger.info(f"Processor registered: {file_type} -> {processor_class.__name__}")
    
    @classmethod
    def get_processor(cls, file_type: str) -> Optional[object]:
        """
        Fayl turi bo'yicha processor olish
        
        Args:
            file_type: Fayl turi
        
        Returns:
            Processor instance yoki None
        
        Raises:
            ValueError: Fayl turi topilmasa
        """
        processor_class = cls._processors.get(file_type.lower())
        
        if not processor_class:
            raise ValueError(f"Unknown processor type: {file_type}")
        
        return processor_class()
    
    @classmethod
    def get_processor_by_extension(cls, file_path: str) -> Optional[object]:
        """
        Fayl kengaytmasi bo'yicha processor olish
        
        Args:
            file_path: Fayl yo'li
        
        Returns:
            Processor instance yoki None
        """
        extension = Path(file_path).suffix.lower()
        
        for processor_class in cls._processors.values():
            processor = processor_class()
            if extension in processor.get_supported_formats():
                return processor
        
        raise ValueError(f"No processor found for extension: {extension}")
    
    @classmethod
    def get_registered_types(cls) -> Dict[str, Type]:
        """Barcha registered processor turlarini olish"""
        return cls._processors.copy()
    
    @classmethod
    def is_supported(cls, file_path: str) -> bool:
        """Faylning qo'llab-quvatlanishini tekshirish"""
        try:
            cls.get_processor_by_extension(file_path)
            return True
        except ValueError:
            return False


class ProcessorRegistry:
    """
    Processor registratsiyasi - Singleton Pattern
    Aplikatsiya boshlashda barcha processorlarni ro'yxatga olish
    """
    
    _initialized = False
    
    @classmethod
    def initialize(cls):
        """Barcha processorlarni registratsiya qilish"""
        if cls._initialized:
            return
        
        try:
            from .concrete_processors import (
                ImageProcessor,
                DocumentProcessor,
                VideoProcessor
            )
            
            ProcessorFactory.register("image", ImageProcessor)
            ProcessorFactory.register("document", DocumentProcessor)
            ProcessorFactory.register("video", VideoProcessor)
            
            cls._initialized = True
            logger.info("Processor registry initialized successfully")
            
        except ImportError as e:
            logger.error(f"Failed to initialize processor registry: {e}")
            raise
