# @cursor start
import os
import requests
import subprocess
from config import AI_PROVIDER, AI_API_URL, AI_API_KEY, AI_MODEL

# Amazon Q CLI 配置
AMAZONQ_CLI_PATH = os.getenv("AMAZONQ_CLI_PATH", "q")

class AIClient:
    """通用AI大模型客户端，支持任意厂商"""
    def __init__(self):
        pass

    def review_code(self, code_changes):
        from config import REVIEW_PROMPT
        # 检查是否使用Amazon Q CLI
        AMAZONQ_USE_CLI = os.getenv("AMAZONQ_USE_CLI", "false").lower() == "true"
        if AMAZONQ_USE_CLI:
            return self._review_code_amazonq_cli(code_changes)
        
        prompt = REVIEW_PROMPT.format(code_changes=code_changes)
        headers = {
            "Authorization": f"Bearer {AI_API_KEY}",
            "Content-Type": "application/json"
        }
        # 适配不同厂商的参数格式
        if "openai" in AI_API_URL:
            data = {
                "model": AI_MODEL,
                "messages": [
                    {"role": "system", "content": "你是一位资深的代码审查专家。"},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 2000,
                "temperature": 0.3
            }
        elif "dashscope.aliyuncs.com" in AI_API_URL:  # 通义千问
            data = {
                "model": AI_MODEL,
                "input": {
                    "prompt": prompt
                },
                "parameters": {
                    "result_format": "message"
                }
            }
        elif "siliconflow" in AI_API_URL:  # 硅流API
            data = {
                "model": AI_MODEL,
                "messages": [
                    {"role": "system", "content": "你是一位资深的代码审查专家。"},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 2000,
                "temperature": 0.3
            }
        elif "deepseek" in AI_API_URL:
            data = {
                "model": AI_MODEL,
                "messages": [
                    {"role": "system", "content": "你是一位资深的代码审查专家。"},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 2000,
                "temperature": 0.3
            }
        else:
            # 默认兼容OpenAI格式
            data = {
                "model": AI_MODEL,
                "messages": [
                    {"role": "system", "content": "你是一位资深的代码审查专家。"},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 2000,
                "temperature": 0.3
            }
        print(f"🔍 调试信息:")
        print(f"   API URL: {AI_API_URL}")
        print(f"   Model: {AI_MODEL}")
        print(f"   Headers: {headers}")
        print(f"   Data: {data}")
        response = requests.post(AI_API_URL, headers=headers, json=data)
        if response.status_code != 200:
            print(f"❌ API请求失败:")
            print(f"   状态码: {response.status_code}")
            print(f"   响应内容: {response.text}")
        response.raise_for_status()
        # 适配不同厂商的返回格式
        if "openai" in AI_API_URL or "deepseek" in AI_API_URL or "siliconflow" in AI_API_URL:
            return response.json()["choices"][0]["message"]["content"]
        elif "dashscope.aliyuncs.com" in AI_API_URL:
            return response.json()["output"]["text"]
        else:
            # 默认兼容OpenAI格式
            return response.json()["choices"][0]["message"]["content"]

    def _review_code_amazonq_cli(self, code_changes):
        """
        使用Amazon Q CLI进行代码审查（最终修复版本）
        """
        from config import REVIEW_PROMPT
        prompt = REVIEW_PROMPT.format(code_changes=code_changes)
        
        # 简化提示词，提高响应速度
        simple_prompt = f"请简要审查以下代码，用中文回答：\n\n{code_changes[:1000]}"
        
        try:
            # 使用临时文件避免引号转义问题
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(simple_prompt)
                temp_file = f.name
            
            # 使用cat管道方式
            cmd = f'cat "{temp_file}" | {AMAZONQ_CLI_PATH} chat'
            
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=90,  # 增加到90秒
                env=dict(os.environ, TERM='dumb')
            )
            
            # 清理临时文件
            try:
                os.unlink(temp_file)
            except:
                pass
            
            if result.returncode == 0:
                output = result.stdout
                
                # 清理ANSI控制字符
                import re
                clean_output = re.sub(r'\x1b\[[0-9;]*[mGKH]', '', output)
                clean_output = re.sub(r'\x1b\[\?[0-9]+[hl]', '', clean_output)
                
                # 提取AI响应（在 > 符号后）
                lines = clean_output.split('\n')
                response_parts = []
                
                for line in lines:
                    line = line.strip()
                    if line.startswith('>') and len(line) > 2:
                        response_parts.append(line[1:].strip())
                
                if response_parts:
                    result_text = '\n'.join(response_parts)
                    # 如果结果太短，可能没有正确提取，返回清理后的全部内容
                    if len(result_text) < 50:
                        # 过滤掉提示信息，保留主要内容
                        filtered_lines = []
                        skip_patterns = ['Did you know', '╭', '│', '╰', '━', 'ctrl +', '/help', 'You are chatting', 'Thinking...', 'To exit']
                        for line in clean_output.split('\n'):
                            line = line.strip()
                            if line and not any(pattern in line for pattern in skip_patterns):
                                filtered_lines.append(line)
                        return '\n'.join(filtered_lines)
                    return result_text
                else:
                    # 如果没有找到 > 符号，返回清理后的全部输出
                    filtered_lines = []
                    skip_patterns = ['Did you know', '╭', '│', '╰', '━', 'ctrl +', '/help', 'You are chatting', 'Thinking...', 'To exit']
                    for line in clean_output.split('\n'):
                        line = line.strip()
                        if line and not any(pattern in line for pattern in skip_patterns):
                            filtered_lines.append(line)
                    return '\n'.join(filtered_lines)
            else:
                return f"Amazon Q CLI执行失败: {result.stderr}"
                
        except subprocess.TimeoutExpired:
            return "Amazon Q CLI响应超时，请稍后重试"
        except Exception as e:
            return f"Amazon Q CLI执行异常: {str(e)}"

# @cursor end 
