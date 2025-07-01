#!/bin/bash

echo "🚀 启动AI代码审查GitLab机器人..."

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到Python3，请先安装Python3"
    exit 1
fi

# 检查环境变量文件
if [ ! -f ".env" ]; then
    echo "❌ 错误: 环境变量文件 .env 不存在"
    echo "💡 请先复制 env.example 为 .env 并填入你的配置"
    echo "   cp env.example .env"
    exit 1
fi

# 检查依赖
if [ ! -f "requirements.txt" ]; then
    echo "❌ 错误: requirements.txt 不存在"
    exit 1
fi

# 安装依赖
echo "📦 安装Python依赖..."
pip3 install -r requirements.txt

# 检查配置
echo "🔍 检查配置..."
python3 -c "
import sys
import os
from dotenv import load_dotenv

try:
    load_dotenv()
    gitlab_token = os.getenv('GITLAB_TOKEN')
    ai_provider = os.getenv('AI_PROVIDER', 'siliconflow')
    
    if ai_provider == 'siliconflow':
        api_key = os.getenv('SILICONFLOW_API_KEY')
    elif ai_provider == 'aliyun':
        api_key = os.getenv('ALIYUN_API_KEY')
    elif ai_provider == 'openai':
        api_key = os.getenv('OPENAI_API_KEY')
    else:
        api_key = os.getenv('SILICONFLOW_API_KEY')
    
    print('✅ 环境变量加载成功')
    print(f'🔧 AI提供商: {ai_provider}')
    
    if not gitlab_token or gitlab_token == 'your-gitlab-token-here':
        print('⚠️  警告: GitLab token 未配置或还是默认值')
    else:
        print('✅ GitLab token 已配置')
        
    if not api_key or api_key == 'your-siliconflow-api-key-here':
        print('⚠️  警告: AI API key 未配置或还是默认值')
    else:
        print('✅ AI API key 已配置')
        
except Exception as e:
    print(f'❌ 配置检查失败: {e}')
    sys.exit(1)
"

if [ $? -ne 0 ]; then
    echo "❌ 配置检查失败，请检查配置文件"
    exit 1
fi

# 启动服务
echo "🌟 启动Web服务..."
echo "📍 服务地址: http://0.0.0.0:8080"
echo "🔗 Webhook地址: http://your-server-ip:8080/webhook"
echo "📝 日志输出:"
echo "----------------------------------------"

python3 app.py 