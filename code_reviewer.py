# @cursor start
import re
import threading
from typing import List, Dict, Optional
from config import REVIEW_FILE_TYPES, IGNORE_FILE_TYPES, MAX_FILES, CONTEXT_LINES
# from prd_analyzer import PRDAnalyzer  # 暂不启用PRD分析

class CodeReviewer:
    """代码审查器"""
    
    def __init__(self, gitlab_client, ai_client):
        self.gitlab_client = gitlab_client
        self.ai_client = ai_client
        # self.prd_analyzer = PRDAnalyzer(gitlab_client)  # 暂不启用PRD分析
        
        # 添加缓存机制
        self._file_cache = {}  # 文件内容缓存
        self._cache_lock = threading.Lock()  # 缓存锁
    
    def _get_cached_file_content(self, project_id, file_path, branch="main"):
        """获取缓存的文件内容"""
        cache_key = f"{project_id}:{file_path}:{branch}"
        
        with self._cache_lock:
            if cache_key in self._file_cache:
                return self._file_cache[cache_key]
            
            # 获取文件内容并缓存
            try:
                content = self.gitlab_client.get_file_content(project_id, file_path, branch)
                self._file_cache[cache_key] = content
                return content
            except Exception as e:
                print(f"获取文件内容失败: {e}")
                self._file_cache[cache_key] = None
                return None
    
    def _clear_cache(self):
        """清理缓存"""
        with self._cache_lock:
            self._file_cache.clear()
    
    def should_review_file(self, file_path):
        """判断是否需要审查该文件"""
        if not file_path:
            return False
        
        # 检查文件类型
        for file_type in REVIEW_FILE_TYPES:
            if file_path.endswith(file_type):
                break
        else:
            return False
        
        # 检查忽略的文件
        for ignore_type in IGNORE_FILE_TYPES:
            if ignore_type in file_path:
                return False
        
        return True
    
    def parse_diff(self, diff_content):
        """解析diff内容，提取代码变更"""
        lines = diff_content.split('\n')
        added_lines = []
        removed_lines = []
        diff_blocks = []
        
        current_block = {
            'old_start': 0,
            'new_start': 0,
            'old_lines': [],
            'new_lines': [],
            'context': []
        }
        
        for line in lines:
            if line.startswith('@@'):
                # 新的diff块
                if current_block['old_lines'] or current_block['new_lines']:
                    diff_blocks.append(current_block)
                
                # 解析@@行
                match = re.match(r'^@@ -(\d+),?(\d+)? \+(\d+),?(\d+)? @@', line)
                if match:
                    current_block = {
                        'old_start': int(match.group(1)),
                        'new_start': int(match.group(3)),
                        'old_lines': [],
                        'new_lines': [],
                        'context': []
                    }
            elif line.startswith('+') and not line.startswith('+++'):
                added_lines.append(line[1:])
                current_block['new_lines'].append(line[1:])
            elif line.startswith('-') and not line.startswith('---'):
                removed_lines.append(line[1:])
                current_block['old_lines'].append(line[1:])
            elif line.startswith(' '):
                current_block['context'].append(line[1:])
        
        # 添加最后一个块
        if current_block['old_lines'] or current_block['new_lines']:
            diff_blocks.append(current_block)
        
        return {
            'added': '\n'.join(added_lines),
            'removed': '\n'.join(removed_lines),
            'raw': diff_content,
            'blocks': diff_blocks
        }
    
    def get_file_context(self, project_id, file_path, diff_blocks, branch="main"):
        """获取文件上下文（优化版）"""
        try:
            file_content = self._get_cached_file_content(project_id, file_path, branch)
            if not file_content:
                return []
            
            lines = file_content.split('\n')
            context_blocks = []
            
            for block in diff_blocks:
                new_start = block['new_start']
                new_end = new_start + len(block['new_lines'])
                
                # 获取上下文行
                context_start = max(0, new_start - CONTEXT_LINES - 1)
                context_end = min(len(lines), new_end + CONTEXT_LINES)
                
                context_lines = lines[context_start:context_end]
                context_blocks.append({
                    'start_line': context_start + 1,
                    'end_line': context_end,
                    'content': '\n'.join(context_lines),
                    'diff_block': block
                })
            
            return context_blocks
        except Exception as e:
            print(f"获取文件上下文失败: {e}")
            return []
    
    def format_code_changes_with_context(self, changes, project_id, branch="main"):
        """格式化代码变更信息（包含上下文，优化版）"""
        formatted_changes = []
        
        # 批量获取文件内容，减少API调用
        files_to_fetch = set()
        for change in changes:
            if self.should_review_file(change.get('new_path')):
                file_path = change.get('new_path', 'unknown')
                files_to_fetch.add((project_id, file_path, branch))
        
        # 预加载文件内容到缓存
        for project_id, file_path, branch in files_to_fetch:
            self._get_cached_file_content(project_id, file_path, branch)
        
        for change in changes:
            if not self.should_review_file(change.get('new_path')):
                continue
            
            file_path = change.get('new_path', 'unknown')
            diff_content = change.get('diff', '')
            
            parsed_diff = self.parse_diff(diff_content)
            context_blocks = self.get_file_context(project_id, file_path, parsed_diff['blocks'], branch)
            
            formatted_change = f"""
## 文件: {file_path}

### 代码变更:
```{self._get_file_extension(file_path)}
{diff_content}
```

"""
            
            # 添加上下文信息
            if context_blocks:
                formatted_change += "### 相关上下文:\n"
                for i, context_block in enumerate(context_blocks, 1):
                    formatted_change += f"""
**上下文块 {i}** (行 {context_block['start_line']}-{context_block['end_line']}):
```{self._get_file_extension(file_path)}
{context_block['content']}
```
"""
            
            formatted_change += "\n---\n"
            formatted_changes.append(formatted_change)
        
        return '\n'.join(formatted_changes)
    
    def format_code_changes(self, changes):
        """格式化代码变更信息（简化版）"""
        formatted_changes = []
        
        for change in changes:
            if not self.should_review_file(change.get('new_path')):
                continue
            
            file_path = change.get('new_path', 'unknown')
            diff_content = change.get('diff', '')
            
            parsed_diff = self.parse_diff(diff_content)
            
            formatted_change = f"""
## 文件: {file_path}

### 添加的代码:
```{self._get_file_extension(file_path)}
{parsed_diff['added']}
```

### 删除的代码:
```{self._get_file_extension(file_path)}
{parsed_diff['removed']}
```

---
"""
            formatted_changes.append(formatted_change)
        
        return '\n'.join(formatted_changes)
    
    def _get_file_extension(self, file_path):
        """获取文件扩展名用于代码高亮"""
        if '.' in file_path:
            return file_path.split('.')[-1]
        return 'text'
    
    def generate_inline_comments(self, changes, project_id, branch="main"):
        """生成真正的行内评论（优化版 - 批量处理）"""
        inline_comments = []
        
        # 收集所有需要生成评论的块
        comment_blocks = []
        
        for change in changes:
            if not self.should_review_file(change.get('new_path')):
                continue
            
            file_path = change.get('new_path', 'unknown')
            diff_content = change.get('diff', '')
            
            parsed_diff = self.parse_diff(diff_content)
            
            # 为每个diff块收集评论信息
            for block in parsed_diff['blocks']:
                if block['new_lines'] or block['old_lines']:
                    # 为新增的代码行生成评论
                    for i, line in enumerate(block['new_lines']):
                        line_number = block['new_start'] + i
                        block_content = f"文件: {file_path}\n行号: {line_number}\n代码: {line}\n"
                        
                        comment_blocks.append({
                            'file_path': file_path,
                            'line_number': line_number,
                            'line_type': 'new',
                            'content': block_content,
                            'code_line': line
                        })
                    
                    # 为删除的代码行生成评论
                    for i, line in enumerate(block['old_lines']):
                        line_number = block['old_start'] + i
                        block_content = f"文件: {file_path}\n行号: {line_number}\n删除代码: {line}\n"
                        
                        comment_blocks.append({
                            'file_path': file_path,
                            'line_number': line_number,
                            'line_type': 'old',
                            'content': block_content,
                            'code_line': line
                        })
        
        # 批量生成评论（限制数量避免过载）
        if comment_blocks:
            # 只处理前5个最重要的变更
            important_blocks = comment_blocks[:5]
            
            # 合并所有块内容，一次性调用AI
            combined_content = "\n\n---\n\n".join([block['content'] for block in important_blocks])
            
            try:
                # 使用AI批量生成评论（使用专门的行内评论提示词）
                inline_prompt = f"""你是代码审查专家。请对以下代码行进行简洁的行内评论。

要求：
1. 评论要简洁明了，不超过50字
2. 针对具体代码行的问题或建议
3. 使用中文，语气友好
4. 如果是好的代码，可以给出正面评价

代码行：
{combined_content}

请为每个代码行生成一行评论，用"---"分隔："""
                
                ai_response = self.ai_client.review_code(inline_prompt)
                
                # 分割AI响应
                responses = ai_response.split('\n---\n')
                
                for i, block in enumerate(important_blocks):
                    if i < len(responses):
                        comment = responses[i].strip()
                        # 清理评论内容，只保留第一行
                        comment = comment.split('\n')[0].strip()
                        # 限制长度
                        short_comment = comment[:80] + "..." if len(comment) > 80 else comment
                    else:
                        # 默认评论
                        short_comment = "建议检查这行代码的逻辑"
                    
                    inline_comments.append({
                        'file_path': block['file_path'],
                        'line_number': block['line_number'],
                        'line_type': block['line_type'],
                        'comment': short_comment
                    })
            except Exception as e:
                print(f"生成行内评论失败: {e}")
                # 如果批量处理失败，返回简单的评论
                for block in important_blocks[:3]:
                    inline_comments.append({
                        'file_path': block['file_path'],
                        'line_number': block['line_number'],
                        'line_type': block['line_type'],
                        'comment': f"建议检查这行代码的逻辑和错误处理。"
                    })
        
        return inline_comments
    
    def review_merge_request(self, project_id, mr_iid):
        """审查整个Merge Request（优化版）"""
        try:
            # 获取代码变更
            changes = self.gitlab_client.get_merge_request_changes(project_id, mr_iid)
            merge_info = self.gitlab_client.get_merge_request_info(project_id, mr_iid)
            
            # 检查文件数量限制
            if len(changes) > MAX_FILES:
                return f"⚠️ 文件数量过多 ({len(changes)} > {MAX_FILES})，跳过审查"
            
            # 格式化代码变更（包含上下文）
            formatted_changes = self.format_code_changes_with_context(
                changes, project_id, merge_info.get('source_branch', 'main')
            )
            
            if not formatted_changes.strip():
                return "✅ 没有需要审查的代码变更"
            
            # 使用AI审查
            review_result = self.ai_client.review_code(formatted_changes)
            
            # 生成真正的行内评论
            inline_comments = self.generate_inline_comments(
                changes, project_id, merge_info.get('source_branch', 'main')
            )
            
            # 添加真正的行内评论
            if inline_comments:
                try:
                    self.gitlab_client.add_multiple_inline_comments(project_id, mr_iid, inline_comments)
                    review_result += f"\n\n✅ 已添加 {len(inline_comments)} 个行内评论"
                except Exception as e:
                    print(f"添加行内评论失败: {e}")
                    # 如果行内评论失败，在普通评论中说明
                    review_result += f"\n\n⚠️ 行内评论添加失败，以下是建议的行内评论：\n\n"
                    for comment in inline_comments[:3]:  # 只显示前3个
                        review_result += f"- **{comment['file_path']}** (第{comment['line_number']}行): {comment['comment']}\n"
            
            # 清理缓存
            self._clear_cache()
            
            return review_result
            
        except Exception as e:
            # 清理缓存
            self._clear_cache()
            return f"❌ 审查失败: {str(e)}"
    
    def review_merge_request_async(self, project_id, mr_iid, callback):
        """异步审查Merge Request"""
        def review_task():
            result = self.review_merge_request(project_id, mr_iid)
            callback(result)
        
        thread = threading.Thread(target=review_task)
        thread.start()
        return thread
# @cursor end 