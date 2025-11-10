# Celery Task Queue Challenge

## 📋 Loyiha Tavsifi

Bu loyihada Django + Celery ishlatib fayllarni asynchronous qayta ishlash tizimi

---

## 🔧 Setup va Installation

### 1. Requirements o'rnatish
```bash
pip install -r requirements.txt
```

### 2. Environment variables (.env)
```env
SECRET_KEY=your-secret-key-here
DEBUG=True

# Database
DB_NAME=celery_db
DB_USER=postgres
DB_PASSWORD=password
DB_HOST=localhost
DB_PORT=5432

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1
```

### 3. Redis o'rnatish
```bash
# Mac
brew install redis
redis-server

# Ubuntu
sudo apt-get install redis-server
redis-server

# Docker
docker run -d -p 6379:6379 redis:latest
```

### 4. Database migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Celery worker boshlash
```bash
# Simple worker
celery -A config worker -l info

# Parallel workers (4 concurrency)
celery -A config worker -l info --concurrency=4

# Separate queues
celery -A config worker -Q file_processing,bulk_processing -l info
```

### 6. Celery Beat (Periodic tasks)
```bash
celery -A config beat -l info
```

---

## 📚 API Documentation (Swagger)

Interactive API documentation is available using Swagger/OpenAPI:

- **Swagger UI**: http://localhost:8000/api/docs/
- **ReDoc**: http://localhost:8000/api/redoc/
- **OpenAPI Schema**: http://localhost:8000/api/schema/

---

## 🔐 Authentication

### Basic Authentication (HTTP Basic Auth)
Use your Django username and password:
```http
Authorization: Basic base64(username:password)
```

**Example with curl:**
```bash
curl -u username:password http://localhost:8000/api/tasks/
```

**Example with Python requests:**
```python
import requests
response = requests.get(
    'http://localhost:8000/api/tasks/',
    auth=('username', 'password')
)
```

## 💻 API Endpoints

### 1. Task ro'yxati olish
```http
GET /api/tasks/
Authorization: Basic base64(username:password)
# OR
Authorization: Token <token>

Query Parameters:
  - status: pending, processing, completed, failed, cancelled
  - task_type: image, video, document
  - from_date: 2024-01-01
  - to_date: 2024-12-31
  - search: filename
  - page: 1
  - page_size: 20

Response:
{
  "count": 100,
  "next": "...",
  "results": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "celery_task_id": "abc123...",
      "status": "processing",
      "task_type": "image",
      "file_name": "photo.jpg",
      "file_size": 2048576,
      "progress": 45,
      "created_at": "2024-01-15T10:30:00Z",
      "completed_at": null
    }
  ]
}
```

### 2. Task yaratish (Yangi fayl qayta ishlash)
```http
POST /api/tasks/create_task/
Authorization: Basic base64(username:password)
# OR
Authorization: Token <token>
Content-Type: application/json

Request:
{
  "file_path": "/path/to/image.jpg",
  "task_type": "image",
  "metadata": {
    "quality": "high",
    "resize": [1920, 1080]
  }
}

Response (201):
{
  "celery_task_id": "abc123...",
  "task_type": "image",
  "file_name": "image.jpg",
  "file_size": 2048576,
  "status": "pending",
  "progress": 0,
  "created_at": "2024-01-15T10:30:00Z"
}
```

### 3. Task ma'lumoti olish
```http
GET /api/tasks/{id}/
Authorization: Basic base64(username:password)
# OR
Authorization: Token <token>

Response:
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "celery_task_id": "abc123...",
  "status": "processing",
  "progress": 75,
  "file_name": "image.jpg",
  "file_size": 2048576,
  "error_message": null,
  "retry_count": 0,
  "created_at": "2024-01-15T10:30:00Z",
  "started_at": "2024-01-15T10:30:05Z",
  "completed_at": null,
  "is_cancellable": true,
  "is_retryable": false,
  "elapsed_time": 35.5
}
```

### 4. Task bekor qilish
```http
POST /api/tasks/{id}/cancel/
Authorization: Basic base64(username:password)
# OR
Authorization: Token <token>
Content-Type: application/json

Request:
{
  "reason": "User cancelled"
}

Response (200):
{
  "status": "cancelled"
}
```

### 5. Task qayta urinish
```http
POST /api/tasks/{id}/retry/
Authorization: Basic base64(username:password)
# OR
Authorization: Token <token>
Content-Type: application/json

Request:
{
  "force": false
}

Response (200):
{
  "status": "retrying"
}
```

### 6. Progress summary
```http
GET /api/tasks/progress/
Authorization: Basic base64(username:password)
# OR
Authorization: Token <token>

Response:
{
  "pending": 5,
  "processing": 3,
  "completed": 25,
  "failed": 2,
  "total": 35
}
```

### 7. Ko'p task yaratish (Bulk)
```http
POST /api/tasks/bulk_create/
Authorization: Basic base64(username:password)
# OR
Authorization: Token <token>
Content-Type: application/json

Request:
{
  "file_paths": [
    "/path/to/file1.jpg",
    "/path/to/file2.jpg",
    "/path/to/file3.jpg"
  ],
  "task_type": "image",
  "parallel": true
}

Response (201):
{
  "celery_task_id": "bulk123...",
  "status": "processing",
  "files_count": 3
}
```

---

## 📊 Database Schema

### TaskLog (Asosiy model)
- id (UUID)
- celery_task_id (String, unique, indexed)
- task_type (String, indexed)
- status (String, indexed)
- file_name, file_size, file_path
- progress (0-100)
- result, error_message, error_code
- retry_count, max_retries
- Timestamps (created_at, started_at, completed_at, cancelled_at)
- user_id, tags, metadata

### TaskProgress (Progress history)
- id (BigInt)
- task_id (ForeignKey -> TaskLog)
- progress (0-100)
- message, data
- created_at (indexed)

### TaskEventLog (Audit trail)
- id (BigInt)
- task_id (ForeignKey -> TaskLog)
- event_type (created, started, progress, completed, failed, cancelled)
- message, metadata
- created_at (indexed)

---

## 🚀 Performance Tips

### 1. Celery Configuration
```python
# Worker tuning
CELERYD_CONCURRENCY = 4
CELERY_WORKER_PREFETCH_MULTIPLIER = 4
CELERY_TASK_ACKS_LATE = True

# Task routing
CELERY_TASK_ROUTES = {
    'tasks.file_processing': {'queue': 'file_processing'},
    'tasks.bulk_file_processing': {'queue': 'bulk_processing'},
}
```

### 2. Database Optimization
```python
# Indexes
- (status, created_at)
- (user_id, status)
- celery_task_id

# Batch operations
Task.objects.bulk_create(tasks, batch_size=100)
```

### 3. Caching Strategy
```python
from django.core.cache import cache

# Task result caching
cache.set(f'task:{task_id}', result, timeout=3600)
result = cache.get(f'task:{task_id}')
```

---

## 🔍 Monitoring va Debugging

### Celery Monitoring Tools

```bash
# Celery Flower (Web UI)
pip install flower
celery -A config flower

# Access at http://localhost:5555
```

### Logs Kuzatish
```bash
# All logs
tail -f celery.log

# Filter by task
grep "task_id" celery.log

# Real-time monitoring
celery -A config inspect active
celery -A config inspect scheduled
celery -A config inspect registered
```
