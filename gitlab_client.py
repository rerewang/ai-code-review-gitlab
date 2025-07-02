# @cursor start
import gitlab
import requests
from retrying import retry
from config import GITLAB_URL, GITLAB_TOKEN

class GitLabClient:
    """GitLab API客户端"""
    
    def __init__(self):
        self.gl = gitlab.Gitlab(url=GITLAB_URL, private_token=GITLAB_TOKEN)
        self.headers = {"PRIVATE-TOKEN": GITLAB_TOKEN}
    
    @retry(stop_max_attempt_number=3, wait_fixed=2000)
    def get_merge_request_changes(self, project_id, mr_iid):
        """获取Merge Request的代码变更"""
        url = f"{GITLAB_URL}/api/v4/projects/{project_id}/merge_requests/{mr_iid}/changes"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()["changes"]
    
    @retry(stop_max_attempt_number=3, wait_fixed=2000)
    def get_merge_request_info(self, project_id, mr_iid):
        """获取Merge Request信息"""
        url = f"{GITLAB_URL}/api/v4/projects/{project_id}/merge_requests/{mr_iid}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    @retry(stop_max_attempt_number=3, wait_fixed=2000)
    def add_comment(self, project_id, mr_iid, comment):
        """在Merge Request中添加评论"""
        url = f"{GITLAB_URL}/api/v4/projects/{project_id}/merge_requests/{mr_iid}/notes"
        data = {"body": comment}
        response = requests.post(url, headers=self.headers, json=data)
        response.raise_for_status()
        return response.json()
    
    @retry(stop_max_attempt_number=3, wait_fixed=2000)
    def add_inline_comment(self, project_id, mr_iid, file_path, line_number, comment, line_type="new"):
        """
        在Merge Request中添加行内评论
        
        Args:
            project_id: 项目ID
            mr_iid: Merge Request的IID
            file_path: 文件路径
            line_number: 行号
            comment: 评论内容
            line_type: 行类型 ("new" 或 "old")
        """
        # 获取MR的详细信息，包括SHA值
        mr_info = self.get_merge_request_info(project_id, mr_iid)
        diff_refs = mr_info.get('diff_refs', {})
        
        if not diff_refs:
            raise Exception("无法获取MR的diff_refs")
        
        # 使用Discussions API，这是正确的行内评论方式（参考原项目）
        url = f"{GITLAB_URL}/api/v4/projects/{project_id}/merge_requests/{mr_iid}/discussions"
        
        # 构建position数据（参考原项目格式）
        position_data = {
            "base_sha": diff_refs.get('base_sha'),
            "start_sha": diff_refs.get('start_sha'),
            "head_sha": diff_refs.get('head_sha'),
            "position_type": "text",
            "old_path": file_path if line_type == "old" else None,
            "old_line": line_number if line_type == "old" else None,
            "new_path": file_path if line_type == "new" else None,
            "new_line": line_number if line_type == "new" else None
        }
        
        # 移除None值
        position_data = {k: v for k, v in position_data.items() if v is not None}
        
        data = {
            "body": comment,
            "position": position_data
        }
        
        print("\n================ Discussions API CURL 命令 ================")
        print(f"curl -X POST \\")
        print(f"  '{url}' \\")
        print(f"  -H 'PRIVATE-TOKEN: {self.headers['PRIVATE-TOKEN']}' \\")
        print(f"  -H 'Content-Type: application/json' \\")
        print(f"  -d '{{")
        print(f"    \"body\": \"{comment}\",")
        print(f"    \"position\": {{")
        for k, v in position_data.items():
            if isinstance(v, str):
                print(f"      \"{k}\": \"{v}\",")
            else:
                print(f"      \"{k}\": {v},")
        print(f"    }}")
        print(f"  }}'")
        print("==================================================\n")
        
        print(f"🔍 添加行内评论:")
        print(f"   文件: {file_path}")
        print(f"   行号: {line_number}")
        print(f"   类型: {line_type}")
        print(f"   评论: {comment[:50]}...")
        
        response = requests.post(url, headers=self.headers, json=data)
        
        if response.status_code != 201:
            print(f"❌ 行内评论添加失败: {response.status_code}")
            print(f"   响应: {response.text}")
            response.raise_for_status()
        
        return response.json()
    
    @retry(stop_max_attempt_number=3, wait_fixed=2000)
    def add_multiple_inline_comments(self, project_id, mr_iid, comments):
        """
        批量添加行内评论
        
        Args:
            project_id: 项目ID
            mr_iid: Merge Request的IID
            comments: 评论列表，每个元素包含 file_path, line_number, comment, line_type
        """
        results = []
        for comment_data in comments:
            try:
                result = self.add_inline_comment(
                    project_id=project_id,
                    mr_iid=mr_iid,
                    file_path=comment_data['file_path'],
                    line_number=comment_data['line_number'],
                    comment=comment_data['comment'],
                    line_type=comment_data.get('line_type', 'new')
                )
                results.append(result)
            except Exception as e:
                print(f"添加行内评论失败: {e}")
                # 如果行内评论失败，尝试添加普通评论作为备选
                try:
                    fallback_comment = f"**{comment_data['file_path']}** (第{comment_data['line_number']}行): {comment_data['comment']}"
                    self.add_comment(project_id, mr_iid, fallback_comment)
                except Exception as fallback_error:
                    print(f"备选评论也失败: {fallback_error}")
        
        return results
    
    def get_file_content(self, project_id, file_path, branch="main"):
        """获取文件内容"""
        # 对文件路径进行URL编码
        encoded_path = file_path.replace('/', '%2F')
        url = f"{GITLAB_URL}/api/v4/projects/{project_id}/repository/files/{encoded_path}/raw"
        params = {"ref": branch}
        response = requests.get(url, headers=self.headers, params=params)
        if response.status_code == 200:
            return response.text
        return None
    
    def get_project_files(self, project_id, branch="main", path=""):
        """获取项目文件列表"""
        url = f"{GITLAB_URL}/api/v4/projects/{project_id}/repository/tree"
        params = {"ref": branch, "path": path, "recursive": "true"}
        response = requests.get(url, headers=self.headers, params=params)
        if response.status_code == 200:
            files = response.json()
            return [file["path"] for file in files if file["type"] == "blob"]
        return []
    
    def is_merge_request_opened(self, webhook_data):
        """判断是否是Merge Request打开事件"""
        try:
            attributes = webhook_data.get("object_attributes", {})
            state = attributes.get("state")
            action = webhook_data.get("object_kind")
            return action == "merge_request" and state == "opened"
        except Exception:
            return False
# @cursor end 