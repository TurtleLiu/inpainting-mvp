import unittest
import os
import sys
import tempfile
from PIL import Image
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.inpainting_app.service import InpaintingService
from src.inpainting_app.security import validate_image_bytes, sanitize_filename
from src.inpainting_app.config import config
from src.inpainting_app.auth import AuthService
from src.inpainting_app.sam_mask import grabcut_mask


class TestSecurity(unittest.TestCase):
    def test_sanitize_filename(self):
        self.assertEqual(sanitize_filename("test.png"), "test.png")
        self.assertEqual(sanitize_filename("test@#$%.png"), "test____.png")
        self.assertEqual(sanitize_filename("/path/to/test.png"), "test.png")
    
    def test_validate_image_bytes_valid(self):
        img = Image.new('RGB', (100, 100), color='red')
        buf = tempfile.SpooledTemporaryFile(max_size=1024*1024)
        img.save(buf, format='PNG')
        buf.seek(0)
        content = buf.read()
        buf.close()
        
        try:
            validate_image_bytes(content)
        except ValueError:
            self.fail("validate_image_bytes raised ValueError unexpectedly")
    
    def test_validate_image_bytes_too_large(self):
        img = Image.new('RGB', (5000, 5000), color='red')
        buf = tempfile.SpooledTemporaryFile(max_size=1024*1024*100)
        img.save(buf, format='PNG')
        buf.seek(0)
        content = buf.read()
        buf.close()
        
        with self.assertRaises(ValueError):
            validate_image_bytes(content)
    
    def test_validate_image_bytes_invalid(self):
        with self.assertRaises(ValueError):
            validate_image_bytes(b"not an image")


class TestImageOps(unittest.TestCase):
    def setUp(self):
        self.service = InpaintingService()
    
    def test_inpaint_opencv_telea(self):
        img = Image.new('RGB', (100, 100), color='red')
        mask = Image.new('L', (100, 100), color=0)
        mask.paste(255, (20, 20, 80, 80))
        
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as img_file:
            img.save(img_file, format='PNG')
            img_path = img_file.name
        
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as mask_file:
            mask.save(mask_file, format='PNG')
            mask_path = mask_file.name
        
        try:
            result = self.service.inpaint(img_path, mask_path, backend='opencv', method='telea')
            self.assertIsInstance(result, Image.Image)
            self.assertEqual(result.size, (100, 100))
        finally:
            os.unlink(img_path)
            os.unlink(mask_path)
    
    def test_inpaint_opencv_ns(self):
        img = Image.new('RGB', (100, 100), color='blue')
        mask = Image.new('L', (100, 100), color=0)
        mask.paste(255, (30, 30, 70, 70))
        
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as img_file:
            img.save(img_file, format='PNG')
            img_path = img_file.name
        
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as mask_file:
            mask.save(mask_file, format='PNG')
            mask_path = mask_file.name
        
        try:
            result = self.service.inpaint(img_path, mask_path, backend='opencv', method='navier-stokes')
            self.assertIsInstance(result, Image.Image)
            self.assertEqual(result.size, (100, 100))
        finally:
            os.unlink(img_path)
            os.unlink(mask_path)


class TestService(unittest.TestCase):
    def setUp(self):
        self.service = InpaintingService()
    
    def test_process_image_from_bytes(self):
        img = Image.new('RGB', (50, 50), color='green')
        mask = Image.new('L', (50, 50), color=0)
        mask.paste(255, (10, 10, 40, 40))
        
        img_buf = tempfile.SpooledTemporaryFile(max_size=1024*1024)
        img.save(img_buf, format='PNG')
        img_buf.seek(0)
        img_bytes = img_buf.read()
        img_buf.close()
        
        mask_buf = tempfile.SpooledTemporaryFile(max_size=1024*1024)
        mask.save(mask_buf, format='PNG')
        mask_buf.seek(0)
        mask_bytes = mask_buf.read()
        mask_buf.close()
        
        result = self.service.process_image_from_bytes(img_bytes, mask_bytes)
        self.assertIsInstance(result, Image.Image)
        self.assertEqual(result.size, (50, 50))


class TestIntegration(unittest.TestCase):
    def test_end_to_end(self):
        service = InpaintingService()
        
        img = Image.new('RGB', (80, 80), color='yellow')
        mask = Image.new('L', (80, 80), color=0)
        mask.paste(255, (25, 25, 55, 55))
        
        img_buf = tempfile.SpooledTemporaryFile(max_size=1024*1024)
        img.save(img_buf, format='PNG')
        img_buf.seek(0)
        img_bytes = img_buf.read()
        img_buf.close()
        
        mask_buf = tempfile.SpooledTemporaryFile(max_size=1024*1024)
        mask.save(mask_buf, format='PNG')
        mask_buf.seek(0)
        mask_bytes = mask_buf.read()
        mask_buf.close()
        
        service.validate_image(img_bytes)
        service.validate_image(mask_bytes)
        
        result = service.process_image_from_bytes(img_bytes, mask_bytes)
        
        self.assertIsInstance(result, Image.Image)
        self.assertEqual(result.size, (80, 80))


class TestConfig(unittest.TestCase):
    def test_config_values(self):
        self.assertEqual(config.max_upload_bytes, 10 * 1024 * 1024)
        self.assertEqual(config.max_pixels, 4096 * 4096)
        self.assertEqual(config.inpaint_backend, 'opencv')


class TestAuth(unittest.TestCase):
    def setUp(self):
        self.auth_service = AuthService()
    
    def test_authenticate_valid_user(self):
        self.assertTrue(self.auth_service.authenticate("admin", "admin123"))
        self.assertTrue(self.auth_service.authenticate("demo", "demo123"))
    
    def test_authenticate_invalid_user(self):
        self.assertFalse(self.auth_service.authenticate("nonexistent", "password"))
    
    def test_authenticate_invalid_password(self):
        self.assertFalse(self.auth_service.authenticate("admin", "wrongpassword"))
    
    def test_register_new_user(self):
        new_username = "testuser"
        new_password = "testpass"
        
        if new_username in self.auth_service.users:
            del self.auth_service.users[new_username]
        
        result = self.auth_service.register(new_username, new_password)
        self.assertTrue(result)
        self.assertTrue(self.auth_service.authenticate(new_username, new_password))
    
    def test_register_existing_user(self):
        result = self.auth_service.register("admin", "newpassword")
        self.assertFalse(result)
    
    def test_get_user_role(self):
        self.assertEqual(self.auth_service.get_user_role("admin"), "admin")
        self.assertEqual(self.auth_service.get_user_role("demo"), "user")
        self.assertIsNone(self.auth_service.get_user_role("nonexistent"))


class TestAutoMask(unittest.TestCase):
    def test_grabcut_mask(self):
        img = Image.new('RGB', (100, 100), color='red')
        
        mask = grabcut_mask(img, (20, 20, 80, 80))
        
        self.assertIsInstance(mask, Image.Image)
        self.assertEqual(mask.size, (100, 100))
        self.assertEqual(mask.mode, 'L')
    
    def test_grabcut_mask_with_invalid_bbox(self):
        img = Image.new('RGB', (50, 50), color='blue')
        
        mask = grabcut_mask(img, (-10, -10, 100, 100))
        
        self.assertIsInstance(mask, Image.Image)
        self.assertEqual(mask.size, (50, 50))
    
    def test_grabcut_mask_with_edge_bbox(self):
        img = Image.new('RGB', (60, 60), color='green')
        
        mask = grabcut_mask(img, (0, 0, 60, 60))
        
        self.assertIsInstance(mask, Image.Image)
        self.assertEqual(mask.size, (60, 60))
    
    def test_grabcut_mask_white_region(self):
        img = Image.new('RGB', (100, 100), color='blue')
        
        mask = grabcut_mask(img, (20, 20, 80, 80))
        
        self.assertIsInstance(mask, Image.Image)
        self.assertEqual(mask.size, (100, 100))
        self.assertEqual(mask.mode, 'L')
        
        mask_array = np.array(mask)
        
        white_pixels = np.sum(mask_array == 255)
        black_pixels = np.sum(mask_array == 0)
        
        expected_white_area = (80 - 20) * (80 - 20)
        expected_black_area = 100 * 100 - expected_white_area
        
        self.assertEqual(white_pixels, expected_white_area)
        self.assertEqual(black_pixels, expected_black_area)


class TestBatchProcessing(unittest.TestCase):
    def setUp(self):
        self.service = InpaintingService()
    
    def test_batch_processing(self):
        images = []
        masks = []
        
        for i in range(3):
            img = Image.new('RGB', (50, 50), color=['red', 'green', 'blue'][i])
            mask = Image.new('L', (50, 50), color=0)
            mask.paste(255, (10, 10, 40, 40))
            
            img_buf = tempfile.SpooledTemporaryFile(max_size=1024*1024)
            img.save(img_buf, format='PNG')
            img_buf.seek(0)
            images.append(img_buf.read())
            img_buf.close()
            
            mask_buf = tempfile.SpooledTemporaryFile(max_size=1024*1024)
            mask.save(mask_buf, format='PNG')
            mask_buf.seek(0)
            masks.append(mask_buf.read())
            mask_buf.close()
        
        results = []
        for img_bytes, mask_bytes in zip(images, masks):
            result = self.service.process_image_from_bytes(img_bytes, mask_bytes)
            results.append(result)
        
        self.assertEqual(len(results), 3)
        for result in results:
            self.assertIsInstance(result, Image.Image)
            self.assertEqual(result.size, (50, 50))


def update_test_results(readme_path, test_results):
    with open(readme_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    start_marker = '<!-- TEST_RESULTS_START -->'
    end_marker = '<!-- TEST_RESULTS_END -->'
    
    start_idx = content.find(start_marker)
    end_idx = content.find(end_marker)
    
    if start_idx == -1 or end_idx == -1:
        return
    
    header = content[:start_idx + len(start_marker)]
    footer = content[end_idx:]
    
    table_lines = []
    table_lines.append('| 测试用例 | 状态 | 耗时 |')
    table_lines.append('|---------|------|------|')
    
    passed = 0
    failed = 0
    total_time = 0.0
    
    for result in test_results:
        test_name = result['test_name']
        status = '✅ PASS' if result['status'] == 'passed' else '❌ FAIL'
        time = f"{result['time']:.2f}s"
        table_lines.append(f'| {test_name} | {status} | {time} |')
        
        if result['status'] == 'passed':
            passed += 1
        else:
            failed += 1
        total_time += result['time']
    
    stats_lines = []
    stats_lines.append('')
    stats_lines.append('**测试统计**:')
    stats_lines.append(f'- ✅ 通过: {passed}/{passed + failed} ({passed / (passed + failed) * 100:.0f}%)')
    stats_lines.append(f'- ❌ 失败: {failed}/{passed + failed}')
    stats_lines.append(f'- ⏱️ 总耗时: {total_time:.2f}s')
    
    new_content = header + '\n' + '\n'.join(table_lines) + '\n' + '\n'.join(stats_lines) + '\n' + footer
    
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(new_content)


class TestResultWithTiming(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.test_results = []
    
    def startTest(self, test):
        self._start_time = time.time()
        super().startTest(test)
    
    def stopTest(self, test):
        elapsed = time.time() - self._start_time
        status = 'passed' if test not in self.failures and test not in self.errors else 'failed'
        self.test_results.append({
            'test_name': test.id().split('.')[-1],
            'status': status,
            'time': elapsed
        })
        super().stopTest(test)


if __name__ == '__main__':
    import time
    
    # 创建测试套件
    suite = unittest.TestSuite()
    
    # 添加当前文件中的测试用例
    suite.addTests(unittest.TestLoader().loadTestsFromModule(__import__(__name__)))
    
    # 添加新创建的测试文件
    try:
        from test_backend_api import TestBackendAPI
        suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestBackendAPI))
    except ImportError:
        print("Warning: test_backend_api.py not found")
    
    try:
        from test_database_models import TestDatabaseModels
        suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestDatabaseModels))
    except ImportError:
        print("Warning: test_database_models.py not found")
    
    try:
        from test_celery_tasks import TestCeleryTasks
        suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestCeleryTasks))
    except ImportError:
        print("Warning: test_celery_tasks.py not found")
    
    try:
        from test_minio_client import TestMinioClient
        suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestMinioClient))
    except ImportError:
        print("Warning: test_minio_client.py not found")
    
    try:
        from test_mode_switch import TestModeSwitch
        suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestModeSwitch))
    except ImportError:
        print("Warning: test_mode_switch.py not found")
    
    try:
        from test_system_integration import TestSystemIntegration
        suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestSystemIntegration))
    except ImportError:
        print("Warning: test_system_integration.py not found")
    
    try:
        from test_security import TestSecurity as TestSecurityNew
        suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestSecurityNew))
    except ImportError:
        print("Warning: test_security.py not found")
    
    try:
        from test_acceptance import TestAcceptance
        suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestAcceptance))
    except ImportError:
        print("Warning: test_acceptance.py not found")
    
    # 运行测试
    runner = unittest.TextTestRunner(resultclass=TestResultWithTiming, verbosity=2)
    result = runner.run(suite)
    
    if result.test_results:
        readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
        update_test_results(readme_path, result.test_results)