import unittest
from datetime import datetime
from backend.database import Base, engine, SessionLocal
from backend.models import User, Task, TaskStatus
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class TestDatabaseModels(unittest.TestCase):
    def setUp(self):
        Base.metadata.create_all(bind=engine)
        self.db = SessionLocal()
    
    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(bind=engine)
    
    def test_user_creation(self):
        user = User(
            username="testuser",
            password_hash=pwd_context.hash("testpass"),
            role="user"
        )
        self.db.add(user)
        self.db.commit()
        
        retrieved_user = self.db.query(User).filter(User.username == "testuser").first()
        self.assertIsNotNone(retrieved_user)
        self.assertEqual(retrieved_user.username, "testuser")
        self.assertEqual(retrieved_user.role, "user")
        self.assertTrue(pwd_context.verify("testpass", retrieved_user.password_hash))
    
    def test_user_duplicate_username(self):
        user1 = User(
            username="duplicate",
            password_hash=pwd_context.hash("pass1"),
            role="user"
        )
        self.db.add(user1)
        self.db.commit()
        
        user2 = User(
            username="duplicate",
            password_hash=pwd_context.hash("pass2"),
            role="user"
        )
        self.db.add(user2)
        with self.assertRaises(Exception):
            self.db.commit()
    
    def test_task_creation(self):
        user = User(
            username="taskuser",
            password_hash=pwd_context.hash("pass"),
            role="user"
        )
        self.db.add(user)
        self.db.commit()
        
        task = Task(
            user_id=user.id,
            image_filename="test_image.png",
            mask_filename="test_mask.png",
            method="telea",
            status=TaskStatus.pending
        )
        self.db.add(task)
        self.db.commit()
        
        retrieved_task = self.db.query(Task).filter(Task.id == task.id).first()
        self.assertIsNotNone(retrieved_task)
        self.assertEqual(retrieved_task.user_id, user.id)
        self.assertEqual(retrieved_task.image_filename, "test_image.png")
        self.assertEqual(retrieved_task.mask_filename, "test_mask.png")
        self.assertEqual(retrieved_task.method, "telea")
        self.assertEqual(retrieved_task.status, TaskStatus.pending)
        self.assertIsInstance(retrieved_task.created_at, datetime)
    
    def test_task_status_transition(self):
        user = User(
            username="statususer",
            password_hash=pwd_context.hash("pass"),
            role="user"
        )
        self.db.add(user)
        self.db.commit()
        
        task = Task(
            user_id=user.id,
            image_filename="image.png",
            mask_filename="mask.png",
            method="telea",
            status=TaskStatus.pending
        )
        self.db.add(task)
        self.db.commit()
        
        task.status = TaskStatus.processing
        self.db.commit()
        self.assertEqual(task.status, TaskStatus.processing)
        
        task.status = TaskStatus.completed
        task.result_filename = "result.png"
        self.db.commit()
        self.assertEqual(task.status, TaskStatus.completed)
        self.assertEqual(task.result_filename, "result.png")
    
    def test_task_with_user_relationship(self):
        user = User(
            username="reluser",
            password_hash=pwd_context.hash("pass"),
            role="user"
        )
        self.db.add(user)
        self.db.commit()
        
        task = Task(
            user_id=user.id,
            image_filename="img.png",
            mask_filename="msk.png",
            method="telea",
            status=TaskStatus.pending
        )
        self.db.add(task)
        self.db.commit()
        
        user_tasks = self.db.query(Task).filter(Task.user_id == user.id).all()
        self.assertEqual(len(user_tasks), 1)
        self.assertEqual(user_tasks[0].image_filename, "img.png")
    
    def test_task_query_by_status(self):
        user = User(
            username="queryuser",
            password_hash=pwd_context.hash("pass"),
            role="user"
        )
        self.db.add(user)
        self.db.commit()
        
        task1 = Task(
            user_id=user.id,
            image_filename="img1.png",
            mask_filename="msk1.png",
            method="telea",
            status=TaskStatus.pending
        )
        task2 = Task(
            user_id=user.id,
            image_filename="img2.png",
            mask_filename="msk2.png",
            method="telea",
            status=TaskStatus.completed
        )
        task3 = Task(
            user_id=user.id,
            image_filename="img3.png",
            mask_filename="msk3.png",
            method="telea",
            status=TaskStatus.failed
        )
        
        self.db.add_all([task1, task2, task3])
        self.db.commit()
        
        pending_tasks = self.db.query(Task).filter(Task.status == TaskStatus.pending).all()
        completed_tasks = self.db.query(Task).filter(Task.status == TaskStatus.completed).all()
        failed_tasks = self.db.query(Task).filter(Task.status == TaskStatus.failed).all()
        
        self.assertEqual(len(pending_tasks), 1)
        self.assertEqual(len(completed_tasks), 1)
        self.assertEqual(len(failed_tasks), 1)

if __name__ == '__main__':
    unittest.main()