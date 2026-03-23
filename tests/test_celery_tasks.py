import unittest
from unittest.mock import patch, MagicMock
import tempfile
import os
from PIL import Image
import io

# 添加backend目录到Python路径
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from backend.celery_app import process_inpainting, celery_app
from backend.models import TaskStatus

class TestCeleryTasks(unittest.TestCase):
    def setUp(self):
        self.task_id = "test_task_123"
        self.image_filename = "test_image.png"
        self.mask_filename = "test_mask.png"
        self.method = "telea"
        
        # 创建测试图像
        self.test_image = Image.new('RGB', (100, 100), color='red')
        self.test_mask = Image.new('L', (100, 100), color=0)
        
        # 创建临时目录存储测试文件
        self.temp_dir = tempfile.mkdtemp()
        self.image_path = os.path.join(self.temp_dir, self.image_filename)
        self.mask_path = os.path.join(self.temp_dir, self.mask_filename)
        
        self.test_image.save(self.image_path)
        self.test_mask.save(self.mask_path)
    
    def tearDown(self):
        if os.path.exists(self.image_path):
            os.remove(self.image_path)
        if os.path.exists(self.mask_path):
            os.remove(self.mask_path)
        if os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)
    
    @patch('backend.celery_app.InpaintingService')
    @patch('backend.celery_app.update_task_status')
    @patch('backend.celery_app.get_db_session')
    @patch('backend.celery_app.minio_client')
    def test_process_inpainting_success(self, mock_minio, mock_db_session, mock_update_status, mock_service):
        mock_service_instance = MagicMock()
        mock_service.return_value = mock_service_instance
        
        mock_result_image = Image.new('RGB', (100, 100), color='blue')
        mock_service_instance.process_image_from_files.return_value = mock_result_image
        
        mock_db = MagicMock()
        mock_db_session.return_value.__enter__.return_value = mock_db
        
        mock_minio.download_file.return_value = None
        mock_minio.upload_file.return_value = None
        
        result = process_inpainting(
            task_id=self.task_id,
            image_filename=self.image_filename,
            mask_filename=self.mask_filename,
            method=self.method
        )
        
        # 验证服务调用
        mock_service.assert_called_once()
        mock_service_instance.process_image_from_files.assert_called_once_with(
            image_path=self.image_path,
            mask_path=self.mask_path,
            backend="opencv",
            method=self.method
        )
        
        # 验证状态更新
        mock_update_status.assert_any_call(self.task_id, TaskStatus.processing)
        mock_update_status.assert_any_call(self.task_id, TaskStatus.completed)
        
        # 验证MinIO操作
        mock_minio.download_file.assert_any_call(self.image_filename, self.image_path)
        mock_minio.download_file.assert_any_call(self.mask_filename, self.mask_path)
        mock_minio.upload_file.assert_called_once()
        
        self.assertEqual(result, "Task completed successfully")
    
    @patch('backend.celery_app.InpaintingService')
    @patch('backend.celery_app.update_task_status')
    @patch('backend.celery_app.get_db_session')
    @patch('backend.celery_app.minio_client')
    def test_process_inpainting_with_ns_method(self, mock_minio, mock_db_session, mock_update_status, mock_service):
        mock_service_instance = MagicMock()
        mock_service.return_value = mock_service_instance
        
        mock_result_image = Image.new('RGB', (100, 100), color='green')
        mock_service_instance.process_image_from_files.return_value = mock_result_image
        
        mock_db = MagicMock()
        mock_db_session.return_value.__enter__.return_value = mock_db
        
        mock_minio.download_file.return_value = None
        mock_minio.upload_file.return_value = None
        
        result = process_inpainting(
            task_id=self.task_id,
            image_filename=self.image_filename,
            mask_filename=self.mask_filename,
            method="navier-stokes"
        )
        
        mock_service_instance.process_image_from_files.assert_called_once_with(
            image_path=self.image_path,
            mask_path=self.mask_path,
            backend="opencv",
            method="navier-stokes"
        )
        
        mock_update_status.assert_any_call(self.task_id, TaskStatus.processing)
        mock_update_status.assert_any_call(self.task_id, TaskStatus.completed)
        
        self.assertEqual(result, "Task completed successfully")
    
    @patch('backend.celery_app.InpaintingService')
    @patch('backend.celery_app.update_task_status')
    @patch('backend.celery_app.get_db_session')
    @patch('backend.celery_app.minio_client')
    def test_process_inpainting_with_exception(self, mock_minio, mock_db_session, mock_update_status, mock_service):
        mock_service_instance = MagicMock()
        mock_service.return_value = mock_service_instance
        
        mock_service_instance.process_image_from_files.side_effect = Exception("Processing failed")
        
        mock_db = MagicMock()
        mock_db_session.return_value.__enter__.return_value = mock_db
        
        mock_minio.download_file.return_value = None
        
        with self.assertRaises(Exception):
            process_inpainting(
                task_id=self.task_id,
                image_filename=self.image_filename,
                mask_filename=self.mask_filename,
                method=self.method
            )
        
        mock_update_status.assert_any_call(self.task_id, TaskStatus.processing)
        mock_update_status.assert_any_call(self.task_id, TaskStatus.failed)
    
    @patch('backend.celery_app.update_task_status')
    @patch('backend.celery_app.get_db_session')
    @patch('backend.celery_app.minio_client')
    def test_process_inpainting_file_not_found(self, mock_minio, mock_db_session, mock_update_status):
        mock_minio.download_file.side_effect = FileNotFoundError("File not found")
        
        mock_db = MagicMock()
        mock_db_session.return_value.__enter__.return_value = mock_db
        
        with self.assertRaises(FileNotFoundError):
            process_inpainting(
                task_id=self.task_id,
                image_filename=self.image_filename,
                mask_filename=self.mask_filename,
                method=self.method
            )
        
        mock_update_status.assert_any_call(self.task_id, TaskStatus.processing)
        mock_update_status.assert_any_call(self.task_id, TaskStatus.failed)
    
    @patch('backend.celery_app.InpaintingService')
    @patch('backend.celery_app.update_task_status')
    @patch('backend.celery_app.get_db_session')
    @patch('backend.celery_app.minio_client')
    def test_process_inpainting_with_large_images(self, mock_minio, mock_db_session, mock_update_status, mock_service):
        large_image = Image.new('RGB', (500, 500), color='red')
        large_mask = Image.new('L', (500, 500), color=0)
        
        large_image_path = os.path.join(self.temp_dir, "large_image.png")
        large_mask_path = os.path.join(self.temp_dir, "large_mask.png")
        
        large_image.save(large_image_path)
        large_mask.save(large_mask_path)
        
        mock_service_instance = MagicMock()
        mock_service.return_value = mock_service_instance
        mock_service_instance.process_image_from_files.return_value = large_image
        
        mock_db = MagicMock()
        mock_db_session.return_value.__enter__.return_value = mock_db
        
        mock_minio.download_file.return_value = None
        mock_minio.upload_file.return_value = None
        
        result = process_inpainting(
            task_id=self.task_id,
            image_filename="large_image.png",
            mask_filename="large_mask.png",
            method=self.method
        )
        
        mock_service_instance.process_image_from_files.assert_called_once()
        mock_update_status.assert_any_call(self.task_id, TaskStatus.processing)
        mock_update_status.assert_any_call(self.task_id, TaskStatus.completed)
        
        self.assertEqual(result, "Task completed successfully")
        
        if os.path.exists(large_image_path):
            os.remove(large_image_path)
        if os.path.exists(large_mask_path):
            os.remove(large_mask_path)

if __name__ == '__main__':
    unittest.main()