from .base_processor import BaseProcessor
from typing import Dict, Any
from PIL import Image
import logging
import json

logger = logging.getLogger(__name__)


class ImageProcessor(BaseProcessor):
    """
    Rasm qayta ishlash - Open/Closed Principle
    Yangi processor turlarini qo'shish oson, mavjud kodga o'zgartirishlar minimal
    """
    
    SUPPORTED_FORMATS = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp']
    
    def __init__(self, max_file_size: int = 1024 * 1024 * 50):
        super().__init__(max_file_size=max_file_size)
    
    def get_supported_formats(self) -> list:
        """Qo'llab-quvatlanadigan rasm formatları"""
        return self.SUPPORTED_FORMATS
    
    def process(self, file_path: str, **kwargs) -> Dict[str, Any]:
        """
        Rasmni qayta ishlash
        
        Args:
            file_path: Rasm faylining yo'li
            **kwargs: Qo'shimcha parametrlar (resize, compress, extract_metadata)
        
        Returns:
            Qayta ishlash natijalari
        """
        try:
            self.logger.info(f"Processing image: {file_path}")
            
            if not self.validate(file_path):
                return {"success": False, "error": "Validation failed"}
            
            image = Image.open(file_path)
            
            metadata = self._extract_metadata(image)
            
            result = {
                "success": True,
                "format": image.format,
                "mode": image.mode,
                "size": image.size,
                "metadata": metadata,
                "file_info": self.get_file_info(file_path),
            }
            
            if kwargs.get("resize"):
                result["resize"] = self._resize_image(image, kwargs["resize"])
            
            if kwargs.get("compress"):
                result["compression"] = self._compress_image(image, kwargs["compress"])
            
            return result
            
        except Exception as e:
            self.logger.error(f"Image processing error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    def _extract_metadata(self, image: Image.Image) -> Dict[str, Any]:
        """Rasm metadatalarini ekstrakti qilish"""
        metadata = {
            "format": image.format,
            "mode": image.mode,
            "size": image.size,
            "info": dict(image.info) if image.info else {},
        }
        
        try:
            from PIL.Image import Exif
            exif = image.getexif()
            if exif:
                metadata["exif"] = {
                    str(k): str(v) for k, v in exif.items()
                }
        except:
            pass
        
        return metadata
    
    def _resize_image(self, image: Image.Image, size: tuple) -> Dict[str, Any]:
        """Rasmni o'lchamini o'zgartirish"""
        try:
            resized = image.resize(size, Image.Resampling.LANCZOS)
            return {
                "success": True,
                "original_size": image.size,
                "new_size": resized.size,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _compress_image(self, image: Image.Image, quality: int = 85) -> Dict[str, Any]:
        """Rasmni siqishtirishni aniqlash"""
        try:
            return {
                "success": True,
                "original_size": self.get_file_info("")["size"],
                "quality": quality,
                "format": image.format or "JPEG",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


class DocumentProcessor(BaseProcessor):
    """
    Hujjat qayta ishlash - Open/Closed Principle
    """
    
    SUPPORTED_FORMATS = ['.txt', '.json', '.csv', '.pdf']
    
    def __init__(self, max_file_size: int = 1024 * 1024 * 100):
        super().__init__(max_file_size=max_file_size)
    
    def get_supported_formats(self) -> list:
        return self.SUPPORTED_FORMATS
    
    def process(self, file_path: str, **kwargs) -> Dict[str, Any]:
        """
        Hujjatni qayta ishlash
        """
        try:
            self.logger.info(f"Processing document: {file_path}")
            
            if not self.validate(file_path):
                return {"success": False, "error": "Validation failed"}
            
            file_info = self.get_file_info(file_path)
            extension = file_info["extension"].lower()
            
            if extension == '.json':
                content = self._process_json(file_path)
            elif extension == '.csv':
                content = self._process_csv(file_path)
            elif extension == '.txt':
                content = self._process_text(file_path)
            else:
                content = {"error": "Unsupported format"}
            
            return {
                "success": True,
                "file_info": file_info,
                "content": content,
                "line_count": len(content) if isinstance(content, list) else None,
            }
            
        except Exception as e:
            self.logger.error(f"Document processing error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    def _process_json(self, file_path: str) -> Dict[str, Any]:
        """JSON faylni qayta ishlash"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _process_csv(self, file_path: str) -> list:
        """CSV faylni qayta ishlash"""
        import csv
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            return list(reader)
    
    def _process_text(self, file_path: str) -> Dict[str, Any]:
        """Matn faylni qayta ishlash"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return {
            "preview": content[:500],
            "full_length": len(content),
            "line_count": len(content.split('\n')),
        }


class VideoProcessor(BaseProcessor):
    """
    Video qayta ishlash - Liskov Substitution Principle
    """
    
    SUPPORTED_FORMATS = ['.mp4', '.avi', '.mov', '.mkv', '.webm']
    
    def __init__(self, max_file_size: int = 1024 * 1024 * 500):
        super().__init__(max_file_size=max_file_size)
    
    def get_supported_formats(self) -> list:
        return self.SUPPORTED_FORMATS
    
    def process(self, file_path: str, **kwargs) -> Dict[str, Any]:
        """
        Video faylni qayta ishlash
        """
        try:
            self.logger.info(f"Processing video: {file_path}")
            
            if not self.validate(file_path):
                return {"success": False, "error": "Validation failed"}
            
            metadata = self._extract_video_metadata(file_path)
            
            return {
                "success": True,
                "file_info": self.get_file_info(file_path),
                "metadata": metadata,
            }
            
        except Exception as e:
            self.logger.error(f"Video processing error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    def _extract_video_metadata(self, file_path: str) -> Dict[str, Any]:
        """Video metadatalarini ekstrakti qilish"""
        return {
            "duration": "00:00:00",
            "bitrate": "Unknown",
            "resolution": "Unknown",
            "codec": "Unknown",
            "fps": "Unknown",
        }
