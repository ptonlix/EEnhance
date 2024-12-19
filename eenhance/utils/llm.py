"""
LLM配置模块

该模块提供了统一的LLM配置管理,包括模型选择、参数设置等。
"""

from langchain_openai import ChatOpenAI
from .config import load_config


def get_research_llm(model: str = None, temperature: float = 0) -> ChatOpenAI:
    """
    获取配置好的LLM实例。

    Args:
        model (str): 要使用的模型名称,如果为None则使用配置文件中的默认值
        temperature (float): 温度参数,控制输出的随机性

    Returns:
        ChatOpenAI: 配置好的LLM实例
    """
    config = load_config()

    # 如果没有指定model,使用配置文件中的默认值
    if model is None:
        model = config.get("research", {}).get("llm_model", "deepseek-chat")

    return ChatOpenAI(model=model, temperature=temperature)


def get_topic_llm(model: str = None, temperature: float = 0) -> ChatOpenAI:
    """
    获取配置好的LLM实例。

    Args:
        model (str): 要使用的模型名称,如果为None则使用配置文件中的默认值
        temperature (float): 温度参数,控制输出的随机性

    Returns:
        ChatOpenAI: 配置好的LLM实例
    """
    config = load_config()

    # 如果没有指定model,使用配置文件中的默认值
    if model is None:
        model = config.get("topic", {}).get("llm_model", "deepseek-chat")

    return ChatOpenAI(model=model, temperature=temperature)


# 创建默认LLM实例
default_research_llm = get_research_llm()
default_topic_llm = get_topic_llm()
