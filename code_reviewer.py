# @cursor start
import re
import threading
from config import REVIEW_FILE_TYPES, IGNORE_FILE_TYPES, MAX_FILES, CONTEXT_LINES

class CodeReviewer:
    """代码审查器"""
    
    def __init__(self, gitlab_client, ai_client):
        self.gitlab_client = gitlab_client
        self.ai_client = ai_client
    
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
        
        for line in lines:
            if line.startswith('+') and not line.startswith('+++'):
                added_lines.append(line[1:])  # 去掉+号
            elif line.startswith('-') and not line.startswith('---'):
                removed_lines.append(line[1:])  # 去掉-号
        
        return {
            'added': '\n'.join(added_lines),
            'removed': '\n'.join(removed_lines),
            'raw': diff_content
        }
    
    def format_code_changes(self, changes):
        """格式化代码变更信息"""
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
    
    def review_merge_request(self, project_id, mr_iid):
        """审查整个Merge Request"""
        try:
            # 获取代码变更
            changes = self.gitlab_client.get_merge_request_changes(project_id, mr_iid)
            
            # 检查文件数量限制
            if len(changes) > MAX_FILES:
                return f"⚠️ 文件数量过多 ({len(changes)} > {MAX_FILES})，跳过审查"
            
            # 格式化代码变更
            formatted_changes = self.format_code_changes(changes)
            
            if not formatted_changes.strip():
                return "✅ 没有需要审查的代码变更"
            
            # 使用AI审查
            review_result = self.ai_client.review_code(formatted_changes)
            
            return review_result
            
        except Exception as e:
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