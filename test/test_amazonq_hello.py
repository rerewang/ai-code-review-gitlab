#!/usr/bin/env python3
"""
最简单的Amazon Q CLI测试 - Hello对话
目标：调用CLI，完成一次hello对话，获取结果并打印
"""

import subprocess
import os
import sys

def test_amazonq_hello():
    """测试Amazon Q CLI的hello对话"""
    print("🧪 测试Amazon Q CLI Hello对话")
    print("-" * 50)
    
    cli_path = "q"  # Amazon Q CLI命令
    message = "Hello, please respond with just 'Hello back!'"
    
    print(f"📝 发送消息: {message}")
    print("🤖 调用Amazon Q CLI...")
    
    try:
        # 方法1: 使用stdin方式，避免交互模式
        process = subprocess.Popen(
            [cli_path, "chat"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # 发送消息并立即关闭stdin
        stdout, stderr = process.communicate(input=message + "\n", timeout=30)
        
        print("📤 原始输出:")
        print("STDOUT:", repr(stdout))
        print("STDERR:", repr(stderr))
        print("返回码:", process.returncode)
        
        if process.returncode == 0:
            print("\n✅ 调用成功!")
            print("🎯 响应内容:")
            print(stdout)
            return True
        else:
            print(f"\n❌ 调用失败，返回码: {process.returncode}")
            print(f"错误信息: {stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("\n⏰ 调用超时")
        return False
    except Exception as e:
        print(f"\n❌ 调用异常: {e}")
        return False

def test_amazonq_simple_command():
    """测试Amazon Q CLI简单命令"""
    print("\n🧪 测试Amazon Q CLI简单命令")
    print("-" * 50)
    
    try:
        # 测试版本命令
        result = subprocess.run(["q", "--version"], capture_output=True, text=True, timeout=10)
        print(f"版本信息: {result.stdout.strip()}")
        
        # 测试help命令
        result = subprocess.run(["q", "--help"], capture_output=True, text=True, timeout=10)
        print(f"帮助信息长度: {len(result.stdout)}字符")
        
        return True
    except Exception as e:
        print(f"❌ 简单命令测试失败: {e}")
        return False

def main():
    """主函数"""
    print("🚀 Amazon Q CLI 最简单测试")
    print("=" * 60)
    
    # 检查CLI是否可用
    try:
        result = subprocess.run(["q", "--version"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print(f"✅ Amazon Q CLI可用: {result.stdout.strip()}")
        else:
            print("❌ Amazon Q CLI不可用")
            return
    except Exception as e:
        print(f"❌ 无法找到Amazon Q CLI: {e}")
        return
    
    # 运行测试
    tests = [
        ("简单命令测试", test_amazonq_simple_command),
        ("Hello对话测试", test_amazonq_hello)
    ]
    
    results = []
    for name, test_func in tests:
        print(f"\n{'='*20} {name} {'='*20}")
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ 测试异常: {e}")
            results.append((name, False))
    
    # 输出结果
    print("\n" + "="*60)
    print("📊 测试结果")
    print("="*60)
    
    for name, result in results:
        status = "✅ 成功" if result else "❌ 失败"
        print(f"{name:15}: {status}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    print(f"\n总计: {passed}/{total} 通过")
    
    if passed > 0:
        print("\n🎉 基本功能正常，可以继续开发集成功能")
    else:
        print("\n⚠️ 需要检查Amazon Q CLI配置")

if __name__ == "__main__":
    main()
