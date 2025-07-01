#!/bin/bash

echo "🚀 启动AI代码审查GitLab机器人..."

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到Python3，请先安装Python3"
    exit 1
fi

# 检查配置文件
if [ ! -f "config.py" ]; then
    echo "❌ 错误: 配置文件 config.py 不存在"
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
try:
    from config import GITLAB_TOKEN, AI_API_KEY
    print('✅ 配置文件加载成功')
    if GITLAB_TOKEN == 'your-gitlab-token-here':
        print('⚠️  警告: GitLab token 还是默认值，请修改配置')
    else:
        print('✅ GitLab token 已配置')
    if AI_API_KEY == 'your-api-key-here':
        print('⚠️  警告: AI API key 还是默认值，请修改配置')
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