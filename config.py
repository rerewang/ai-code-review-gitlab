import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# ==================== GitLab配置 ====================
GITLAB_URL = os.getenv("GITLAB_URL", "https://gitlab.com")
GITLAB_TOKEN = os.getenv("GITLAB_TOKEN", "your-gitlab-token-here")

# ==================== AI模型配置 ====================
# 支持的AI提供商: siliconflow, aliyun, openai, deepseek等
AI_PROVIDER = os.getenv("AI_PROVIDER", "siliconflow")

# 硅流配置 (SiliconFlow)
SILICONFLOW_API_URL = os.getenv("SILICONFLOW_API_URL", "https://api.siliconflow.cn/v1/chat/completions")
SILICONFLOW_API_KEY = os.getenv("SILICONFLOW_API_KEY", "your-siliconflow-api-key-here")
SILICONFLOW_MODEL = os.getenv("SILICONFLOW_MODEL", "Qwen/Qwen2.5-72B-Instruct")

# 阿里云通义千问配置 (Aliyun Qwen)
ALIYUN_API_URL = os.getenv("ALIYUN_API_URL", "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation")
ALIYUN_API_KEY = os.getenv("ALIYUN_API_KEY", "your-aliyun-api-key-here")
ALIYUN_MODEL = os.getenv("ALIYUN_MODEL", "qwen2.5-72b-instruct")

# OpenAI配置
OPENAI_API_URL = os.getenv("OPENAI_API_URL", "https://api.openai.com/v1/chat/completions")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "your-openai-api-key-here")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")

# DeepSeek配置
DEEPSEEK_API_URL = os.getenv("DEEPSEEK_API_URL", "https://api.deepseek.com/v1/chat/completions")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "your-deepseek-api-key-here")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

# 根据AI_PROVIDER选择配置
if AI_PROVIDER == "siliconflow":
    AI_API_URL = SILICONFLOW_API_URL
    AI_API_KEY = SILICONFLOW_API_KEY
    AI_MODEL = SILICONFLOW_MODEL
elif AI_PROVIDER == "aliyun":
    AI_API_URL = ALIYUN_API_URL
    AI_API_KEY = ALIYUN_API_KEY
    AI_MODEL = ALIYUN_MODEL
elif AI_PROVIDER == "openai":
    AI_API_URL = OPENAI_API_URL
    AI_API_KEY = OPENAI_API_KEY
    AI_MODEL = OPENAI_MODEL
elif AI_PROVIDER == "deepseek":
    AI_API_URL = DEEPSEEK_API_URL
    AI_API_KEY = DEEPSEEK_API_KEY
    AI_MODEL = DEEPSEEK_MODEL
else:
    # 默认使用硅流
    AI_API_URL = SILICONFLOW_API_URL
    AI_API_KEY = SILICONFLOW_API_KEY
    AI_MODEL = SILICONFLOW_MODEL

# ==================== 服务器配置 ====================
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8080"))

# ==================== 代码审查配置 ====================
# 需要审查的文件类型
REVIEW_FILE_TYPES = ['.py', '.js', '.ts', '.java', '.go', '.cpp', '.c', '.php']

# 忽略的文件类型
IGNORE_FILE_TYPES = ['package-lock.json', 'yarn.lock', 'mod.go']

# 最大处理文件数量
MAX_FILES = 50

# 上下文代码行数
CONTEXT_LINES = 5

# ==================== 触发配置 ====================
# 评论触发关键词（不区分大小写）
REVIEW_TRIGGER_KEYWORDS = [
    '/review',
    '/ai-review', 
    'ai review',
    '代码审查',
    'review code',
    'ai审查',
    '智能审查'
]

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