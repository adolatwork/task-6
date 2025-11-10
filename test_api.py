#!/usr/bin/env python3

import requests
import base64
import time
import sys
from pathlib import Path

BASE_URL = "http://localhost:8000"
USERNAME = "a"
PASSWORD = "a"


FILES_DIR = Path(__file__).parent / "files"


def get_auth_headers():
    """Basic Auth headers yaratish"""
    credentials = base64.b64encode(f"{USERNAME}:{PASSWORD}".encode()).decode()
    return {
        "Authorization": f"Basic {credentials}",
        "Content-Type": "application/json"
    }


def create_task(file_path, task_type, metadata=None):
    """Yangi task yaratish"""
    url = f"{BASE_URL}/tasks/create_task/"
    data = {
        "file_path": str(file_path),
        "task_type": task_type,
        "metadata": metadata or {}
    }
    
    print(f"\n📤 Task yaratilmoqda: {file_path.name} ({task_type})")
    response = requests.post(url, headers=get_auth_headers(), json=data)
    
    if response.status_code == 201:
        task_data = response.json()
        print(f"✅ Task yaratildi!")
        print(f"   Task ID: {task_data.get('id')}")
        print(f"   Celery Task ID: {task_data.get('celery_task_id')}")
        print(f"   Status: {task_data.get('status')}")
        return task_data
    else:
        print(f"❌ Xatolik: {response.status_code}")
        print(f"   {response.text}")
        return None


def get_task_status(task_id):
    """Task holatini olish"""
    url = f"{BASE_URL}/tasks/{task_id}/"
    response = requests.get(url, headers=get_auth_headers())
    
    if response.status_code == 200:
        return response.json()
    return None


def wait_for_task_completion(task_id, timeout=60):
    """Task tugashini kutish"""
    print(f"\n⏳ Task tugashini kutmoqda...")
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        task = get_task_status(task_id)
        if task:
            status = task.get('status')
            progress = task.get('progress', 0)
            print(f"   Status: {status} | Progress: {progress}%", end='\r')
            
            if status in ['completed', 'failed', 'cancelled']:
                print() 
                return task
        
        time.sleep(1)
    
    print(f"\n⏱️  Timeout! Task {timeout} soniyadan keyin ham tugamadi")
    return None


def test_image_processing():
    """Image fayl bilan test"""
    print("\n" + "="*60)
    print("📷 IMAGE PROCESSING TEST")
    print("="*60)
    
    image_file = FILES_DIR / "Screenshot 2025-07-04 at 16.50.47.png"
    
    if not image_file.exists():
        print(f"❌ Fayl topilmadi: {image_file}")
        return
    
    task = create_task(image_file, "image")
    if task:
        task_id = task.get('id')
        completed_task = wait_for_task_completion(task_id)
        
        if completed_task:
            print(f"\n✅ Task tugadi: {completed_task.get('status')}")
            if completed_task.get('status') == 'completed':
                result = completed_task.get('result', {})
                print(f"   Format: {result.get('format')}")
                print(f"   Size: {result.get('size')}")
                print(f"   Mode: {result.get('mode')}")


def test_document_processing():
    """Document fayl bilan test"""
    print("\n" + "="*60)
    print("📄 DOCUMENT PROCESSING TEST")
    print("="*60)
    
    text_file = FILES_DIR / "test_document.txt"
    if text_file.exists():
        print("\n--- Text File Test ---")
        task = create_task(text_file, "document")
        if task:
            task_id = task.get('id')
            completed_task = wait_for_task_completion(task_id)
            if completed_task and completed_task.get('status') == 'completed':
                result = completed_task.get('result', {})
                print(f"   Line count: {result.get('line_count')}")
    
    json_file = FILES_DIR / "test_data.json"
    if json_file.exists():
        print("\n--- JSON File Test ---")
        task = create_task(json_file, "document")
        if task:
            task_id = task.get('id')
            completed_task = wait_for_task_completion(task_id)
            if completed_task and completed_task.get('status') == 'completed':
                result = completed_task.get('result', {})
                print(f"   Content keys: {list(result.get('content', {}).keys())}")
    
    csv_file = FILES_DIR / "test_data.csv"
    if csv_file.exists():
        print("\n--- CSV File Test ---")
        task = create_task(csv_file, "document")
        if task:
            task_id = task.get('id')
            completed_task = wait_for_task_completion(task_id)
            if completed_task and completed_task.get('status') == 'completed':
                result = completed_task.get('result', {})
                print(f"   Rows: {result.get('line_count')}")


def get_progress_summary():
    """Progress summary olish"""
    print("\n" + "="*60)
    print("📊 PROGRESS SUMMARY")
    print("="*60)
    
    url = f"{BASE_URL}/tasks/progress/"
    response = requests.get(url, headers=get_auth_headers())
    
    if response.status_code == 200:
        summary = response.json()
        print(f"   Pending: {summary.get('pending', 0)}")
        print(f"   Processing: {summary.get('processing', 0)}")
        print(f"   Completed: {summary.get('completed', 0)}")
        print(f"   Failed: {summary.get('failed', 0)}")
        print(f"   Total: {summary.get('total', 0)}")
    else:
        print(f"❌ Xatolik: {response.status_code}")


def main():
    """Asosiy funksiya"""
    print("🚀 API Test Script")
    print(f"Base URL: {BASE_URL}")
    print(f"Username: {USERNAME}")
    
    try:
        response = requests.get(f"{BASE_URL}/tasks/", headers=get_auth_headers(), timeout=5)
        if response.status_code == 200:
            print("✅ API ga ulanish muvaffaqiyatli!")
        else:
            print(f"⚠️  API javob berdi, lekin status code: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ API ga ulanib bo'lmadi. Server ishlayaptimi?")
        print(f"   {BASE_URL} ni tekshiring")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Xatolik: {e}")
        sys.exit(1)
    
    try:
        test_image_processing()
        test_document_processing()
        get_progress_summary()
        
        print("\n" + "="*60)
        print("✅ Barcha testlar yakunlandi!")
        print("="*60)
        print("\n💡 Admin panelda natijalarni ko'rish:")
        print(f"   {BASE_URL}/admin/file_processor/tasklog/")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Test to'xtatildi")
    except Exception as e:
        print(f"\n❌ Xatolik: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

