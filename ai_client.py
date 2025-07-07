# @cursor start
import os
import requests
from config import AI_PROVIDER, AI_API_URL, AI_API_KEY, AI_MODEL

class AIClient:
    """通用AI大模型客户端，支持任意厂商（简化版）"""
    def __init__(self):
        pass

    def review_code(self, code_changes):
        from config import REVIEW_PROMPT
        
        # 通用API调用逻辑
        prompt = REVIEW_PROMPT.format(code_changes=code_changes)
        headers = {
            "Authorization": f"Bearer {AI_API_KEY}",
            "Content-Type": "application/json"
        }
        
        # 根据AI_PROVIDER自动适配API格式
        data = self._build_api_request_data(prompt)
        
        print(f"🔍 调试信息:")
        print(f"   Provider: {AI_PROVIDER}")
        print(f"   API URL: {AI_API_URL}")
        print(f"   Model: {AI_MODEL}")
        
        response = requests.post(AI_API_URL, headers=headers, json=data)
        
        if response.status_code != 200:
            print(f"❌ API请求失败:")
            print(f"   状态码: {response.status_code}")
            print(f"   响应内容: {response.text}")
        
        response.raise_for_status()
        
        # 根据AI_PROVIDER解析响应
        return self._parse_api_response(response.json())

    def _build_api_request_data(self, prompt):
        """根据AI_PROVIDER构建API请求数据"""
        if AI_PROVIDER == "aliyun":
            # 阿里云通义千问格式
            return {
                "model": AI_MODEL,
                "input": {
                    "prompt": prompt
                },
                "parameters": {
                    "result_format": "message"
                }
            }
        else:
            # 默认OpenAI兼容格式（适用于siliconflow, openai, deepseek等）
            return {
                "model": AI_MODEL,
                "messages": [
                    {"role": "system", "content": "你是一位资深的代码审查专家。"},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 2000,
                "temperature": 0.3
            }

    def _parse_api_response(self, response_json):
        """根据AI_PROVIDER解析API响应"""
        if AI_PROVIDER == "aliyun":
            return response_json["output"]["text"]
        else:
            # 默认OpenAI兼容格式
            return response_json["choices"][0]["message"]["content"]

# @cursor end 