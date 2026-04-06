"""
测试高保真管线
"""
import cv2
import numpy as np
from controllers.hifi_pipeline import HiFiPipeline


def test_hifi_pipeline():
    """测试高保真管线"""
    print("=" * 60)
    print("高保真管线测试")
    print("=" * 60)
    
    # 初始化管线
    pipeline = HiFiPipeline()
    status = pipeline.initialize()
    
    print("\n模块状态:")
    for module, available in status.items():
        status_str = "✓ 可用" if available else "✗ 不可用"
        print(f"  {module}: {status_str}")
    
    print("\n模型信息:")
    model_info = pipeline.get_model_info()
    for module, info in model_info.items():
        print(f"  {module}: {info}")
    
    print("\n管线可用性:", "✓ 可用" if pipeline.is_available() else "✗ 不可用")
    
    # 如果有测试图片，进行处理测试
    test_image_path = "test_id_photos/test.jpg"
    try:
        image = cv2.imread(test_image_path)
        if image is not None:
            print(f"\n测试图片: {test_image_path}")
            print(f"图片尺寸: {image.shape[1]}x{image.shape[0]}")
            
            # 处理图片
            result, info = pipeline.process(
                image,
                bg_color=(255, 255, 255),  # 白色背景
                use_codeformer=False
            )
            
            print("\n处理步骤:")
            for step in info['steps']:
                print(f"  ✓ {step}")
            
            if info['warnings']:
                print("\n警告:")
                for warning in info['warnings']:
                    print(f"  ⚠ {warning}")
            
            if info['face_info']:
                print("\n人脸信息:")
                print(f"  边界框: {info['face_info']['bbox']}")
                print(f"  关键点数: {info['face_info']['landmarks']}")
                print(f"  身份特征: {'已提取' if info['face_info']['has_embedding'] else '未提取'}")
            
            # 保存结果
            output_path = "test_hifi_output.jpg"
            cv2.imwrite(output_path, result)
            print(f"\n结果已保存: {output_path}")
        else:
            print(f"\n测试图片不存在: {test_image_path}")
    except Exception as e:
        print(f"\n测试图片处理失败: {e}")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    test_hifi_pipeline()
