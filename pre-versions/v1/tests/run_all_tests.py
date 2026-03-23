import sys
import os
import io
import unittest
from PIL import Image

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from inpainting_app.config import AppConfig
from inpainting_app.service import InpaintingService
from inpainting_app.image_ops import inpaint_image, prepare_mask
from inpainting_app.security import validate_upload, validate_mask, sanitize_filename, SecurityError

class TestHelper:
    @staticmethod
    def create_sample_image():
        img = Image.new("RGB", (64, 64), "white")
        for x in range(20, 44):
            for y in range(20, 44):
                img.putpixel((x, y), (255, 0, 0))
        return img

    @staticmethod
    def create_sample_mask():
        mask = Image.new("L", (64, 64), 0)
        for x in range(24, 40):
            for y in range(24, 40):
                mask.putpixel((x, y), 255)
        return mask

    @staticmethod
    def pil_to_upload(img, fmt="PNG", name="file.png"):
        bio = io.BytesIO()
        img.save(bio, format=fmt)
        bio.name = name
        bio.seek(0)
        return bio

class UnitTests(unittest.TestCase):
    def test_prepare_mask_binary(self):
        mask = TestHelper.create_sample_mask()
        out = prepare_mask(mask)
        vals = set(out.getdata())
        self.assertTrue(vals.issubset({0, 255}))

    def test_inpaint_returns_image(self):
        img = TestHelper.create_sample_image()
        mask = TestHelper.create_sample_mask()
        result = inpaint_image(img, mask, algorithm="telea", radius=3, max_edge=128)
        self.assertEqual(result.output_image.size, img.size)
        self.assertEqual(result.meta["algorithm"], "telea")
        self.assertTrue(result.meta["masked_pixels"] > 0)

    def test_service_run_success(self):
        img = TestHelper.create_sample_image()
        mask = TestHelper.create_sample_mask()
        svc = InpaintingService(AppConfig())
        result = svc.run(img, mask, algorithm="ns", radius=5, max_edge=128)
        self.assertEqual(result.output_image.size, (64, 64))

    def test_service_invalid_algorithm(self):
        img = TestHelper.create_sample_image()
        mask = TestHelper.create_sample_mask()
        svc = InpaintingService(AppConfig())
        with self.assertRaises(ValueError):
            svc.run(img, mask, algorithm="bad", radius=5, max_edge=128)

    def test_service_invalid_radius(self):
        img = TestHelper.create_sample_image()
        mask = TestHelper.create_sample_mask()
        svc = InpaintingService(AppConfig())
        with self.assertRaises(ValueError):
            svc.run(img, mask, algorithm="telea", radius=0, max_edge=128)

class SystemTests(unittest.TestCase):
    def test_full_system_workflow(self):
        cfg = AppConfig()
        img = TestHelper.create_sample_image()
        mask = TestHelper.create_sample_mask()
        
        svc = InpaintingService(cfg)
        result = svc.run(img, mask, algorithm="telea", radius=3, max_edge=256)
        
        self.assertIsNotNone(result.output_image)
        self.assertEqual(result.output_image.size, img.size)
        self.assertTrue("masked_pixels" in result.meta)
        self.assertTrue("algorithm" in result.meta)
        self.assertTrue("radius" in result.meta)

    def test_system_with_different_algorithms(self):
        cfg = AppConfig()
        img = TestHelper.create_sample_image()
        mask = TestHelper.create_sample_mask()
        
        for algo in ["telea", "ns"]:
            svc = InpaintingService(cfg)
            result = svc.run(img, mask, algorithm=algo, radius=3, max_edge=256)
            self.assertEqual(result.meta["algorithm"], algo)
            self.assertEqual(result.output_image.size, img.size)

class AcceptanceTests(unittest.TestCase):
    def test_end_to_end_acceptance_with_sample_files(self):
        cfg = AppConfig()
        img = TestHelper.create_sample_image()
        mask = TestHelper.create_sample_mask()
        
        img_upload = TestHelper.pil_to_upload(img, "PNG", "image.png")
        mask_upload = TestHelper.pil_to_upload(mask.convert("RGB"), "PNG", "mask.png")
        
        validated_img = validate_upload(img_upload, cfg)
        validated_mask = validate_mask(mask_upload, validated_img.size, cfg)
        
        svc = InpaintingService(cfg)
        result = svc.run(validated_img, validated_mask, algorithm="telea", radius=3, max_edge=256)
        
        self.assertEqual(result.output_image.size, validated_img.size)
        self.assertTrue(result.meta["masked_pixels"] > 0)

    def test_with_real_test_images(self):
        test_dir = os.path.dirname(__file__)
        origin_path = os.path.join(test_dir, 'inpaint_case_1_origin.png')
        lack_path = os.path.join(test_dir, 'inpaint_case_1_lack.png')
        
        if os.path.exists(origin_path) and os.path.exists(lack_path):
            cfg = AppConfig()
            origin_img = Image.open(origin_path)
            lack_img = Image.open(lack_path)
            
            origin_upload = TestHelper.pil_to_upload(origin_img, "PNG", "inpaint_case_1_origin.png")
            lack_upload = TestHelper.pil_to_upload(lack_img, "PNG", "inpaint_case_1_lack.png")
            
            validated_origin = validate_upload(origin_upload, cfg)
            validated_mask = validate_mask(lack_upload, validated_origin.size, cfg)
            
            svc = InpaintingService(cfg)
            result = svc.run(validated_origin, validated_mask, algorithm="telea", radius=5, max_edge=512)
            
            self.assertEqual(result.output_image.size, validated_origin.size)
            self.assertTrue(result.meta["masked_pixels"] > 0)
        else:
            self.skipTest("Test images not found")

class SecurityTests(unittest.TestCase):
    def test_validate_upload_ok(self):
        img = TestHelper.create_sample_image()
        img_upload = TestHelper.pil_to_upload(img, "PNG", "image.png")
        cfg = AppConfig()
        validated_img = validate_upload(img_upload, cfg)
        self.assertEqual(validated_img.size, (64, 64))

    def test_reject_bad_filename(self):
        with self.assertRaises(SecurityError):
            sanitize_filename("../evil.png")

    def test_reject_non_image(self):
        bio = io.BytesIO(b"not an image")
        bio.name = "x.txt"
        cfg = AppConfig()
        with self.assertRaises(SecurityError):
            validate_upload(bio, cfg)

    def test_mask_size_mismatch(self):
        mask = TestHelper.create_sample_mask()
        mask_upload = TestHelper.pil_to_upload(mask.convert("RGB"), "PNG", "mask.png")
        img = Image.new("RGB", (128, 128), "white")
        cfg = AppConfig()
        with self.assertRaises(SecurityError):
            validate_mask(mask_upload, img.size, cfg)

def run_all_tests():
    print("开始运行所有测试...")
    
    test_suites = [
        ('单元测试', unittest.TestLoader().loadTestsFromTestCase(UnitTests)),
        ('系统测试', unittest.TestLoader().loadTestsFromTestCase(SystemTests)),
        ('验收测试', unittest.TestLoader().loadTestsFromTestCase(AcceptanceTests)),
        ('安全测试', unittest.TestLoader().loadTestsFromTestCase(SecurityTests))
    ]
    
    all_results = []
    
    for test_name, test_suite in test_suites:
        print(f"\n{'='*50}")
        print(f"运行 {test_name}...")
        print('='*50)
        
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(test_suite)
        
        all_results.append({
            'name': test_name,
            'result': result
        })
    
    print(f"\n{'='*60}")
    print("测试结果汇总")
    print('='*60)
    
    total_tests = 0
    total_failures = 0
    total_errors = 0
    
    for result_info in all_results:
        test_name = result_info['name']
        result = result_info['result']
        
        print(f"{test_name}:")
        print(f"  - 运行测试数: {result.testsRun}")
        print(f"  - 失败数: {len(result.failures)}")
        print(f"  - 错误数: {len(result.errors)}")
        print(f"  - 跳过数: {len(result.skipped)}")
        print()
        
        total_tests += result.testsRun
        total_failures += len(result.failures)
        total_errors += len(result.errors)
    
    print(f"总计:")
    print(f"  - 运行测试数: {total_tests}")
    print(f"  - 失败数: {total_failures}")
    print(f"  - 错误数: {total_errors}")
    
    if total_failures == 0 and total_errors == 0:
        print("\n✅ 所有测试通过！")
        return True
    else:
        print("\n❌ 部分测试失败或出错！")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
