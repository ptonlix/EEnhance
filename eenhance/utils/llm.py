"""
LLM配置模块

该模块提供了统一的LLM配置管理,包括模型选择、参数设置等。
"""

from langchain_openai import ChatOpenAI
from .config import load_config
import os


class LLMFactory:
    """统一的LLM工厂类"""

    def __init__(self):
        self.config = load_config()

    def create_llm(
        self,
        use_case: str = "default",
        model: str = None,
        temperature: float = 0,
        **kwargs
    ) -> ChatOpenAI:
        """
        创建LLM实例的工厂方法

        Args:
            use_case: 使用场景,如 'research', 'blog', 'topic' 等
            model: 指定模型名称,若为None则从配置文件读取
            temperature: 温度参数
            **kwargs: 其他参数

        Returns:
            ChatOpenAI: 配置好的LLM实例
        """
        # 获取用例配置
        use_case_config = self.config.get(use_case, {})

        # 从配置获取默认model
        if model is None:
            model = use_case_config.get("llm_model", "deepseek-chat")

        # 获取对应的API配置
        api_key_env = use_case_config.get("api_key_env")
        api_base_env = use_case_config.get("api_base_env")

        # 创建基础参数
        llm_params = {"model": model, "temperature": temperature, **kwargs}

        # 如果配置了特定的API密钥和基础URL,则使用它们
        if api_key_env:
            llm_params["api_key"] = os.getenv(api_key_env)
        if api_base_env:
            llm_params["base_url"] = os.getenv(api_base_env)

        return ChatOpenAI(**llm_params)


# 创建全局单例
llm_factory = LLMFactory()
