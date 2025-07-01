# @cursor start
import json
import logging
from flask import Flask, request, jsonify
from gitlab_client import GitLabClient
from ai_client import AIClient
from code_reviewer import CodeReviewer
from config import HOST, PORT

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建Flask应用
app = Flask(__name__)

# 初始化客户端
gitlab_client = GitLabClient()
ai_client = AIClient()
code_reviewer = CodeReviewer(gitlab_client, ai_client)

@app.route('/webhook', methods=['POST'])
def webhook():
    """处理GitLab webhook请求"""
    try:
        # 解析webhook数据
        webhook_data = request.get_json()
        logger.info(f"收到webhook: {webhook_data.get('object_kind', 'unknown')}")
        
        # 检查是否是Merge Request事件
        if webhook_data.get('object_kind') != 'merge_request':
            return jsonify({'status': 'ignored', 'message': '不是Merge Request事件'}), 200
        
        # 检查是否是打开事件
        if not gitlab_client.is_merge_request_opened(webhook_data):
            return jsonify({'status': 'ignored', 'message': '不是Merge Request打开事件'}), 200
        
        # 提取项目ID和MR ID
        project_id = webhook_data['project']['id']
        mr_iid = webhook_data['object_attributes']['iid']
        
        logger.info(f"开始审查 MR #{mr_iid} in project {project_id}")
        
        # 异步执行代码审查
        def review_callback(review_result):
            try:
                # 添加评论到GitLab
                gitlab_client.add_comment(project_id, mr_iid, review_result)
                logger.info(f"审查完成，已添加评论到 MR #{mr_iid}")
            except Exception as e:
                logger.error(f"添加评论失败: {e}")
        
        code_reviewer.review_merge_request_async(project_id, mr_iid, review_callback)
        
        return jsonify({'status': 'success', 'message': '审查已启动'}), 200
        
    except Exception as e:
        logger.error(f"处理webhook失败: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return jsonify({'status': 'healthy', 'message': 'AI代码审查服务运行正常'}), 200

@app.route('/', methods=['GET'])
def index():
    """首页"""
    return jsonify({
        'name': 'AI代码审查GitLab机器人',
        'version': '1.0.0',
        'endpoints': {
            'webhook': '/webhook',
            'health': '/health'
        }
    }), 200

@app.errorhandler(400)
@app.errorhandler(404)
@app.errorhandler(500)
def handle_error(error):
    """错误处理"""
    return jsonify({
        'status': 'error',
        'code': error.code,
        'message': str(error)
    }), error.code

if __name__ == '__main__':
    logger.info(f"启动AI代码审查服务，监听 {HOST}:{PORT}")
    app.run(host=HOST, port=PORT, debug=True)
# @cursor end 