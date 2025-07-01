# @cursor start
# AI代码审查GitLab机器人配置文件模板
# 复制此文件为 config.py 并填入你的真实配置

# ==================== GitLab配置 ====================
GITLAB_URL = "https://gitlab.com"  # GitLab服务器地址
GITLAB_TOKEN = "your-gitlab-token-here"  # GitLab访问令牌

# ==================== AI模型配置 ====================
# 支持的AI提供商: siliconflow, aliyun, openai, deepseek等
AI_PROVIDER = "siliconflow"  # 选择AI提供商

# 硅流配置 (SiliconFlow)
SILICONFLOW_API_URL = "https://api.siliconflow.cn/v1/chat/completions"
SILICONFLOW_API_KEY = "your-siliconflow-api-key-here"

# 阿里云通义千问配置 (Aliyun Qwen)
ALIYUN_API_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
ALIYUN_API_KEY = "your-aliyun-api-key-here"

# OpenAI配置
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"
OPENAI_API_KEY = "your-openai-api-key-here"

# 兼容旧配置
AI_API_URL = SILICONFLOW_API_URL
AI_MODEL = "Qwen/Qwen2.5-72B-Instruct"  # 硅流支持的模型
AI_API_KEY = SILICONFLOW_API_KEY

# ==================== 服务器配置 ====================
HOST = "0.0.0.0"
PORT = 8080

# ==================== 代码审查配置 ====================
# 需要审查的文件类型
REVIEW_FILE_TYPES = ['.py', '.js', '.ts', '.java', '.go', '.cpp', '.c', '.php']

# 忽略的文件类型
IGNORE_FILE_TYPES = ['package-lock.json', 'yarn.lock', 'mod.go']

# 最大处理文件数量
MAX_FILES = 50

# 上下文代码行数
CONTEXT_LINES = 5

# ==================== 审查提示词 ====================
REVIEW_PROMPT = """
你是一位资深的代码审查专家。请对以下代码变更进行审查，并提供详细的建议。

请从以下方面进行审查：
1. 代码质量和可读性
2. 安全性问题
3. 性能优化
4. 最佳实践
5. 潜在的bug

请用中文回答，格式如下：

### 代码评分：XX分（0-100）

#### ✅ 优点：
- 优点1
- 优点2

#### ❌ 问题：
- 问题1
- 问题2

#### 💡 建议：
- 建议1
- 建议2

#### 🔧 修改建议：
```代码
修改后的代码示例
```

代码变更内容：
{code_changes}
"""
# @cursor end 