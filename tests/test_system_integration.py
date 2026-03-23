import unittest
from unittest.mock import patch, MagicMock
import os
import sys
from PIL import Image
import io

# 添加根目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

class TestSystemIntegration(unittest.TestCase):
    def setUp(self):
        # 创建测试图像
        self.test_image = Image.new('RGB', (100, 100), color='red')
        self.test_mask = Image.new('L', (100, 100), color=0)
        
        # 将测试图像转换为字节
        self.image_bytes = io.BytesIO()
        self.test_image.save(self.image_bytes, format='PNG')
        self.image_bytes.seek(0)
        
        self.mask_bytes = io.BytesIO()
        self.test_mask.save(self.mask_bytes, format='PNG')
        self.mask_bytes.seek(0)
    
    @patch('requests.get')
    @patch('requests.post')
    @patch('requests.get')
    def test_full_system_flow_backend_mode(self, mock_get_tasks, mock_post_task, mock_backend_check):
        # 模拟后端服务可用
        backend_check_response = MagicMock()
        backend_check_response.status_code = 200
        mock_backend_check.return_value = backend_check_response
        
        # 模拟任务创建响应
        task_response = MagicMock()
        task_response.status_code = 200
        task_response.json.return_value = {
            "id": "test-task-id",
            "user_id": 1,
            "status": "pending",
            "method": "telea"
        }
        mock_post_task.return_value = task_response
        
        # 模拟任务列表响应
        tasks_response = MagicMock()
        tasks_response.status_code = 200
        tasks_response.json.return_value = [{
            "id": "test-task-id",
            "user_id": 1,
            "status": "completed",
            "method": "telea",
            "created_at": "2024-01-01T00:00:00",
            "result_filename": "result.png"
        }]
        mock_get_tasks.return_value = tasks_response
        
        # 重新导入应用以应用模拟
        if 'app' in sys.modules:
            del sys.modules['app']
        
        from app import USE_BACKEND
        
        self.assertTrue(USE_BACKEND)
        
        # 验证模拟调用
        mock_backend_check.assert_called_once()
    
    @patch('requests.get')
    @patch('requests.post')
    def test_full_system_flow_local_mode(self, mock_post, mock_get):
        # 模拟后端服务不可用
        mock_get.side_effect = Exception("Connection refused")
        
        # 重新导入应用以应用模拟
        if 'app' in sys.modules:
            del sys.modules['app']
        
        from app import USE_BACKEND, service
        
        self.assertFalse(USE_BACKEND)
        
        # 测试本地模式下的图像处理
        result = service.process_image_from_bytes(
            image_bytes=self.image_bytes.getvalue(),
            mask_bytes=self.mask_bytes.getvalue(),
            backend="opencv",
            method="telea"
        )
        
        self.assertIsNotNone(result)
        self.assertEqual(result.size, (100, 100))
    
    @patch('requests.get')
    @patch('requests.post')
    def test_auth_flow_backend_mode(self, mock_post, mock_get):
        # 模拟后端服务可用
        backend_check_response = MagicMock()
        backend_check_response.status_code = 200
        mock_get.return_value = backend_check_response
        
        # 模拟用户注册响应
        register_response = MagicMock()
        register_response.status_code = 200
        register_response.json.return_value = {"username": "testuser", "role": "user"}
        mock_post.return_value = register_response
        
        # 重新导入应用
        if 'app' in sys.modules:
            del sys.modules['app']
        
        from app import USE_BACKEND
        
        self.assertTrue(USE_BACKEND)
    
    @patch('requests.get')
    @patch('requests.post')
    def test_auth_flow_local_mode(self, mock_post, mock_get):
        # 模拟后端服务不可用
        mock_get.side_effect = Exception("Connection refused")
        mock_post.side_effect = Exception("Connection refused")
        
        # 重新导入应用
        if 'app' in sys.modules:
            del sys.modules['app']
        
        from app import USE_BACKEND, auth_service
        
        self.assertFalse(USE_BACKEND)
        
        # 测试本地认证
        auth_result = auth_service.authenticate("demo", "demo123")
        self.assertTrue(auth_result)
        
        auth_result_invalid = auth_service.authenticate("wrong", "wrong")
        self.assertFalse(auth_result_invalid)
    
    @patch('requests.get')
    def test_mode_switch_with_different_api_urls(self, mock_get):
        # 测试不同API URL的情况
        test_cases = [
            ('http://localhost:8000/api', 200, True),
            ('http://api.example.com/api', 404, True),
            ('http://invalid-api:9999/api', None, False),
        ]
        
        for api_url, status_code, expected_mode in test_cases:
            with self.subTest(api_url=api_url):
                # 设置环境变量
                os.environ['API_URL'] = api_url
                
                # 模拟响应
                if status_code is not None:
                    mock_response = MagicMock()
                    mock_response.status_code = status_code
                    mock_get.return_value = mock_response
                else:
                    mock_get.side_effect = Exception("Connection error")
                
                # 重新导入应用
                if 'app' in sys.modules:
                    del sys.modules['app']
                
                from app import API_URL, USE_BACKEND
                
                self.assertEqual(API_URL, api_url)
                self.assertEqual(USE_BACKEND, expected_mode)
    
    def test_local_mode_processing_variations(self):
        """测试本地模式下的不同处理参数"""
        from app import service
        
        test_cases = [
            ("telea", (100, 100)),
            ("navier-stokes", (100, 100)),
        ]
        
        for method, expected_size in test_cases:
            with self.subTest(method=method):
                result = service.process_image_from_bytes(
                    image_bytes=self.image_bytes.getvalue(),
                    mask_bytes=self.mask_bytes.getvalue(),
                    backend="opencv",
                    method=method
                )
                
                self.assertIsNotNone(result)
                self.assertEqual(result.size, expected_size)
    
    @patch('requests.get')
    @patch('requests.post')
    def test_backend_fallback_mechanism(self, mock_post, mock_get):
        """测试后端失败时的回退机制"""
        # 第一次调用成功，第二次调用失败
        def backend_check_side_effect(*args, **kwargs):
            if not hasattr(backend_check_side_effect, 'call_count'):
                backend_check_side_effect.call_count = 0
            backend_check_side_effect.call_count += 1
            
            if backend_check_side_effect.call_count == 1:
                response = MagicMock()
                response.status_code = 200
                return response
            else:
                raise Exception("Connection failed")
        
        mock_get.side_effect = backend_check_side_effect
        
        # 第一次导入 - 后端模式
        if 'app' in sys.modules:
            del sys.modules['app']
        
        from app import USE_BACKEND as use_backend_1
        self.assertTrue(use_backend_1)
        
        # 第二次导入 - 本地模式（回退）
        if 'app' in sys.modules:
            del sys.modules['app']
        
        from app import USE_BACKEND as use_backend_2
        self.assertFalse(use_backend_2)

if __name__ == '__main__':
    unittest.main()