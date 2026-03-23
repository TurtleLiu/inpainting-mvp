import unittest
from unittest.mock import patch, MagicMock
import tempfile
import os
from PIL import Image
import io

# 添加backend目录到Python路径
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from backend.minio_client import minio_client

class TestMinioClient(unittest.TestCase):
    def setUp(self):
        # 创建测试图像
        self.test_image = Image.new('RGB', (100, 100), color='red')
        self.test_image_bytes = io.BytesIO()
        self.test_image.save(self.test_image_bytes, format='PNG')
        self.test_image_bytes.seek(0)
        
        # 创建临时目录
        self.temp_dir = tempfile.mkdtemp()
        self.test_file_path = os.path.join(self.temp_dir, "test_image.png")
        self.test_image.save(self.test_file_path)
        
        self.bucket_name = "inpainting-bucket"
        self.object_name = "test_image.png"
    
    def tearDown(self):
        if os.path.exists(self.test_file_path):
            os.remove(self.test_file_path)
        if os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)
    
    @patch('backend.minio_client.client')
    def test_upload_file(self, mock_minio_client):
        mock_put_object = MagicMock()
        mock_minio_client.put_object = mock_put_object
        
        minio_client.upload_file(self.object_name, self.test_file_path)
        
        mock_put_object.assert_called_once()
        args, kwargs = mock_put_object.call_args
        self.assertEqual(args[0], self.bucket_name)
        self.assertEqual(args[1], self.object_name)
    
    @patch('backend.minio_client.client')
    def test_upload_file_with_bytes(self, mock_minio_client):
        mock_put_object = MagicMock()
        mock_minio_client.put_object = mock_put_object
        
        minio_client.upload_file(self.object_name, self.test_image_bytes)
        
        mock_put_object.assert_called_once()
        args, kwargs = mock_put_object.call_args
        self.assertEqual(args[0], self.bucket_name)
        self.assertEqual(args[1], self.object_name)
    
    @patch('backend.minio_client.client')
    def test_upload_file_not_found(self, mock_minio_client):
        non_existent_path = os.path.join(self.temp_dir, "non_existent.png")
        
        with self.assertRaises(FileNotFoundError):
            minio_client.upload_file(self.object_name, non_existent_path)
    
    @patch('backend.minio_client.client')
    def test_download_file(self, mock_minio_client):
        mock_get_object = MagicMock()
        mock_response = MagicMock()
        mock_response.read.return_value = self.test_image_bytes.getvalue()
        mock_get_object.return_value = mock_response
        mock_minio_client.get_object = mock_get_object
        
        download_path = os.path.join(self.temp_dir, "downloaded.png")
        
        minio_client.download_file(self.object_name, download_path)
        
        mock_get_object.assert_called_once_with(self.bucket_name, self.object_name)
        
        self.assertTrue(os.path.exists(download_path))
        downloaded_image = Image.open(download_path)
        self.assertEqual(downloaded_image.size, (100, 100))
        
        os.remove(download_path)
    
    @patch('backend.minio_client.client')
    def test_download_file_to_nonexistent_directory(self, mock_minio_client):
        non_existent_dir = os.path.join(self.temp_dir, "nonexistent")
        download_path = os.path.join(non_existent_dir, "downloaded.png")
        
        with self.assertRaises(FileNotFoundError):
            minio_client.download_file(self.object_name, download_path)
    
    @patch('backend.minio_client.client')
    def test_delete_file(self, mock_minio_client):
        mock_remove_object = MagicMock()
        mock_minio_client.remove_object = mock_remove_object
        
        minio_client.delete_file(self.object_name)
        
        mock_remove_object.assert_called_once_with(self.bucket_name, self.object_name)
    
    @patch('backend.minio_client.client')
    def test_file_exists_true(self, mock_minio_client):
        mock_stat_object = MagicMock()
        mock_minio_client.stat_object = mock_stat_object
        
        result = minio_client.file_exists(self.object_name)
        
        mock_stat_object.assert_called_once_with(self.bucket_name, self.object_name)
        self.assertTrue(result)
    
    @patch('backend.minio_client.client')
    def test_file_exists_false(self, mock_minio_client):
        from minio.error import S3Error
        
        mock_stat_object = MagicMock()
        mock_stat_object.side_effect = S3Error("NoSuchKey")
        mock_minio_client.stat_object = mock_stat_object
        
        result = minio_client.file_exists(self.object_name)
        
        mock_stat_object.assert_called_once_with(self.bucket_name, self.object_name)
        self.assertFalse(result)
    
    @patch('backend.minio_client.client')
    def test_create_bucket_if_not_exists(self, mock_minio_client):
        mock_bucket_exists = MagicMock()
        mock_bucket_exists.return_value = False
        mock_minio_client.bucket_exists = mock_bucket_exists
        
        mock_make_bucket = MagicMock()
        mock_minio_client.make_bucket = mock_make_bucket
        
        minio_client.create_bucket_if_not_exists()
        
        mock_bucket_exists.assert_called_once_with(self.bucket_name)
        mock_make_bucket.assert_called_once_with(self.bucket_name)
    
    @patch('backend.minio_client.client')
    def test_create_bucket_if_exists(self, mock_minio_client):
        mock_bucket_exists = MagicMock()
        mock_bucket_exists.return_value = True
        mock_minio_client.bucket_exists = mock_bucket_exists
        
        mock_make_bucket = MagicMock()
        mock_minio_client.make_bucket = mock_make_bucket
        
        minio_client.create_bucket_if_not_exists()
        
        mock_bucket_exists.assert_called_once_with(self.bucket_name)
        mock_make_bucket.assert_not_called()
    
    @patch('backend.minio_client.client')
    def test_list_objects(self, mock_minio_client):
        mock_list_objects = MagicMock()
        mock_object1 = MagicMock()
        mock_object1.object_name = "image1.png"
        mock_object2 = MagicMock()
        mock_object2.object_name = "image2.png"
        mock_list_objects.return_value = [mock_object1, mock_object2]
        mock_minio_client.list_objects = mock_list_objects
        
        objects = minio_client.list_objects()
        
        mock_list_objects.assert_called_once_with(self.bucket_name)
        self.assertEqual(len(objects), 2)
        self.assertEqual(objects[0], "image1.png")
        self.assertEqual(objects[1], "image2.png")
    
    @patch('backend.minio_client.client')
    def test_upload_large_file(self, mock_minio_client):
        large_image = Image.new('RGB', (1000, 1000), color='blue')
        large_file_path = os.path.join(self.temp_dir, "large_image.png")
        large_image.save(large_file_path)
        
        mock_put_object = MagicMock()
        mock_minio_client.put_object = mock_put_object
        
        minio_client.upload_file("large_image.png", large_file_path)
        
        mock_put_object.assert_called_once()
        args, kwargs = mock_put_object.call_args
        self.assertEqual(args[0], self.bucket_name)
        self.assertEqual(args[1], "large_image.png")
        
        os.remove(large_file_path)

if __name__ == '__main__':
    unittest.main()