# @cursor start
# AI代码审查GitLab机器人

一个简单的AI代码审查工具，自动审查GitLab的Merge Request并提供建议。

## 🎯 功能特点

- 🤖 自动审查代码变更
- 📝 提供详细的审查建议
- 🔗 支持多种大模型（GPT、DeepSeek等）
- 📤 自动发送评论到GitLab
- ⚡ 异步处理，不阻塞webhook

## 🏗️ 项目结构

```
ai-code-review-gitlab/
├── app.py              # 主程序入口
├── config.py           # 配置文件
├── gitlab_client.py    # GitLab API客户端
├── ai_client.py        # AI大模型客户端
├── code_reviewer.py    # 代码审查逻辑
├── requirements.txt    # 依赖包
└── README.md          # 说明文档
```

## 🚀 快速开始

1. 安装依赖：`pip install -r requirements.txt`
2. 配置 `config.py`
3. 运行：`python app.py`
4. 在GitLab中配置webhook：`http://your-server:8080/webhook`

## 📝 配置说明

在 `config.py` 中配置：
- GitLab访问令牌
- 大模型API密钥
- 服务器地址等
# @cursor end 