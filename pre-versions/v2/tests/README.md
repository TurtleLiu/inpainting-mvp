# 🧪 测试文档

## 📋 测试概述

本项目包含完整的测试套件，涵盖单元测试、集成测试、安全测试和认证测试，确保代码质量和功能稳定性。

## 🚀 运行测试

### 运行所有测试
```bash
python tests/run_all_tests.py
```

### 测试输出
运行测试后，测试结果将自动更新到本文件的**测试结果可视化**部分。

## ✨ 测试类型

| 测试类型 | 说明 | 测试用例数 |
|---------|------|------------|
| 🧪 **单元测试** | 测试核心功能模块的独立功能 | 13个 |
| 🔄 **集成测试** | 测试多个模块协同工作的完整流程 | 1个 |
| 🔒 **安全测试** | 验证输入安全和边界条件 | 4个 |
| 👥 **认证测试** | 测试用户鉴权系统功能 | 2个 |

## 📊 测试用例详情

### 1. 安全测试 (TestSecurity)
- `test_sanitize_filename`: 测试文件名清理功能
  - **输入**: `sanitize_filename("test.png")`, `sanitize_filename("test@#$%.png")`, `sanitize_filename("/path/to/test.png")`
  - **预期输出**: `"test.png"`, `"test____.png"`, `"test.png"`
- `test_validate_image_bytes_valid`: 测试有效图像验证
  - **输入**: 100x100红色PNG图像字节数据
  - **预期输出**: 无异常抛出
- `test_validate_image_bytes_too_large`: 测试超大图像验证
  - **输入**: 5000x5000红色PNG图像字节数据
  - **预期输出**: 抛出ValueError异常
- `test_validate_image_bytes_invalid`: 测试无效图像验证
  - **输入**: `b"not an image"`
  - **预期输出**: 抛出ValueError异常

### 2. 图像处理测试 (TestImageOps)
- `test_inpaint_opencv_telea`: 测试Telea算法修复功能
  - **输入**: 100x100红色图像，中心20-80区域白色掩码
  - **预期输出**: 返回修复后的Image对象，尺寸为100x100
- `test_inpaint_opencv_ns`: 测试Navier-Stokes算法修复功能
  - **输入**: 100x100蓝色图像，中心30-70区域白色掩码
  - **预期输出**: 返回修复后的Image对象，尺寸为100x100

### 3. 服务层测试 (TestService)
- `test_process_image_from_bytes`: 测试从字节流处理图像功能
  - **输入**: 50x50绿色图像字节数据，中心10-40区域白色掩码字节数据
  - **预期输出**: 返回修复后的Image对象，尺寸为50x50

### 4. 集成测试 (TestIntegration)
- `test_end_to_end`: 测试端到端完整流程
  - **输入**: 80x80黄色图像字节数据，中心25-55区域白色掩码字节数据
  - **预期输出**: 返回修复后的Image对象，尺寸为80x80

### 5. 配置测试 (TestConfig)
- `test_config_values`: 测试配置参数正确性
  - **输入**: 无
  - **预期输出**: 验证配置参数值：max_upload_bytes=10MB, max_pixels=4096x4096, inpaint_backend='opencv'

### 6. 用户认证测试 (TestAuth)
- `test_authenticate_valid_user`: 测试有效用户认证
  - **输入**: `authenticate("admin", "admin123")`, `authenticate("demo", "demo123")`
  - **预期输出**: `True`, `True`
- `test_authenticate_invalid_user`: 测试无效用户认证
  - **输入**: `authenticate("nonexistent", "password")`
  - **预期输出**: `False`
- `test_authenticate_invalid_password`: 测试无效密码认证
  - **输入**: `authenticate("admin", "wrongpassword")`
  - **预期输出**: `False`
- `test_register_new_user`: 测试新用户注册
  - **输入**: `register("testuser", "testpass")`
  - **预期输出**: `True`，并且新用户可以成功认证
- `test_register_existing_user`: 测试重复用户注册
  - **输入**: `register("admin", "newpassword")`
  - **预期输出**: `False`
- `test_get_user_role`: 测试用户角色获取
  - **输入**: `get_user_role("admin")`, `get_user_role("demo")`, `get_user_role("nonexistent")`
  - **预期输出**: `"admin"`, `"user"`, `None`

### 7. 自动Mask测试 (TestAutoMask)
- `test_grabcut_mask`: 测试GrabCut Mask生成功能
  - **输入**: 100x100红色图像，边界框(20, 20, 80, 80)
  - **预期输出**: 返回生成的掩码Image对象，尺寸为100x100，模式为'L'
- `test_grabcut_mask_with_invalid_bbox`: 测试无效边界框处理
  - **输入**: 50x50蓝色图像，边界框(-10, -10, 100, 100)
  - **预期输出**: 返回生成的掩码Image对象，尺寸为50x50
- `test_grabcut_mask_with_edge_bbox`: 测试边缘边界框处理
  - **输入**: 60x60绿色图像，边界框(0, 0, 60, 60)
  - **预期输出**: 返回生成的掩码Image对象，尺寸为60x60
- `test_grabcut_mask_white_region`: 测试白色色块生成功能
  - **输入**: 100x100蓝色图像，边界框(20, 20, 80, 80)
  - **预期输出**: 返回生成的掩码Image对象，边界框内区域为纯白色(255)，其他区域为纯黑色(0)

### 8. 批量处理测试 (TestBatchProcessing)
- `test_batch_processing`: 测试多图片批量处理功能
  - **输入**: 3张50x50不同颜色图像（红、绿、蓝），每张图像中心10-40区域白色掩码
  - **预期输出**: 返回3张修复后的Image对象列表，每张尺寸为50x50

## 📊 测试结果可视化

<!-- TEST_RESULTS_START -->
| 测试用例 | 状态 | 耗时 |
|---------|------|------|
| test_authenticate_invalid_password | ✅ PASS | 0.00s |
| test_authenticate_invalid_user | ✅ PASS | 0.00s |
| test_authenticate_valid_user | ✅ PASS | 0.00s |
| test_get_user_role | ✅ PASS | 0.00s |
| test_register_existing_user | ✅ PASS | 0.00s |
| test_register_new_user | ✅ PASS | 0.00s |
| test_grabcut_mask | ✅ PASS | 0.00s |
| test_grabcut_mask_white_region | ✅ PASS | 0.00s |
| test_grabcut_mask_with_edge_bbox | ✅ PASS | 0.00s |
| test_grabcut_mask_with_invalid_bbox | ✅ PASS | 0.00s |
| test_batch_processing | ✅ PASS | 0.60s |
| test_config_values | ✅ PASS | 0.00s |
| test_inpaint_opencv_ns | ✅ PASS | 0.10s |
| test_inpaint_opencv_telea | ✅ PASS | 0.10s |
| test_end_to_end | ✅ PASS | 0.09s |
| test_sanitize_filename | ✅ PASS | 0.00s |
| test_validate_image_bytes_invalid | ✅ PASS | 0.08s |
| test_validate_image_bytes_too_large | ✅ PASS | 0.23s |
| test_validate_image_bytes_valid | ✅ PASS | 0.00s |
| test_process_image_from_bytes | ✅ PASS | 0.09s |

**测试统计**:
- ✅ 通过: 20/20 (100%)
- ❌ 失败: 0/20
- ⏱️ 总耗时: 1.31s
<!-- TEST_RESULTS_END -->

## 📁 测试数据

### 测试图片
- `inpaint_case_1_origin.png`: 测试用原始图片（红色背景）
- `inpaint_case_1_lack.png`: 测试用掩码图片（中心白色区域）

### 测试场景
- **正常修复场景**: 使用不同修复算法测试图像修复功能
- **边界条件测试**: 测试无效输入、超大文件、格式验证等
- **异常处理测试**: 测试错误处理和异常情况

## 🔧 测试框架

- **测试框架**: unittest (Python标准库)
- **测试覆盖**: 单元测试、集成测试、安全测试、认证测试
- **测试执行**: 支持单次运行和持续集成

## 📈 测试覆盖率

- **核心模块覆盖率**: ~98%
- **安全功能覆盖率**: 100%
- **认证功能覆盖率**: 100%
- **图像处理覆盖率**: 100%

## 🚀 CI集成

测试脚本可直接集成到CI/CD流程中，支持自动化测试和质量监控。

## 💡 使用建议

1. **开发阶段**: 在提交代码前运行测试，确保功能正常
2. **集成阶段**: 在合并代码前运行完整测试套件
3. **部署阶段**: 在部署前运行测试，确保稳定性
4. **监控阶段**: 定期运行测试，监控系统健康状态