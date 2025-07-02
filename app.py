# @cursor start
import json
import logging
from flask import Flask, request, jsonify
from gitlab_client import GitLabClient
from ai_client import AIClient
from code_reviewer import CodeReviewer
from config import HOST, PORT, REVIEW_TRIGGER_KEYWORDS

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
        object_kind = webhook_data.get('object_kind', 'unknown')
        logger.info(f"收到webhook: {object_kind}")
        
        # 处理不同类型的webhook事件
        if object_kind == 'merge_request':
            return handle_merge_request_event(webhook_data)
        elif object_kind == 'note':
            return handle_note_event(webhook_data)
        else:
            return jsonify({'status': 'ignored', 'message': f'不支持的事件类型: {object_kind}'}), 200
        
    except Exception as e:
        logger.error(f"处理webhook失败: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

def is_bot_comment(webhook_data):
    """检查是否是机器人自己的评论"""
    try:
        # 检查评论作者信息
        user = webhook_data.get('user', {})
        username = user.get('username', '').lower()
        
        # 检查是否是机器人用户（根据GitLab用户名或ID判断）
        bot_indicators = [
            'bot', 'ai', 'aibot', 'robot', 'automation', 'ci', 'jenkins', 'gitlab-ci'
        ]
        
        # 如果用户名包含机器人标识，则认为是机器人评论
        if any(indicator in username for indicator in bot_indicators):
            return True
        
        # 检查评论内容是否包含机器人标识
        note_body = webhook_data.get('object_attributes', {}).get('note', '').lower()
        bot_content_indicators = [
            '🤖 ai代码审查机器人',
            '🤖 **ai代码审查机器人**',
            '*由ai代码审查机器人自动生成*',
            'ai代码审查完成'
        ]
        
        if any(indicator in note_body for indicator in bot_content_indicators):
            return True
        
        return False
    except Exception as e:
        logger.error(f"检查机器人评论失败: {e}")
        return False

def handle_merge_request_event(webhook_data):
    """处理Merge Request事件（优化版）"""
    # 检查是否是打开事件
    if not gitlab_client.is_merge_request_opened(webhook_data):
        return jsonify({'status': 'ignored', 'message': '不是Merge Request打开事件'}), 200
    
    # 提取项目ID和MR ID
    project_id = webhook_data['project']['id']
    mr_iid = webhook_data['object_attributes']['iid']
    
    logger.info(f"开始审查 MR #{mr_iid} in project {project_id}")
    
    # 立即添加处理中的评论（避免使用触发关键词）
    processing_comment = """🤖 **AI代码审查机器人**

⏳ 正在处理智能分析请求...

**处理步骤：**
1. 📋 分析代码变更
2. 🔍 获取相关上下文
3. 🤖 AI智能分析
4. 💬 生成详细建议

请稍候，分析结果将在几分钟内完成。"""
    
    try:
        gitlab_client.add_comment(project_id, mr_iid, processing_comment)
        logger.info(f"已添加处理中评论到 MR #{mr_iid}")
    except Exception as e:
        logger.error(f"添加处理中评论失败: {e}")
    
    # 异步执行代码审查
    def review_callback(review_result):
        try:
            # 添加最终审查结果评论（避免使用触发关键词）
            final_comment = f"""🤖 **AI智能分析完成**

{review_result}

---
*由AI代码审查机器人自动生成*"""
            
            gitlab_client.add_comment(project_id, mr_iid, final_comment)
            logger.info(f"审查完成，已添加最终评论到 MR #{mr_iid}")
        except Exception as e:
            logger.error(f"添加最终评论失败: {e}")
    
    code_reviewer.review_merge_request_async(project_id, mr_iid, review_callback)
    
    return jsonify({'status': 'success', 'message': '审查已启动，正在处理中...'}), 200

def handle_note_event(webhook_data):
    """处理评论事件（优化版）"""
    try:
        # 检查是否是Merge Request的评论
        if webhook_data.get('merge_request') is None:
            return jsonify({'status': 'ignored', 'message': '不是Merge Request评论'}), 200
        
        # 检查是否是机器人自己的评论，避免循环触发
        if is_bot_comment(webhook_data):
            logger.info("检测到机器人自己的评论，跳过处理")
            return jsonify({'status': 'ignored', 'message': '机器人自己的评论，跳过处理'}), 200
        
        # 检查评论内容是否包含触发关键词
        note_body = webhook_data.get('object_attributes', {}).get('note', '').strip().lower()
        
        is_triggered = any(keyword.lower() in note_body for keyword in REVIEW_TRIGGER_KEYWORDS)
        
        if not is_triggered:
            return jsonify({'status': 'ignored', 'message': '评论不包含触发关键词'}), 200
        
        # 提取项目ID和MR ID
        project_id = webhook_data['project']['id']
        mr_iid = webhook_data['merge_request']['iid']
        comment_id = webhook_data['object_attributes']['id']
        
        logger.info(f"评论触发审查: MR #{mr_iid}, 评论ID: {comment_id}, 内容: {note_body}")
        
        # 立即回复触发确认（避免使用触发关键词）
        trigger_comment = f"""🤖 **AI代码审查机器人**

✅ 检测到触发关键词: `{note_body}`
⏳ 正在启动智能分析...

**处理步骤：**
1. 📋 分析代码变更
2. 🔍 获取相关上下文  
3. 🤖 AI智能分析
4. 💬 生成详细建议

请稍候，分析结果将在几分钟内完成。"""
        
        try:
            gitlab_client.add_comment(project_id, mr_iid, trigger_comment)
            logger.info(f"已添加触发确认评论到 MR #{mr_iid}")
        except Exception as e:
            logger.error(f"添加触发确认评论失败: {e}")
        
        # 异步执行代码审查
        def review_callback(review_result):
            try:
                # 添加最终审查结果评论（避免使用触发关键词）
                final_comment = f"""🤖 **AI智能分析完成** (由评论触发)

{review_result}

---
*由AI代码审查机器人自动生成*"""
                
                gitlab_client.add_comment(project_id, mr_iid, final_comment)
                logger.info(f"评论触发审查完成，已添加最终评论到 MR #{mr_iid}")
            except Exception as e:
                logger.error(f"添加最终评论失败: {e}")
        
        code_reviewer.review_merge_request_async(project_id, mr_iid, review_callback)
        
        return jsonify({'status': 'success', 'message': '评论触发审查已启动，正在处理中...'}), 200
        
    except Exception as e:
        logger.error(f"处理评论事件失败: {e}")
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
        'features': [
            '🚀 性能优化版本',
            '💾 文件内容缓存',
            '⚡ 批量AI处理',
            '💬 即时反馈',
            '🔍 上下文增强',
            '📝 行内评论'
        ],
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
    logger.info(f"启动AI代码审查服务（性能优化版），监听 {HOST}:{PORT}")
    app.run(host=HOST, port=PORT, debug=True)
# @cursor end 