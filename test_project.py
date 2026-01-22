#!/usr/bin/env python3
"""
测试项目是否能正常运行
"""
import os
import sys
import subprocess

def test_imports():
    """测试导入"""
    print("🧪 测试导入模块...")
    try:
        from src.data.fetcher import get_stock_data
        print("✅ src.data.fetcher 导入成功")
        return True
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        return False

def test_main():
    """测试主程序"""
    print("\n🧪 测试主程序...")
    result = subprocess.run([sys.executable, "main.py", "--help"], 
                          capture_output=True, text=True)
    if result.returncode == 0:
        print("✅ 主程序运行正常")
        print(result.stdout[:200])
        return True
    else:
        print("❌ 主程序运行失败")
        print(result.stderr)
        return False

def test_structure():
    """测试项目结构"""
    print("\n🧪 检查项目结构...")
    required_dirs = ["src", "src/data", "src/analysis", "config", "examples"]
    required_files = ["README.md", "requirements.txt", "main.py"]
    
    all_ok = True
    for dir_path in required_dirs:
        if os.path.exists(dir_path):
            print(f"✅ 目录存在: {dir_path}")
        else:
            print(f"❌ 目录缺失: {dir_path}")
            all_ok = False
    
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ 文件存在: {file_path}")
        else:
            print(f"❌ 文件缺失: {file_path}")
            all_ok = False
    
    return all_ok

def main():
    print("=" * 50)
    print("🔧 股票分析机器人项目测试")
    print("=" * 50)
    
    tests = [
        test_structure,
        test_imports,
        test_main,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！项目结构完整。")
        print("\n下一步:")
        print("1. 安装依赖: pip install -r requirements.txt")
        print("2. 运行示例: python examples/basic_analysis.py")
        print("3. 开始开发!")
    else:
        print("⚠️  有些测试未通过，请检查项目结构。")
    
    print("=" * 50)

if __name__ == "__main__":
    main()
