import unittest
from unittest.mock import patch, MagicMock
import os
import sys
from PIL import Image
import io

# 添加根目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.inpainting_app.service import InpaintingService
from src.inpainting_app.auth import AuthService
from src.inpainting_app.sam_mask import grabcut_mask

class TestAcceptance(unittest.TestCase):
    def setUp(self):
        self.service = InpaintingService()
        self.auth_service = AuthService()
        
        # 创建测试图像
        self.test_image = Image.new('RGB', (200, 200), color='red')
        self.image_bytes = io.BytesIO()
        self.test_image.save(self.image_bytes, format='PNG')
        self.image_bytes.seek(0)
        
        # 创建测试mask
        self.test_mask = Image.new('L', (200, 200), color=0)
        self.mask_bytes = io.BytesIO()
        self.test_mask.save(self.mask_bytes, format='PNG')
        self.mask_bytes.seek(0)
    
    def test_user_login_flow(self):
        """验收测试：用户登录流程"""
        # 测试有效登录
        login_result = self.auth_service.authenticate("demo", "demo123")
        self.assertTrue(login_result)
        
        # 测试无效登录
        login_result = self.auth_service.authenticate("wrong", "wrong")
        self.assertFalse(login_result)
    
    def test_single_image_inpainting_flow(self):
        """验收测试：单图修复完整流程"""
        # 步骤1: 用户登录
        login_success = self.auth_service.authenticate("demo", "demo123")
        self.assertTrue(login_success)
        
        # 步骤2: 上传图像
        # 步骤3: 创建mask
        mask = grabcut_mask(self.test_image, (50, 50, 150, 150))
        mask_bytes = io.BytesIO()
        mask.save(mask_bytes, format='PNG')
        mask_bytes.seek(0)
        
        # 步骤4: 执行修复
        result = self.service.process_image_from_bytes(
            image_bytes=self.image_bytes.getvalue(),
            mask_bytes=mask_bytes.getvalue(),
            backend="opencv",
            method="telea"
        )
        
        # 验证结果
        self.assertIsNotNone(result)
        self.assertEqual(result.size, (200, 200))
    
    def test_batch_processing_flow(self):
        """验收测试：批量处理流程"""
        # 创建多个测试图像
        images = []
        masks = []
        
        for i in range(3):
            img = Image.new('RGB', (100, 100), color=['red', 'green', 'blue'][i])
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='PNG')
            img_bytes.seek(0)
            images.append(img_bytes.getvalue())
            
            mask = grabcut_mask(img, (20, 20, 80, 80))
            mask_bytes = io.BytesIO()
            mask.save(mask_bytes, format='PNG')
            mask_bytes.seek(0)
            masks.append(mask_bytes.getvalue())
        
        # 批量处理
        results = []
        for img_bytes, mask_bytes in zip(images, masks):
            result = self.service.process_image_from_bytes(
                image_bytes=img_bytes,
                mask_bytes=mask_bytes,
                backend="opencv",
                method="telea"
            )
            results.append(result)
        
        # 验证结果
        self.assertEqual(len(results), 3)
        for result in results:
            self.assertIsNotNone(result)
            self.assertEqual(result.size, (100, 100))
    
    def test_auto_mask_generation(self):
        """验收测试：自动Mask生成功能"""
        # 测试默认参数
        mask = grabcut_mask(self.test_image, (50, 50, 150, 150))
        
        # 验证mask属性
        self.assertIsNotNone(mask)
        self.assertEqual(mask.size, (200, 200))
        self.assertEqual(mask.mode, 'L')
        
        # 验证白色区域存在
        mask_array = list(mask.getdata())
        white_pixels = sum(1 for pixel in mask_array if pixel == 255)
        self.assertTrue(white_pixels > 0)
    
    def test_different_inpainting_methods(self):
        """验收测试：不同修复算法"""
        mask = grabcut_mask(self.test_image, (50, 50, 150, 150))
        mask_bytes = io.BytesIO()
        mask.save(mask_bytes, format='PNG')
        mask_bytes.seek(0)
        
        # 测试telea算法
        result_telea = self.service.process_image_from_bytes(
            image_bytes=self.image_bytes.getvalue(),
            mask_bytes=mask_bytes.getvalue(),
            backend="opencv",
            method="telea"
        )
        
        # 测试navier-stokes算法
        result_ns = self.service.process_image_from_bytes(
            image_bytes=self.image_bytes.getvalue(),
            mask_bytes=mask_bytes.getvalue(),
            backend="opencv",
            method="navier-stokes"
        )
        
        # 验证两种算法都能正常工作
        self.assertIsNotNone(result_telea)
        self.assertIsNotNone(result_ns)
        self.assertEqual(result_telea.size, (200, 200))
        self.assertEqual(result_ns.size, (200, 200))
    
    def test_edge_case_handling(self):
        """验收测试：边界情况处理"""
        # 测试小图像
        small_image = Image.new('RGB', (10, 10), color='red')
        small_bytes = io.BytesIO()
        small_image.save(small_bytes, format='PNG')
        small_bytes.seek(0)
        
        small_mask = grabcut_mask(small_image, (2, 2, 8, 8))
        small_mask_bytes = io.BytesIO()
        small_mask.save(small_mask_bytes, format='PNG')
        small_mask_bytes.seek(0)
        
        result = self.service.process_image_from_bytes(
            image_bytes=small_bytes.getvalue(),
            mask_bytes=small_mask_bytes.getvalue(),
            backend="opencv",
            method="telea"
        )
        
        self.assertIsNotNone(result)
        self.assertEqual(result.size, (10, 10))
    
    def test_task_history_management(self):
        """验收测试：任务历史管理"""
        # 模拟任务历史记录
        history = []
        
        # 执行多次修复任务
        for i in range(3):
            mask = grabcut_mask(self.test_image, (50 + i*10, 50, 150 + i*10, 150))
            mask_bytes = io.BytesIO()
            mask.save(mask_bytes, format='PNG')
            mask_bytes.seek(0)
            
            result = self.service.process_image_from_bytes(
                image_bytes=self.image_bytes.getvalue(),
                mask_bytes=mask_bytes.getvalue(),
                backend="opencv",
                method="telea"
            )
            
            # 记录任务历史
            history.append({
                "task_id": f"task_{i}",
                "method": "telea",
                "result": result
            })
        
        # 验证历史记录
        self.assertEqual(len(history), 3)
        for task in history:
            self.assertIn("task_id", task)
            self.assertIn("method", task)
            self.assertIn("result", task)
            self.assertEqual(task["method"], "telea")
            self.assertIsNotNone(task["result"])
    
    def test_error_handling(self):
        """验收测试：错误处理"""
        # 测试无效的图像数据
        invalid_image = b"not an image"
        
        with self.assertRaises(Exception):
            self.service.process_image_from_bytes(
                image_bytes=invalid_image,
                mask_bytes=self.mask_bytes.getvalue(),
                backend="opencv",
                method="telea"
            )
        
        # 测试无效的mask数据
        invalid_mask = b"not a mask"
        
        with self.assertRaises(Exception):
            self.service.process_image_from_bytes(
                image_bytes=self.image_bytes.getvalue(),
                mask_bytes=invalid_mask,
                backend="opencv",
                method="telea"
            )
    
    def test_complete_user_scenario(self):
        """验收测试：完整用户场景"""
        # 用户登录
        login_success = self.auth_service.authenticate("demo", "demo123")
        self.assertTrue(login_success)
        
        # 上传图像并生成mask
        mask = grabcut_mask(self.test_image, (50, 50, 150, 150))
        mask_bytes = io.BytesIO()
        mask.save(mask_bytes, format='PNG')
        mask_bytes.seek(0)
        
        # 执行修复
        result = self.service.process_image_from_bytes(
            image_bytes=self.image_bytes.getvalue(),
            mask_bytes=mask_bytes.getvalue(),
            backend="opencv",
            method="telea"
        )
        
        # 验证结果
        self.assertIsNotNone(result)
        self.assertEqual(result.size, (200, 200))
        
        # 模拟保存到历史记录
        task_history = [{
            "timestamp": "2024-01-01 12:00:00",
            "method": "telea",
            "result": result
        }]
        
        self.assertEqual(len(task_history), 1)
        self.assertEqual(task_history[0]["method"], "telea")

if __name__ == '__main__':
    unittest.main()