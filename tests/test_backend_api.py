import unittest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import tempfile
import os
from PIL import Image
import io

# 添加backend目录到Python路径
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from backend.app import app
from backend.database import Base, engine
from backend.models import User, Task, TaskStatus
from backend.celery_app import process_inpainting

client = TestClient(app)

class TestBackendAPI(unittest.TestCase):
    def setUp(self):
        Base.metadata.create_all(bind=engine)
    
    def tearDown(self):
        Base.metadata.drop_all(bind=engine)
    
    def test_root_endpoint(self):
        response = client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "图像修复API服务运行中"})
    
    def test_register_user(self):
        response = client.post(
            "/api/auth/register",
            json={"username": "testuser", "password": "testpass", "role": "user"}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["username"], "testuser")
        self.assertEqual(data["role"], "user")
    
    def test_register_existing_user(self):
        client.post(
            "/api/auth/register",
            json={"username": "existing", "password": "pass", "role": "user"}
        )
        response = client.post(
            "/api/auth/register",
            json={"username": "existing", "password": "pass", "role": "user"}
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("用户名已存在", response.text)
    
    @patch('backend.app.authenticate_user')
    def test_create_task(self, mock_authenticate):
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.username = "testuser"
        mock_authenticate.return_value = mock_user
        
        img = Image.new('RGB', (100, 100), color='red')
        img_buf = io.BytesIO()
        img.save(img_buf, format='PNG')
        img_buf.seek(0)
        
        mask = Image.new('L', (100, 100), color=0)
        mask_buf = io.BytesIO()
        mask.save(mask_buf, format='PNG')
        mask_buf.seek(0)
        
        response = client.post(
            "/api/tasks",
            files={
                'image': ('image.png', img_buf, 'image/png'),
                'mask': ('mask.png', mask_buf, 'image/png')
            },
            data={'method': 'telea'},
            auth=('testuser', 'testpass')
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('id', data)
        self.assertEqual(data['user_id'], 1)
        self.assertEqual(data['status'], 'pending')
        self.assertEqual(data['method'], 'telea')
    
    @patch('backend.app.authenticate_user')
    def test_get_tasks(self, mock_authenticate):
        mock_user = MagicMock()
        mock_user.id = 1
        mock_authenticate.return_value = mock_user
        
        response = client.get(
            "/api/tasks",
            auth=('testuser', 'testpass')
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), list)
    
    @patch('backend.app.authenticate_user')
    def test_get_task(self, mock_authenticate):
        mock_user = MagicMock()
        mock_user.id = 1
        mock_authenticate.return_value = mock_user
        
        img = Image.new('RGB', (100, 100), color='red')
        img_buf = io.BytesIO()
        img.save(img_buf, format='PNG')
        img_buf.seek(0)
        
        mask = Image.new('L', (100, 100), color=0)
        mask_buf = io.BytesIO()
        mask.save(mask_buf, format='PNG')
        mask_buf.seek(0)
        
        create_response = client.post(
            "/api/tasks",
            files={
                'image': ('image.png', img_buf, 'image/png'),
                'mask': ('mask.png', mask_buf, 'image/png')
            },
            data={'method': 'telea'},
            auth=('testuser', 'testpass')
        )
        
        task_id = create_response.json()['id']
        
        get_response = client.get(
            f"/api/tasks/{task_id}",
            auth=('testuser', 'testpass')
        )
        
        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(get_response.json()['id'], task_id)
    
    def test_get_nonexistent_task(self):
        response = client.get(
            "/api/tasks/nonexistent",
            auth=('user', 'pass')
        )
        self.assertEqual(response.status_code, 401)

if __name__ == '__main__':
    unittest.main()