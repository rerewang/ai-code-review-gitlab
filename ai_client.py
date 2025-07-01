# @cursor start
import requests
from config import AI_API_URL, AI_MODEL, AI_API_KEY, AI_API_KEY_HEADER, AI_API_KEY_PREFIX

class AIClient:
    """通用AI大模型客户端，支持任意厂商"""
    def __init__(self):
        pass

    def review_code(self, code_changes):
        from config import REVIEW_PROMPT
        prompt = REVIEW_PROMPT.format(code_changes=code_changes)
        headers = {
            AI_API_KEY_HEADER: f"{AI_API_KEY_PREFIX}{AI_API_KEY}",
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
# @cursor end 