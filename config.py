import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# ==================== GitLab配置 ====================
GITLAB_URL = os.getenv("GITLAB_URL", "https://gitlab.com")
GITLAB_TOKEN = os.getenv("GITLAB_TOKEN", "your-gitlab-token-here")

# ==================== AI模型配置（简化版） ====================
# 支持的AI提供商: siliconflow, aliyun, openai, deepseek等
AI_PROVIDER = os.getenv("AI_PROVIDER", "siliconflow")

# 通用AI配置（用户只需要配置这一组）
AI_API_URL = os.getenv("AI_API_URL", "https://api.siliconflow.cn/v1/chat/completions")
AI_API_KEY = os.getenv("AI_API_KEY", "your-api-key-here")
AI_MODEL = os.getenv("AI_MODEL", "Qwen/Qwen2.5-72B-Instruct")

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