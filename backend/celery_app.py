from celery import Celery
import os

celery_app = Celery(
    'tasks',
    broker=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
    backend=os.getenv('REDIS_URL', 'redis://localhost:6379/0')
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Shanghai',
    enable_utc=True,
)

@celery_app.task
def process_inpainting(task_id, image_path, mask_path, method="telea"):
    from PIL import Image
    import numpy as np
    import cv2
    import os
    
    try:
        from database import SessionLocal
        from models import Task, TaskStatus
        from datetime import datetime
        
        db = SessionLocal()
        
        img = Image.open(image_path).convert('RGB')
        mask = Image.open(mask_path).convert('L')
        
        img_array = np.array(img)
        mask_array = np.array(mask)
        
        if method == "telea":
            result_array = cv2.inpaint(img_array, mask_array, 3, cv2.INPAINT_TELEA)
        else:
            result_array = cv2.inpaint(img_array, mask_array, 3, cv2.INPAINT_NS)
        
        result_img = Image.fromarray(result_array)
        
        result_filename = f"{task_id}_result.png"
        result_path = os.path.join(os.getenv("MINIO_DATA_DIR", "./data"), result_filename)
        
        os.makedirs(os.path.dirname(result_path), exist_ok=True)
        result_img.save(result_path)
        
        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            task.status = TaskStatus.COMPLETED
            task.result_filename = result_filename
            task.completed_at = datetime.utcnow()
            db.commit()
        
        return {"status": "success", "result_filename": result_filename}
        
    except Exception as e:
        db = SessionLocal()
        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            task.status = TaskStatus.FAILED
            db.commit()
        return {"status": "error", "message": str(e)}