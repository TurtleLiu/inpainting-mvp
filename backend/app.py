from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
import os
from datetime import datetime

from database import SessionLocal, engine
from models import User, Task
from schemas import UserCreate, UserResponse, TaskCreate, TaskResponse, TaskStatus

app = FastAPI(title="图像修复API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBasic()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def authenticate_user(credentials: HTTPBasicCredentials = Depends(security), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == credentials.username).first()
    if not user or user.password != credentials.password:
        raise HTTPException(
            status_code=401,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Basic"},
        )
    return user

@app.post("/api/auth/register", response_model=UserResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    new_user = User(
        username=user.username,
        password=user.password,
        role=user.role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user

@app.post("/api/tasks", response_model=TaskResponse)
def create_task(
    image: UploadFile = File(...),
    mask: UploadFile = File(...),
    method: str = "telea",
    user: User = Depends(authenticate_user),
    db: Session = Depends(get_db)
):
    task_id = str(uuid.uuid4())
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    image_filename = f"{task_id}_{timestamp}_image.png"
    mask_filename = f"{task_id}_{timestamp}_mask.png"
    
    task = Task(
        id=task_id,
        user_id=user.id,
        status=TaskStatus.PENDING,
        method=method,
        image_filename=image_filename,
        mask_filename=mask_filename,
        created_at=datetime.now()
    )
    
    db.add(task)
    db.commit()
    db.refresh(task)
    
    return task

@app.get("/api/tasks", response_model=List[TaskResponse])
def get_tasks(
    skip: int = 0,
    limit: int = 100,
    user: User = Depends(authenticate_user),
    db: Session = Depends(get_db)
):
    tasks = db.query(Task).filter(Task.user_id == user.id).offset(skip).limit(limit).all()
    return tasks

@app.get("/api/tasks/{task_id}", response_model=TaskResponse)
def get_task(
    task_id: str,
    user: User = Depends(authenticate_user),
    db: Session = Depends(get_db)
):
    task = db.query(Task).filter(Task.id == task_id, Task.user_id == user.id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return task

@app.get("/api/tasks/{task_id}/result")
def get_task_result(
    task_id: str,
    user: User = Depends(authenticate_user),
    db: Session = Depends(get_db)
):
    task = db.query(Task).filter(Task.id == task_id, Task.user_id == user.id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    if task.status != TaskStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="任务尚未完成")
    
    result_filename = task.result_filename
    if not result_filename:
        raise HTTPException(status_code=404, detail="结果文件不存在")
    
    result_path = os.path.join(os.getenv("MINIO_DATA_DIR", "./data"), result_filename)
    
    if not os.path.exists(result_path):
        raise HTTPException(status_code=404, detail="结果文件不存在")
    
    from fastapi.responses import FileResponse
    return FileResponse(result_path, media_type="image/png", filename=result_filename)

@app.get("/")
def root():
    return {"message": "图像修复API服务运行中"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)