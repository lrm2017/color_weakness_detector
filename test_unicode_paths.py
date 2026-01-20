#!/usr/bin/env python3
"""
测试中文路径处理功能
"""

import shutil
from pathlib import Path
from image_utils import imread_unicode, imwrite_unicode
from color_vision_filters import ColorVisionFilters, FilterType
from multi_channel_color_detector import MultiChannelColorDetector


def test_unicode_paths():
    """测试中文路径处理"""
    print("=== 中文路径处理测试 ===\n")
    
    # 创建测试目录
    test_dir = Path("test_results/中文路径测试")
    test_dir.mkdir(parents=True, exist_ok=True)
    
    # 源图像
    source_image = "downloaded_images/俞自萍第五版/001.jpg"
    
    if not Path(source_image).exists():
        print(f"错误：源图像不存在 {source_image}")
        return False
    
    print(f"源图像: {source_image}")
    
    # 测试1：复制到中文路径
    chinese_path = test_dir / "测试图像_001.jpg"
    try:
        # 使用我们的函数读取和保存
        image = imread_unicode(source_image)
        if image is not None:
            success = imwrite_unicode(chinese_path, image)
            if success:
                print(f"✓ 成功复制到中文路径: {chinese_path}")
            else:
                print(f"✗ 复制到中文路径失败")
                return False
        else:
            print(f"✗ 读取源图像失败")
            return False
    except Exception as e:
        print(f"✗ 复制过程出错: {e}")
        return False
    
    # 测试2：从中文路径读取并应用滤镜
    try:
        print(f"\n测试从中文路径读取: {chinese_path}")
        image = imread_unicode(chinese_path)
        if image is not None:
            print(f"✓ 成功从中文路径读取图像，尺寸: {image.shape}")
            
            # 应用滤镜
            filtered = ColorVisionFilters.apply_filter(image, FilterType.PROTANOPIA_ASSIST)
            filter_output = test_dir / "红色盲辅助滤镜_结果.jpg"
            
            if imwrite_unicode(filter_output, filtered):
                print(f"✓ 滤镜处理成功，保存到: {filter_output}")
            else:
                print(f"✗ 滤镜结果保存失败")
                return False
        else:
            print(f"✗ 从中文路径读取失败")
            return False
    except Exception as e:
        print(f"✗ 滤镜处理出错: {e}")
        return False
    
    # 测试3：多通道检测
    try:
        print(f"\n测试多通道检测...")
        detector = MultiChannelColorDetector()
        
        # 红绿通道测试
        output_base = test_dir / "多通道测试结果"
        result_image, data = detector.test_red_green_channel(chinese_path, output_base)
        
        print(f"✓ 多通道检测完成")
        print(f"  红色比例: {data['red_ratio']:.1%}")
        print(f"  绿色比例: {data['green_ratio']:.1%}")
        
    except Exception as e:
        print(f"✗ 多通道检测出错: {e}")
        return False
    
    # 测试4：验证生成的文件
    print(f"\n验证生成的文件:")
    generated_files = list(test_dir.glob("*"))
    for file_path in generated_files:
        if file_path.is_file():
            print(f"  ✓ {file_path.name}")
    
    print(f"\n=== 中文路径测试完成 ===")
    print(f"所有测试通过！中文路径处理正常工作。")
    return True


def test_various_encodings():
    """测试各种编码的文件名"""
    print("\n=== 多语言文件名测试 ===")
    
    test_dir = Path("test_results/多语言测试")
    test_dir.mkdir(parents=True, exist_ok=True)
    
    source_image = "downloaded_images/俞自萍第五版/001.jpg"
    if not Path(source_image).exists():
        print("跳过多语言测试：源图像不存在")
        return
    
    # 各种语言的文件名
    test_names = [
        "中文测试_简体.jpg",
        "中文測試_繁體.jpg", 
        "日本語テスト.jpg",
        "한국어_테스트.jpg",
        "Русский_тест.jpg",
        "العربية_اختبار.jpg",
        "Ελληνικά_δοκιμή.jpg"
    ]
    
    image = imread_unicode(source_image)
    if image is None:
        print("无法读取源图像")
        return
    
    success_count = 0
    for name in test_names:
        try:
            output_path = test_dir / name
            if imwrite_unicode(output_path, image):
                # 验证能否读回
                test_read = imread_unicode(output_path)
                if test_read is not None:
                    print(f"✓ {name}")
                    success_count += 1
                else:
                    print(f"✗ {name} (读取失败)")
            else:
                print(f"✗ {name} (保存失败)")
        except Exception as e:
            print(f"✗ {name} (错误: {e})")
    
    print(f"\n多语言测试结果: {success_count}/{len(test_names)} 成功")


if __name__ == "__main__":
    success = test_unicode_paths()
    if success:
        test_various_encodings()
    else:
        print("基础中文路径测试失败，跳过其他测试")