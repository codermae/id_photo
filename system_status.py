"""
系统状态检查和诊断工具
"""
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from utils.face_recognition_manager import get_face_recognition_manager, print_status as print_face_status
from fix_database_and_setup import check_and_fix_database, check_dependencies

def print_header(title):
    """打印标题"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

def main():
    """主函数"""
    print("\n")
    print("╔" + "="*68 + "╗")
    print("║" + " "*68 + "║")
    print("║" + "  ID证照片系统 - 完整系统诊断".center(68) + "║")
    print("║" + " "*68 + "║")
    print("╚" + "="*68 + "╝")
    
    # 1. 数据库检查
    print_header("1. 数据库状态")
    db_ok = check_and_fix_database()
    
    # 2. 依赖检查
    print_header("2. 依赖库状态")
    required_ok, face_recognition_ok = check_dependencies()
    
    # 3. 人脸识别状态
    print_header("3. 人脸识别系统")
    manager = get_face_recognition_manager()
    status = manager.get_status()
    
    print(f"\n模式: {status['mode']}")
    print(f"描述: {status['description']}")
    print(f"就绪: {'✓ 是' if status['is_ready'] else '✗ 否'}")
    
    # 4. 综合诊断
    print_header("4. 综合诊断报告")
    
    print(f"\n[数据库]")
    print(f"  状态: {'✓ 正常' if db_ok else '✗ 需要修复'}")
    
    print(f"\n[必需依赖]")
    print(f"  状态: {'✓ 完整' if required_ok else '✗ 缺失'}")
    
    print(f"\n[人脸识别]")
    print(f"  状态: {'✓ 可用' if status['is_ready'] else '⚠ 不可用'}")
    print(f"  模式: {status['mode']}")
    
    # 5. 建议
    print_header("5. 建议和后续步骤")
    
    if not db_ok:
        print("\n[数据库问题]")
        print("  • 数据库需要修复")
        print("  • 运行: python fix_database_and_setup.py")
    
    if not required_ok:
        print("\n[依赖问题]")
        print("  • 缺少必需的依赖库")
        print("  • 运行: pip install -r requirements.txt")
    
    if not status['is_ready']:
        print("\n[人脸识别问题]")
        print("  • 人脸识别功能不可用")
        print("  • 要启用人脸识别，请按照以下步骤:")
        print("    1. 从 https://cmake.org 下载并安装 CMake")
        print("    2. 确保 CMake 已添加到 PATH")
        print("    3. 运行: pip install face-recognition")
        print("  • 详细说明: 查看 INSTALL_FACE_RECOGNITION_GUIDE.md")
    
    # 6. 最终状态
    print_header("6. 最终状态")
    
    all_ok = db_ok and required_ok
    
    if all_ok:
        print("\n[✓] 系统已准备就绪！")
        print("\n可以运行以下命令启动系统:")
        print("  python main.py")
        
        if status['is_ready']:
            print("\n[✓] 人脸识别功能已启用")
        else:
            print("\n[⚠] 人脸识别功能未启用（可选功能）")
            print("    系统可以正常运行，但防重复采集功能将被禁用")
    else:
        print("\n[✗] 系统需要修复")
        print("\n请按照上述建议进行修复，然后重新运行此诊断工具")
    
    print("\n" + "="*70 + "\n")
    
    return 0 if all_ok else 1

if __name__ == '__main__':
    sys.exit(main())
