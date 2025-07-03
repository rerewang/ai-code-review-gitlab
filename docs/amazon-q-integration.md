# Amazon Q 集成使用方法

本文档详细介绍如何将Amazon Q AI助手集成到GitLab代码审查机器人中，实现与AI的直接交互。

## 🎯 功能特点

- **直接交互**: 通过Amazon Q CLI直接与AI助手对话
- **智能审查**: 获得更准确、更专业的代码审查建议
- **上下文理解**: AI能理解完整的项目上下文和代码变更
- **行内评论**: 生成精确的行级评论建议
- **备用机制**: 如果Amazon Q不可用，自动回退到其他AI提供商

## 📋 前置条件

### 1. 安装Amazon Q CLI

```bash
# 安装Amazon Q CLI (根据你的系统选择)
# macOS
brew install amazon-q

# 或者从官网下载安装包
# https://aws.amazon.com/q/developer/
```

### 2. 配置认证

```bash
# 配置AWS凭证
aws configure

# 或者设置环境变量
export AWS_ACCESS_KEY_ID=your-access-key
export AWS_SECRET_ACCESS_KEY=your-secret-key
export AWS_DEFAULT_REGION=us-east-1

# 验证Amazon Q CLI
q doctor
```

## ⚙️ 配置步骤

### 1. 环境变量配置

在 `.env` 文件中添加以下配置：

```bash
# ==================== AI模型配置 ====================
# 设置AI提供商为Amazon Q
AI_PROVIDER=amazonq

# 启用Amazon Q CLI模式
AMAZONQ_USE_CLI=true
AMAZONQ_CLI_PATH=q

# ==================== GitLab配置 ====================
GITLAB_URL=https://your-gitlab-server.com
GITLAB_TOKEN=your-gitlab-token-here

# ==================== 服务器配置 ====================
HOST=0.0.0.0
PORT=8080
```

### 2. 验证配置

运行完整测试脚本：

```bash
python3 test_amazonq_cli.py
```

测试脚本会检查：
- ✅ Amazon Q CLI安装状态
- ✅ 认证配置
- ✅ 基本功能
- ✅ AI客户端集成
- ✅ 代码审查器集成

## 🚀 使用方法

### 1. 启动服务

```bash
python3 app.py
```

服务启动后会显示：
```
🚀 启动AI代码审查服务（性能优化版），监听 0.0.0.0:8080
```

### 2. 配置GitLab Webhook

在GitLab项目设置中添加Webhook：
- **URL**: `http://your-server:8080/webhook`
- **触发事件**: 
  - ✅ Merge request events
  - ✅ Comments

### 3. 触发代码审查

#### 自动触发
- 创建Merge Request时自动触发审查

#### 手动触发
在MR评论中输入以下任一关键词：
- `/review`
- `/ai-review`
- `ai review`
- `代码审查`
- `review code`
- `ai审查`
- `智能审查`

## 📝 审查流程

### 1. 触发阶段
```
GitLab MR创建/评论 → Webhook → AI代码审查服务
```

### 2. 处理阶段
```
代码变更获取 → 上下文分析 → Amazon Q AI审查 → 结果格式化
```

### 3. 反馈阶段
```
审查结果 → GitLab评论 → 行内评论 → 完成通知
```

## 🎨 审查结果示例

Amazon Q会提供详细的审查结果：

```markdown
🤖 **AI智能分析完成**

### 🎯 代码评分：85分（0-100分）

### ✅ 优点
- 代码结构清晰，函数职责单一
- 添加了适当的日志记录
- 遵循了Python编码规范

### ❌ 发现的问题
- 缺少输入参数验证，可能导致运行时错误
- 数据库查询未使用参数化查询，存在SQL注入风险
- 异常处理不够完善，可能导致程序崩溃

### 💡 改进建议
- 添加输入参数类型检查和格式验证
- 使用ORM或参数化查询防止SQL注入
- 增加try-catch异常处理机制
- 添加单元测试覆盖关键逻辑

### 🔧 代码修改示例
```python
# 修改前
def get_user(user_id):
    query = f"SELECT * FROM users WHERE id = {user_id}"
    return db.execute(query)

# 修改后
def get_user(user_id: int) -> Optional[User]:
    if not isinstance(user_id, int) or user_id <= 0:
        raise ValueError("Invalid user_id")
    
    try:
        query = "SELECT * FROM users WHERE id = %s"
        return db.execute(query, (user_id,))
    except Exception as e:
        logger.error(f"Failed to get user {user_id}: {e}")
        return None
```

### 📋 总结
代码整体质量良好，主要需要加强安全性和错误处理。

---
*由AI代码审查机器人自动生成*

✅ 已添加 3 个AI行内评论
📊 **审查统计**: 已完成 1 次审查，平均耗时 15.2秒
```

## 🔧 故障排除

### 常见问题

#### 1. Amazon Q CLI不可用
```bash
❌ 找不到Amazon Q CLI工具: q，请检查安装和配置
```

**解决方案**:
- 检查CLI是否正确安装: `which q`
- 验证PATH环境变量
- 重新安装Amazon Q CLI

#### 2. 认证失败
```bash
❌ AI助手调用失败: Authentication failed
```

**解决方案**:
- 检查AWS凭证配置: `aws configure list`
- 验证IAM权限
- 运行认证检查: `q doctor`

#### 3. 响应超时
```bash
⏰ AI助手响应超时，代码变更可能过于复杂
```

**解决方案**:
- 减少单次审查的文件数量
- 检查网络连接
- 增加超时时间配置

#### 4. 备用机制触发
```bash
🔄 回退到备用AI客户端...
```

**说明**: 这是正常的容错机制，当Amazon Q不可用时会自动使用其他AI提供商。

### 调试模式

启用详细日志：

```bash
# 在.env中添加
LOG_LEVEL=DEBUG

# 或者直接运行
DEBUG=true python3 app.py
```

## 📊 性能优化

### 1. 缓存机制
- 文件内容缓存，减少重复API调用
- 智能缓存清理，避免内存泄漏

### 2. 批量处理
- 多文件变更批量分析
- 行内评论批量生成

### 3. 异步执行
- 即时反馈，后台异步处理
- 避免Webhook超时

## 🔒 安全考虑

### 1. 凭证管理
- 使用环境变量存储敏感信息
- 定期轮换API密钥
- 避免在代码中硬编码凭证

### 2. 网络安全
- 使用HTTPS传输
- 验证Webhook签名
- 限制访问IP范围

### 3. 数据隐私
- 代码内容仅用于审查目的
- 不存储敏感代码信息
- 遵循数据保护法规

## 📈 监控和维护

### 1. 日志监控
```bash
# 查看服务日志
tail -f ai_code_review.log

# 查看错误日志
grep "ERROR" ai_code_review.log
```

### 2. 性能监控
- 审查响应时间
- API调用频率
- 错误率统计

### 3. 定期维护
- 更新Amazon Q CLI版本
- 清理日志文件
- 检查配置有效性

## 🤝 最佳实践

### 1. 代码审查
- 专注于安全性、性能和可维护性
- 提供建设性的改进建议
- 保持审查标准的一致性

### 2. 团队协作
- 培训团队成员使用触发关键词
- 建立代码审查流程规范
- 定期收集反馈和改进

### 3. 持续改进
- 监控审查质量和效果
- 根据反馈调整提示词
- 优化审查规则和配置

---

## 📞 技术支持

如果遇到问题，请：

1. 查看本文档的故障排除部分
2. 运行完整测试: `python3 test_amazonq_cli.py`
3. 检查日志文件获取详细错误信息
4. 提交Issue到项目仓库

**版本**: v2.0  
**更新时间**: 2025-01-03  
**维护者**: AI代码审查团队
