# Test Qilish Qo'llanmasi

## Qo'llab-quvvatlanadigan Fayl Turlari

### 1. 📷 Image (Rasm) - `task_type: "image"`

**Qo'llab-quvvatlanadigan formatlar:**
- `.jpg` / `.jpeg`
- `.png`
- `.gif`
- `.webp`
- `.bmp`

**Test qilish:**
```bash
# Swagger UI orqali
POST /tasks/create_task/
{
  "file_path": "/Users/abdulaziz/Documents/self_improvement/paylov-tasks/task_6/files/Screenshot 2025-07-04 at 16.50.47.png",
  "task_type": "image",
  "metadata": {}
}

# yoki curl orqali
curl -X POST http://localhost:8000/tasks/create_task/ \
  -H "Authorization: Basic base64(username:password)" \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "/Users/abdulaziz/Documents/self_improvement/paylov-tasks/task_6/files/Screenshot 2025-07-04 at 16.50.47.png",
    "task_type": "image"
  }'
```

**Natija:**
- Rasm format, o'lcham, mode
- EXIF metadata (agar mavjud bo'lsa)
- Rasm haqida boshqa ma'lumotlar

---

### 2. 📄 Document (Hujjat) - `task_type: "document"`

**Qo'llab-quvvatlanadigan formatlar:**
- `.txt` - Matn fayllar
- `.json` - JSON fayllar
- `.csv` - CSV fayllar
- `.pdf` - PDF fayllar (asosiy qo'llab-quvvatlash)

**Test qilish:**

#### Text fayl (.txt)
```bash
POST /tasks/create_task/
{
  "file_path": "/path/to/your/file.txt",
  "task_type": "document"
}
```

#### JSON fayl (.json)
```bash
POST /tasks/create_task/
{
  "file_path": "/path/to/your/data.json",
  "task_type": "document"
}
```

#### CSV fayl (.csv)
```bash
POST /tasks/create_task/
{
  "file_path": "/path/to/your/data.csv",
  "task_type": "document"
}
```

**Natija:**
- Fayl ma'lumotlari
- Kontent preview (text uchun)
- Qatorlar soni
- JSON/CSV parsing natijalari

---

### 3. 🎥 Video - `task_type: "video"`

**Qo'llab-quvvatlanadigan formatlar:**
- `.mp4`
- `.avi`
- `.mov`
- `.mkv`
- `.webm`

**Test qilish:**
```bash
POST /tasks/create_task/
{
  "file_path": "/path/to/your/video.mp4",
  "task_type": "video"
}
```

**Natija:**
- Video fayl ma'lumotlari
- Metadata (duration, bitrate, resolution, codec, fps)

---

## Test Fayllarini Yaratish

### 1. Test Image Yaratish
```bash
# Terminalda
cd /Users/abdulaziz/Documents/self_improvement/paylov-tasks/task_6/files

# Python orqali test rasm yaratish
python3 << EOF
from PIL import Image
import os

# Oddiy test rasm
img = Image.new('RGB', (800, 600), color='red')
img.save('test_image.jpg')
print("Test image yaratildi: test_image.jpg")
EOF
```

### 2. Test Text Fayl Yaratish
```bash
cd /Users/abdulaziz/Documents/self_improvement/paylov-tasks/task_6/files

cat > test_document.txt << EOF
Bu test hujjat fayli.
Bu yerda bir nechta qator bor.
Bu fayl test qilish uchun yaratilgan.
EOF
```

### 3. Test JSON Fayl Yaratish
```bash
cd /Users/abdulaziz/Documents/self_improvement/paylov-tasks/task_6/files

cat > test_data.json << EOF
{
  "name": "Test Data",
  "version": "1.0",
  "items": [
    {"id": 1, "name": "Item 1"},
    {"id": 2, "name": "Item 2"}
  ]
}
EOF
```

### 4. Test CSV Fayl Yaratish
```bash
cd /Users/abdulaziz/Documents/self_improvement/paylov-tasks/task_6/files

cat > test_data.csv << EOF
id,name,email
1,John Doe,john@example.com
2,Jane Smith,jane@example.com
3,Bob Johnson,bob@example.com
EOF
```

---

## Python orqali Test Qilish

### Test Script Yaratish

```python
# test_api.py
import requests
import base64
import json

# Basic Auth
username = "your_username"
password = "your_password"
credentials = base64.b64encode(f"{username}:{password}".encode()).decode()

headers = {
    "Authorization": f"Basic {credentials}",
    "Content-Type": "application/json"
}

# Test Image
image_task = {
    "file_path": "/Users/abdulaziz/Documents/self_improvement/paylov-tasks/task_6/files/Screenshot 2025-07-04 at 16.50.47.png",
    "task_type": "image",
    "metadata": {"test": True}
}

response = requests.post(
    "http://localhost:8000/tasks/create_task/",
    headers=headers,
    json=image_task
)

print("Image Task Response:")
print(json.dumps(response.json(), indent=2))
print(f"Task ID: {response.json().get('id')}")

# Test Document
text_task = {
    "file_path": "/Users/abdulaziz/Documents/self_improvement/paylov-tasks/task_6/files/test_document.txt",
    "task_type": "document"
}

response = requests.post(
    "http://localhost:8000/tasks/create_task/",
    headers=headers,
    json=text_task
)

print("\nDocument Task Response:")
print(json.dumps(response.json(), indent=2))
```

---

## Swagger UI orqali Test Qilish

1. **Swagger UI ochish:**
   ```
   http://localhost:8000/api/docs/
   ```

2. **Authentication:**
   - "Authorize" tugmasini bosing
   - Basic Auth: username va password kiriting
   - yoki Token Auth: `Token your-token-here` formatida kiriting

3. **Task yaratish:**
   - `POST /tasks/create_task/` endpointini toping
   - "Try it out" tugmasini bosing
   - Request body ni to'ldiring:
     ```json
     {
       "file_path": "/Users/abdulaziz/Documents/self_improvement/paylov-tasks/task_6/files/Screenshot 2025-07-04 at 16.50.47.png",
       "task_type": "image",
       "metadata": {}
     }
     ```
   - "Execute" tugmasini bosing

4. **Task holatini kuzatish:**
   - `GET /tasks/{id}/` - Task ma'lumotlarini olish
   - `GET /tasks/progress/` - Barcha tasklarning progress summary

---

## Mavjud Test Fayllar

Sizning `files/` papkangizda:
- ✅ `Screenshot 2025-07-04 at 16.50.47.png` - Image test qilish uchun tayyor
- ⚠️ `python_developer_task.docx` - .docx format qo'llab-quvvatlanmaydi

---

## Tez Test Qilish

### 1. Mavjud PNG fayl bilan:
```bash
curl -X POST http://localhost:8000/tasks/create_task/ \
  -u username:password \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "/Users/abdulaziz/Documents/self_improvement/paylov-tasks/task_6/files/Screenshot 2025-07-04 at 16.50.47.png",
    "task_type": "image"
  }'
```

### 2. Task holatini tekshirish:
```bash
# Task ID ni oling (yuqoridagi response dan)
curl -u username:password \
  http://localhost:8000/tasks/{task_id}/
```

### 3. Progress summary:
```bash
curl -u username:password \
  http://localhost:8000/tasks/progress/
```

---

## Xatolarni Tekshirish

Agar task muvaffaqiyatsiz bo'lsa:
1. Admin panelda tekshiring: `http://localhost:8000/admin/file_processor/tasklog/`
2. Celery loglarni ko'ring: `tail -f celery.log`
3. Task event loglarni ko'ring: `http://localhost:8000/admin/file_processor/taskeventlog/`

---

## Maslahatlar

1. **Fayl yo'li:** To'liq absolute path ishlating
2. **Fayl mavjudligi:** Fayl mavjudligini tekshiring
3. **Ruxsatlar:** Fayl o'qish uchun ruxsati borligini tekshiring
4. **Fayl hajmi:** 
   - Image: maksimal 50MB
   - Document: maksimal 100MB
   - Video: maksimal 500MB

