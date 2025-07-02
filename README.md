# AI代码审查GitLab机器人

基于AI的GitLab代码审查机器人，支持自动代码审查、上下文增强和行内评论功能。

## ✨ 功能特点

- 🤖 **自动审查**: MR创建时自动触发代码审查
- 🔍 **上下文增强**: 获取代码变更的完整上下文
- 📝 **行内评论**: 精确定位到具体代码行的评论
- 💬 **评论触发**: 支持关键词触发审查 (`/review`, `代码审查`等)
- ⚡ **高性能**: 响应时间从分钟级降低到秒级
- 🔄 **异步处理**: 即时反馈，后台异步执行

## 🚀 快速开始

### 1. 安装依赖
```bash
pip3 install -r requirements.txt
```

### 2. 配置环境变量
```bash
cp env.example .env
# 编辑 .env 文件，填入你的配置
```

### 3. 启动服务
```bash
python3 app.py
```

### 4. 配置GitLab Webhook
- URL: `http://your-server:8080/webhook`
- 事件: `Merge request events`, `Comments`

## 🔧 配置说明

### 支持的AI提供商
- **SiliconFlow** (推荐): 国内访问速度快
- **阿里云通义千问**: 中文支持好
- **OpenAI**: 全球通用
- **DeepSeek**: 专业代码模型

### 触发关键词
- `/review`
- `/ai-review`
- `ai review`
- `代码审查`
- `review code`
- `ai审查`
- `智能审查`

## 📝 审查结果示例

```
🤖 AI代码审查完成

### 代码评分：88分（0-100）

#### ✅ 优点：
- 代码结构清晰，函数职责单一
- 添加了日志记录，提升了系统可观测性

#### ❌ 问题：
- 缺少输入参数验证
- 日志记录可以更详细

#### 💡 建议：
- 添加参数类型和格式验证
- 增加更详细的日志信息

#### 💬 行内评论建议
- **app/services/user_service.py** (第10行): 建议添加参数验证...
```

## 🧪 测试

```bash
# 性能测试
python3 performance_test.py

# 功能测试
python3 test_context_and_inline.py
```

## 📚 文档

- [更新日志](docs/CHANGELOG.md)
- [v2.0性能优化说明](docs/v2.0-performance-optimization.md)

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📄 许可证

MIT License

---

**版本**: v2.0  
**维护者**: AI代码审查团队 