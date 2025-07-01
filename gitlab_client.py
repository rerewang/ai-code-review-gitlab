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
    
    def get_file_content(self, project_id, file_path, branch="main"):
        """获取文件内容"""
        url = f"{GITLAB_URL}/api/v4/projects/{project_id}/repository/files/{file_path}/raw"
        params = {"ref": branch}
        response = requests.get(url, headers=self.headers, params=params)
        if response.status_code == 200:
            return response.text
        return None
    
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