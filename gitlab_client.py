# @cursor start
import gitlab
import requests
from retrying import retry
from config import GITLAB_URL, GITLAB_TOKEN
import re

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

    def extract_diff_new_lines(self, diff_content):
        """解析diff，返回所有可评论的new_line行号和内容"""
        results = []
        diff_lines = diff_content.split('\n')
        new_line_num = None
        for line in diff_lines:
            if line.startswith('@@'):
                m = re.match(r'@@ -\\d+(?:,\\d+)? \\+(\\d+)(?:,\\d+)? @@', line)
                if m:
                    new_line_num = int(m.group(1))
                continue
            if line.startswith('+') and not line.startswith('+++'):
                if new_line_num is not None:
                    results.append((new_line_num, line[1:]))  # (new_line, 代码内容)
                    new_line_num += 1
            elif line.startswith('-') and not line.startswith('---'):
                continue
            else:
                if new_line_num is not None:
                    new_line_num += 1
        return results

    @retry(stop_max_attempt_number=3, wait_fixed=2000)
    def add_inline_comment(self, project_id, mr_iid, file_path, line_number, comment, line_type="new"):
        """
        在Merge Request中添加行内评论（只对diff变更+号行）
        """
        mr_info = self.get_merge_request_info(project_id, mr_iid)
        diff_refs = mr_info.get('diff_refs', {})
        if not diff_refs:
            raise Exception("无法获取MR的diff_refs")
        url = f"{GITLAB_URL}/api/v4/projects/{project_id}/merge_requests/{mr_iid}/discussions"
        position_data = {
            "base_sha": diff_refs.get('base_sha'),
            "start_sha": diff_refs.get('start_sha'),
            "head_sha": diff_refs.get('head_sha'),
            "position_type": "text",
            "new_path": file_path,
            "new_line": line_number
        }
        data = {
            "body": comment,
            "position": position_data
        }
        response = requests.post(url, headers=self.headers, json=data)
        if response.status_code != 201:
            print(f"❌ 行内评论添加失败: {response.status_code}")
            print(f"   响应: {response.text}")
            response.raise_for_status()
        return response.json()

    def get_visible_inline_comments_count(self, project_id, mr_iid, file_path, line_numbers, ai_comments):
        """
        统计真正可见的行内评论数（拉取discussions校验）
        """
        url = f"{GITLAB_URL}/api/v4/projects/{project_id}/merge_requests/{mr_iid}/discussions"
        resp = requests.get(url, headers=self.headers)
        discussions = resp.json()
        count = 0
        for d in discussions:
            notes = d.get('notes', [])
            for note in notes:
                pos = note.get('position', {})
                if (pos.get('new_path') == file_path and
                    pos.get('new_line') in line_numbers and
                    note.get('body') in ai_comments):
                    count += 1
        return count

    def add_multiple_inline_comments(self, project_id, mr_iid, ai_comment_func):
        """
        批量添加行内评论：只对diff变更+号行，AI评论自动绑定，统计真正可见评论数
        ai_comment_func: (file_path, line_number, code_line) -> str
        """
        changes = self.get_merge_request_changes(project_id, mr_iid)
        count = 0
        visible_count = 0
        for change in changes:
            file_path = change.get('new_path', change.get('old_path', 'unknown'))
            diff_content = change.get('diff', '')
            diff_lines = self.extract_diff_new_lines(diff_content)
            ai_comments = []
            line_numbers = []
            for line_number, code_line in diff_lines:
                comment = ai_comment_func(file_path, line_number, code_line)
                ai_comments.append(comment)
                line_numbers.append(line_number)
                try:
                    self.add_inline_comment(
                        project_id=project_id,
                        mr_iid=mr_iid,
                        file_path=file_path,
                        line_number=line_number,
                        comment=comment,
                        line_type="new"
                    )
                    print(f"✅ 行内评论成功: {file_path}:{line_number}")
                    count += 1
                except Exception as e:
                    print(f"❌ 行内评论失败: {file_path}:{line_number} {e}")
            # 统计本文件真正可见的评论数
            if line_numbers and ai_comments:
                visible = self.get_visible_inline_comments_count(project_id, mr_iid, file_path, line_numbers, ai_comments)
                visible_count += visible
        print(f"共尝试添加 {count} 个行内评论（仅diff变更+号行），真正可见 {visible_count} 个")

    def get_file_content(self, project_id, file_path, branch="main"):
        """获取文件内容"""
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