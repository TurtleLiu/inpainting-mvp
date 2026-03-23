import unittest
from unittest.mock import patch, MagicMock
import os
import sys
from PIL import Image
import io
import tempfile

# 添加根目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.inpainting_app.security import validate_image_bytes, sanitize_filename
from src.inpainting_app.config import Config

class TestSecurity(unittest.TestCase):
    def setUp(self):
        # 创建测试图像
        self.test_image = Image.new('RGB', (100, 100), color='red')
        self.image_bytes = io.BytesIO()
        self.test_image.save(self.image_bytes, format='PNG')
        self.image_bytes.seek(0)
    
    def test_validate_image_bytes_valid(self):
        """测试有效的图像字节验证"""
        result = validate_image_bytes(self.image_bytes.getvalue())
        self.assertTrue(result)
    
    def test_validate_image_bytes_too_large(self):
        """测试超过大小限制的图像"""
        large_image = Image.new('RGB', (10000, 10000), color='red')
        large_bytes = io.BytesIO()
        large_image.save(large_bytes, format='PNG')
        large_bytes.seek(0)
        
        with self.assertRaises(ValueError):
            validate_image_bytes(large_bytes.getvalue())
    
    def test_validate_image_bytes_invalid_format(self):
        """测试无效的图像格式"""
        invalid_bytes = b'not an image file'
        
        with self.assertRaises(ValueError):
            validate_image_bytes(invalid_bytes)
    
    def test_validate_image_bytes_empty(self):
        """测试空图像"""
        with self.assertRaises(ValueError):
            validate_image_bytes(b'')
    
    def test_sanitize_filename_basic(self):
        """测试基本的文件名清理"""
        test_cases = [
            ("test.png", "test.png"),
            ("test@#$%.png", "test____.png"),
            ("test with spaces.png", "test_with_spaces.png"),
            ("test/file/path.png", "test_file_path.png"),
            ("test\\file\\path.png", "test_file_path.png"),
        ]
        
        for input_name, expected in test_cases:
            with self.subTest(input_name=input_name):
                result = sanitize_filename(input_name)
                self.assertEqual(result, expected)
    
    def test_sanitize_filename_malicious(self):
        """测试恶意文件名的清理"""
        malicious_cases = [
            ("../../../etc/passwd", "etc_passwd"),
            ("..\\..\\windows\\system32\\cmd.exe", "windows_system32_cmd.exe"),
            ("/etc/passwd", "etc_passwd"),
            ("C:\\windows\\system32\\cmd.exe", "C_windows_system32_cmd.exe"),
        ]
        
        for input_name, expected in malicious_cases:
            with self.subTest(input_name=input_name):
                result = sanitize_filename(input_name)
                self.assertEqual(result, expected)
    
    def test_sanitize_filename_xss(self):
        """测试XSS攻击的文件名清理"""
        xss_cases = [
            ('"><script>alert("xss")</script>', "__script_alert_xss_script_"),
            ('<img src="x" onerror="alert(1)">', "_img_src_x_onerror_alert_1_"),
            ('javascript:alert("xss")', "javascript_alert_xss_"),
        ]
        
        for input_name, expected in xss_cases:
            with self.subTest(input_name=input_name):
                result = sanitize_filename(input_name)
                self.assertEqual(result, expected)
    
    def test_config_max_upload_bytes(self):
        """测试配置中的最大上传字节数"""
        self.assertEqual(Config.max_upload_bytes, 10 * 1024 * 1024)
    
    def test_config_max_pixels(self):
        """测试配置中的最大像素数"""
        self.assertEqual(Config.max_pixels, 4096 * 4096)
    
    def test_config_inpaint_backend_default(self):
        """测试默认的修复后端"""
        self.assertEqual(Config.inpaint_backend, "opencv")
    
    @patch.dict(os.environ, {'INPAINT_BACKEND': 'diffusers'})
    def test_config_inpaint_backend_from_env(self):
        """测试从环境变量设置的修复后端"""
        from src.inpainting_app.config import Config
        self.assertEqual(Config.inpaint_backend, "diffusers")
    
    def test_image_file_extension_validation(self):
        """测试图像文件扩展名验证"""
        valid_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp']
        invalid_extensions = ['.txt', '.exe', '.pdf', '.zip', '.py']
        
        for ext in valid_extensions:
            filename = f"test{ext}"
            img = Image.new('RGB', (100, 100))
            buf = io.BytesIO()
            format_map = {'.jpg': 'JPEG', '.jpeg': 'JPEG', '.png': 'PNG', '.gif': 'GIF', '.bmp': 'BMP'}
            img.save(buf, format=format_map.get(ext, 'PNG'))
            buf.seek(0)
            
            try:
                validate_image_bytes(buf.getvalue())
            except ValueError:
                self.fail(f"Valid extension {ext} failed validation")
        
        for ext in invalid_extensions:
            filename = f"test{ext}"
            invalid_bytes = f"This is not an image{ext}".encode()
            
            with self.assertRaises(ValueError):
                validate_image_bytes(invalid_bytes)
    
    def test_large_image_validation(self):
        """测试超大图像的验证"""
        # 创建接近限制的图像
        max_dim = int(Config.max_pixels ** 0.5)
        large_image = Image.new('RGB', (max_dim, max_dim))
        large_bytes = io.BytesIO()
        large_image.save(large_bytes, format='PNG')
        large_bytes.seek(0)
        
        try:
            validate_image_bytes(large_bytes.getvalue())
        except ValueError:
            self.fail("Large but valid image failed validation")
        
        # 创建超过限制的图像
        oversized_image = Image.new('RGB', (max_dim + 1, max_dim + 1))
        oversized_bytes = io.BytesIO()
        oversized_image.save(oversized_bytes, format='PNG')
        oversized_bytes.seek(0)
        
        with self.assertRaises(ValueError):
            validate_image_bytes(oversized_bytes.getvalue())
    
    def test_filename_length_validation(self):
        """测试文件名长度验证"""
        # 正常长度文件名
        normal_name = "a" * 50 + ".png"
        result = sanitize_filename(normal_name)
        self.assertEqual(len(result), 54)
        
        # 超长文件名
        long_name = "a" * 500 + ".png"
        result = sanitize_filename(long_name)
        # 清理后的文件名应该被截断或处理
        self.assertTrue(len(result) > 0)
    
    def test_mixed_special_characters(self):
        """测试混合特殊字符的文件名清理"""
        mixed_name = "test@#$%^&*()_+[]{}|;:'\",.<>/?\\`~! image.png"
        expected = "test__________+[]{}|;:'\",.<>/?\\`~!_image.png"
        result = sanitize_filename(mixed_name)
        self.assertEqual(result, expected)

if __name__ == '__main__':
    unittest.main()