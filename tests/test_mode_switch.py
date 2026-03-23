import unittest
from unittest.mock import patch, MagicMock
import os
import sys

# 添加根目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

class TestModeSwitch(unittest.TestCase):
    def setUp(self):
        # 保存原始环境变量
        self.original_api_url = os.environ.get('API_URL')
    
    def tearDown(self):
        # 恢复原始环境变量
        if self.original_api_url is not None:
            os.environ['API_URL'] = self.original_api_url
        elif 'API_URL' in os.environ:
            del os.environ['API_URL']
    
    @patch('requests.get')
    def test_backend_available_switch_to_backend_mode(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        from app import USE_BACKEND
        
        self.assertTrue(USE_BACKEND)
        mock_get.assert_called_once()
    
    @patch('requests.get')
    def test_backend_unavailable_switch_to_local_mode(self, mock_get):
        mock_get.side_effect = Exception("Connection refused")
        
        from app import USE_BACKEND
        
        self.assertFalse(USE_BACKEND)
        mock_get.assert_called_once()
    
    @patch('requests.get')
    def test_custom_api_url(self, mock_get):
        os.environ['API_URL'] = 'http://custom-api:8000/api'
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        # 重新导入以应用新的环境变量
        if 'app' in sys.modules:
            del sys.modules['app']
        
        from app import API_URL, USE_BACKEND
        
        self.assertEqual(API_URL, 'http://custom-api:8000/api')
        self.assertTrue(USE_BACKEND)
        mock_get.assert_called_once_with('http://custom-api:8000/api/../', timeout=2)
    
    @patch('requests.get')
    def test_api_url_default_value(self, mock_get):
        if 'API_URL' in os.environ:
            del os.environ['API_URL']
        
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        if 'app' in sys.modules:
            del sys.modules['app']
        
        from app import API_URL, USE_BACKEND
        
        self.assertEqual(API_URL, 'http://localhost:8000/api')
        self.assertTrue(USE_BACKEND)
    
    @patch('requests.get')
    def test_backend_status_code_not_200(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        if 'app' in sys.modules:
            del sys.modules['app']
        
        from app import USE_BACKEND
        
        self.assertTrue(USE_BACKEND)
    
    @patch('requests.get')
    def test_backend_timeout(self, mock_get):
        from requests.exceptions import Timeout
        
        mock_get.side_effect = Timeout("Connection timeout")
        
        if 'app' in sys.modules:
            del sys.modules['app']
        
        from app import USE_BACKEND
        
        self.assertFalse(USE_BACKEND)
    
    @patch('requests.get')
    def test_backend_connection_error(self, mock_get):
        from requests.exceptions import ConnectionError
        
        mock_get.side_effect = ConnectionError("Connection error")
        
        if 'app' in sys.modules:
            del sys.modules['app']
        
        from app import USE_BACKEND
        
        self.assertFalse(USE_BACKEND)
    
    @patch('requests.post')
    def test_auth_in_backend_mode(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"username": "testuser", "role": "user"}
        mock_post.return_value = mock_response
        
        from app import USE_BACKEND
        
        if USE_BACKEND:
            mock_post.assert_not_called()
    
    @patch('requests.get')
    @patch('requests.post')
    def test_login_fallback_to_local(self, mock_post, mock_get):
        mock_get.side_effect = Exception("Backend unavailable")
        mock_post.side_effect = Exception("Backend unavailable")
        
        if 'app' in sys.modules:
            del sys.modules['app']
        
        from app import USE_BACKEND, auth_service
        
        self.assertFalse(USE_BACKEND)
        
        # 测试本地认证
        result = auth_service.authenticate("demo", "demo123")
        self.assertTrue(result)
    
    def test_mode_switch_idempotency(self):
        """测试模式切换的幂等性"""
        if 'app' in sys.modules:
            del sys.modules['app']
        
        from app import USE_BACKEND
        
        if 'app' in sys.modules:
            del sys.modules['app']
        
        from app import USE_BACKEND as USE_BACKEND2
        
        self.assertEqual(USE_BACKEND, USE_BACKEND2)

if __name__ == '__main__':
    unittest.main()