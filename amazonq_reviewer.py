#!/usr/bin/env python3
"""
Amazon Q 代码审查客户端
专门用于与Amazon Q AI助手进行代码审查交互
"""

import subprocess
import os
import json
import time
from datetime import datetime
from typing import Dict, List, Optional

class AmazonQReviewer:
    """Amazon Q代码审查客户端"""
    
    def __init__(self, cli_path="q"):
        self.cli_path = cli_path
        self.review_history = []
        
    def _validate_cli(self):
        """验证Amazon Q CLI是否可用"""
        try:
            result = subprocess.run(
                [self.cli_path, "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    def _send_review_request(self, prompt: str) -> str:
        """发送代码审查请求给Amazon Q（优化版本）"""
        try:
            print(f"🤖 正在请求AI代码审查...")
            
            # 简化提示词，提高响应速度
            if len(prompt) > 3000:
                prompt = prompt[:3000] + "\n\n请基于以上内容进行简要审查。"
            
            # 方法1：尝试直接调用
            result = subprocess.run(
                f'echo "{prompt}" | {self.cli_path} chat',
                shell=True,
                capture_output=True,
                text=True,
                timeout=45,  # 减少超时时间
                env=dict(os.environ, SHELL='/bin/zsh')
            )
            
            if result.returncode == 0 and result.stdout.strip():
                response = result.stdout.strip()
                cleaned = self._clean_response(response)
                if cleaned and len(cleaned) > 10:  # 确保有实际内容
                    return cleaned
            
            # 方法2：如果失败，使用智能分析
            print("🔄 使用智能分析模式...")
            return self._intelligent_analysis(prompt)
                
        except subprocess.TimeoutExpired:
            print("⏰ 响应超时，使用快速分析...")
            return self._quick_analysis(prompt)
        except Exception as e:
            print(f"❌ 调用异常，使用备用分析: {str(e)}")
            return self._fallback_analysis(prompt)
    
    def _intelligent_analysis(self, prompt: str) -> str:
        """智能代码分析（不依赖外部API）"""
        # 从提示词中提取代码内容
        code_content = ""
        if "代码变更内容：" in prompt:
            code_content = prompt.split("代码变更内容：")[-1]
        elif "```" in prompt:
            # 提取代码块
            parts = prompt.split("```")
            for i, part in enumerate(parts):
                if i % 2 == 1:  # 奇数索引是代码块
                    code_content += part + "\n"
        
        issues = []
        suggestions = []
        score = 85  # 默认分数
        
        # 安全性检查
        if 'eval(' in code_content:
            issues.append("使用eval()函数存在代码注入风险")
            suggestions.append("使用json.loads()或ast.literal_eval()替代eval()")
            score -= 15
        
        if 'exec(' in code_content:
            issues.append("使用exec()函数存在安全风险")
            suggestions.append("避免使用exec()，寻找更安全的替代方案")
            score -= 15
        
        # SQL注入检查
        if any(sql_word in code_content.lower() for sql_word in ['select ', 'insert ', 'update ', 'delete ']):
            # 检查字符串格式化可能导致的SQL注入
            if ('"{' in code_content and '}"' in code_content) or ("'{" in code_content and "}'" in code_content):
                issues.append("可能存在SQL注入风险")
                suggestions.append("使用参数化查询或ORM防止SQL注入")
                score -= 10
        
        # 密码安全检查
        if any(pwd_word in code_content.lower() for pwd_word in ['password', 'passwd', 'pwd']):
            if 'plain' in code_content.lower() or '=' in code_content:
                issues.append("可能存在明文密码存储")
                suggestions.append("使用密码哈希（如bcrypt）存储密码")
                score -= 10
        
        # 异常处理检查
        if 'try:' in code_content and 'except:' in code_content:
            if 'except Exception:' in code_content or 'except:' in code_content:
                suggestions.append("建议使用具体的异常类型而不是通用Exception")
                score -= 5
        elif any(risky_func in code_content for risky_func in ['open(', 'requests.', 'urllib.']):
            issues.append("缺少异常处理")
            suggestions.append("为可能失败的操作添加try-except异常处理")
            score -= 8
        
        # 代码质量检查
        if 'TODO' in code_content or 'FIXME' in code_content:
            issues.append("代码中包含未完成的TODO项")
            suggestions.append("完成所有TODO项后再提交")
            score -= 5
        
        # 性能检查
        if 'for ' in code_content and 'in range(' in code_content:
            suggestions.append("考虑使用列表推导式或numpy提高性能")
        
        # 如果没有发现问题，给出正面评价
        if not issues:
            issues = ["代码结构清晰，未发现明显问题"]
            suggestions.append("代码质量良好，建议添加单元测试")
        
        return f"""### 🎯 代码评分：{score}分（0-100分）

### ✅ 优点
- 代码结构相对清晰
- 遵循基本编码规范

### ❌ 发现的问题
{chr(10).join(f'- {issue}' for issue in issues)}

### 💡 改进建议
{chr(10).join(f'- {suggestion}' for suggestion in suggestions)}

### 📋 总结
基于静态代码分析的审查结果。建议结合人工审查确保代码质量。"""
    
    def _quick_analysis(self, prompt: str) -> str:
        """快速分析模式"""
        return """### 🎯 代码评分：80分（0-100分）

### ⚡ 快速审查模式
由于响应超时，使用快速审查模式。

### 💡 通用建议
- 确保添加适当的错误处理
- 检查输入参数验证  
- 考虑添加单元测试
- 注意安全性问题（SQL注入、XSS等）

### 📋 总结
建议进行详细的人工代码审查以确保质量。"""
    
    def _fallback_analysis(self, prompt: str) -> str:
        """备用分析模式"""
        return """### 🎯 代码评分：75分（0-100分）

### 🔧 备用审查模式
AI助手暂时不可用，使用备用审查模式。

### ✅ 基本检查
- 代码变更已检测
- 建议进行人工审查

### 💡 建议
- 检查代码逻辑正确性
- 确保安全性和性能
- 添加必要的测试

### 📋 总结
请配合人工审查确保代码质量。"""
    
    def _clean_response(self, response: str) -> str:
        """清理和格式化AI响应"""
        lines = response.split('\n')
        
        # 移除可能的CLI提示符和状态信息
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            if line and not line.startswith('q>') and not line.startswith('Amazon Q'):
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def review_merge_request(self, project_info: Dict, mr_info: Dict, code_changes: str) -> str:
        """审查Merge Request"""
        
        # 构建详细的审查提示词
        review_prompt = f"""
你是一位资深的代码审查专家。请对以下GitLab Merge Request进行详细的代码审查。

## 项目信息
- 项目: {project_info.get('name', 'Unknown')}
- MR标题: {mr_info.get('title', 'Unknown')}
- 作者: {mr_info.get('author', {}).get('name', 'Unknown')}
- 分支: {mr_info.get('source_branch', 'Unknown')} → {mr_info.get('target_branch', 'Unknown')}

## 审查要求
请从以下方面进行审查：
1. **代码质量**: 可读性、可维护性、代码规范
2. **安全性**: 潜在的安全漏洞和风险
3. **性能**: 性能优化建议
4. **最佳实践**: 是否遵循行业最佳实践
5. **潜在问题**: Bug、逻辑错误、边界条件
6. **架构设计**: 代码结构和设计模式

## 输出格式
请用中文回答，格式如下：

### 🎯 代码评分：XX分（0-100分）

### ✅ 优点
- 优点1
- 优点2

### ❌ 发现的问题
- 问题1：具体描述和影响
- 问题2：具体描述和影响

### 💡 改进建议
- 建议1：具体的改进方案
- 建议2：具体的改进方案

### 🔧 代码修改示例（如有必要）
```语言
// 修改前的问题代码
// 修改后的建议代码
```

### 📋 总结
简要总结这次代码审查的核心要点。

## 代码变更内容
{code_changes}
"""
        
        # 发送审查请求
        start_time = time.time()
        review_result = self._send_review_request(review_prompt)
        end_time = time.time()
        
        # 记录审查历史
        self.review_history.append({
            'timestamp': datetime.now().isoformat(),
            'project': project_info.get('name', 'Unknown'),
            'mr_iid': mr_info.get('iid', 'Unknown'),
            'duration': round(end_time - start_time, 2),
            'result': review_result[:500] + "..." if len(review_result) > 500 else review_result
        })
        
        return review_result
    
    def review_code_snippet(self, code: str, context: str = "") -> str:
        """审查代码片段"""
        
        # 构建上下文部分
        context_part = f"## 上下文\n{context}\n" if context else ""
        
        prompt = f"""请对以下代码片段进行快速审查：

{context_part}

## 代码
```
{code}
```

请简要指出：
1. 潜在问题
2. 改进建议
3. 最佳实践建议

用中文回答，保持简洁。
"""
        
        return self._send_review_request(prompt)
    
    def generate_inline_comments(self, file_changes: List[Dict]) -> List[Dict]:
        """为代码变更生成行内评论建议"""
        
        inline_comments = []
        
        for change in file_changes[:5]:  # 限制处理文件数量
            file_path = change.get('new_path', 'unknown')
            diff_content = change.get('diff', '')
            
            if not diff_content.strip():
                continue
            
            # 构建提示词，避免f-string中的反斜杠问题
            prompt_template = """请为以下代码变更生成简洁的行内评论建议。

文件: {file_path}

代码变更:
```diff
{diff_content}
```

要求：
1. 只对有问题或需要改进的代码行生成评论
2. 每个评论不超过50字
3. 语气友好，建设性
4. 用中文

请按以下格式输出：
行号:评论内容
行号:评论内容
...

如果没有需要评论的地方，请回复"无需评论"。
"""
            
            prompt = prompt_template.format(file_path=file_path, diff_content=diff_content)
            
            response = self._send_review_request(prompt)
            
            # 解析响应，提取行内评论
            if response and "无需评论" not in response:
                for line in response.split('\n'):
                    if ':' in line and line.strip():
                        try:
                            line_num, comment = line.split(':', 1)
                            line_num = int(line_num.strip())
                            comment = comment.strip()
                            
                            inline_comments.append({
                                'file_path': file_path,
                                'line_number': line_num,
                                'comment': comment
                            })
                        except (ValueError, IndexError):
                            continue
        
        return inline_comments
    
    def get_review_stats(self) -> Dict:
        """获取审查统计信息"""
        if not self.review_history:
            return {'total_reviews': 0, 'avg_duration': 0}
        
        total_reviews = len(self.review_history)
        avg_duration = sum(r['duration'] for r in self.review_history) / total_reviews
        
        return {
            'total_reviews': total_reviews,
            'avg_duration': round(avg_duration, 2),
            'last_review': self.review_history[-1]['timestamp']
        }

# 使用示例
if __name__ == "__main__":
    # 测试Amazon Q审查客户端
    reviewer = AmazonQReviewer()
    
    # 测试代码片段审查
    test_code = """
def process_user_data(user_input):
    data = eval(user_input)  # 潜在安全问题
    return data.upper()
"""
    
    result = reviewer.review_code_snippet(test_code, "用户输入处理函数")
    print("🤖 代码审查结果:")
    print(result)
    
    # 显示统计信息
    stats = reviewer.get_review_stats()
    print(f"\n📊 审查统计: {stats}")
