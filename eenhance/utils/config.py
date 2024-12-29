"""
Configuration Module

This module handles the loading and management of configuration settings for the Podcastfy application.
It uses environment variables to securely store and access API keys and other sensitive information,
and a YAML file for non-sensitive configuration settings.
"""

import os
from dotenv import load_dotenv, find_dotenv
from typing import Any, Dict, Optional
import yaml


def get_config_path(config_file: str = "config.yaml"):
    """
    Get the path to the config.yaml file.

    Returns:
            str: The path to the config.yaml file.
    """
    try:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        # Look for config.yaml in the package root
        config_path = os.path.join(base_path, config_file)
        if os.path.exists(config_path):
            return config_path

        # If not found, look in the current working directory
        config_path = os.path.join(os.getcwd(), config_file)
        if os.path.exists(config_path):
            return config_path

        raise FileNotFoundError(f"{config_file} not found")

    except Exception as e:
        print(f"Error locating {config_file}: {str(e)}")
        return None


def singleton(cls):
    """单例模式装饰器"""
    _instance = {}

    def _singleton(*args, **kwargs):
        if cls not in _instance:
            _instance[cls] = cls(*args, **kwargs)
        return _instance[cls]

    return _singleton


@singleton
class Config:
    def __init__(self, config_file: str = "config.yaml"):
        """
        初始化Config类,加载环境变量和YAML配置。

        Args:
                config_file (str): YAML配置文件路径。默认为'config.yaml'。
        """
        # 尝试查找.env文件
        dotenv_path = find_dotenv(usecwd=True)
        if dotenv_path:
            load_dotenv(dotenv_path)
        else:
            print(
                "Warning: .env file not found. Using environment variables if available."
            )

        # 从环境变量加载API密钥
        self.GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
        self.GEMINI_API_BASE: str = os.getenv("GEMINI_API_BASE", "")
        self.OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
        self.OPENAI_API_BASE: str = os.getenv("OPENAI_API_BASE", "")
        self.ELEVENLABS_API_KEY: str = os.getenv("ELEVENLABS_API_KEY", "")
        self.ELEVENLABS_API_BASE: str = os.getenv("ELEVENLABS_API_BASE", "")
        self.FISH_API_KEY: str = os.getenv("FISH_API_KEY", "")

        config_path = get_config_path(config_file)
        if config_path:
            with open(config_path, "r") as file:
                self.config: Dict[str, Any] = yaml.safe_load(file)
        else:
            print("Could not locate config.yaml")
            self.config = {}

        # 根据YAML配置设置属性
        self._set_attributes()

    def _set_attributes(self):
        """根据当前配置设置属性"""
        for key, value in self.config.items():
            setattr(self, key.upper(), value)

        # 确保输出目录存在
        if "output_directories" in self.config:
            for dir_type, dir_path in self.config["output_directories"].items():
                os.makedirs(dir_path, exist_ok=True)

    def configure(self, **kwargs):
        """
        通过更新配置字典和相关属性来配置设置。

        Args:
                **kwargs: 表示要更新的配置键和值的关键字参数。
        """
        for key, value in kwargs.items():
            if key in self.config:
                self.config[key] = value
            elif key in [
                "JINA_API_KEY",
                "GEMINI_API_KEY",
                "OPENAI_API_KEY",
                "ELEVENLABS_API_KEY",
            ]:
                setattr(self, key, value)
            else:
                raise ValueError(f"Unknown configuration key: {key}")

        # 根据新配置更新属性
        self._set_attributes()

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """
        通过键获取配置值。

        Args:
                key (str): 要检索的配置键。
                default (Optional[Any]): 如果未找到键时的默认值。

        Returns:
                Any: 与键关联的值,如果未找到则返回默认值。
        """
        return self.config.get(key, default)


def load_config() -> Config:
    """
    Load and return a Config instance.

    Returns:
            Config: An instance of the Config class.
    """
    return Config()


def main() -> None:
    """
    Test the Config class and print configuration status.
    """
    # Create an instance of the Config class
    config = load_config()

    # Test each configuration value
    print("Testing Config class:")
    print(f"JINA_API_KEY: {'Set' if config.JINA_API_KEY else 'Not set'}")
    print(f"GEMINI_API_KEY: {'Set' if config.GEMINI_API_KEY else 'Not set'}")
    print(f"OPENAI_API_KEY: {'Set' if config.OPENAI_API_KEY else 'Not set'}")
    print(f"ELEVENLABS_API_KEY: {'Set' if config.ELEVENLABS_API_KEY else 'Not set'}")

    # Print a warning for any missing configuration
    missing_config = []
    for key in [
        "JINA_API_KEY",
        "GEMINI_API_KEY",
        "OPENAI_API_KEY",
        "ELEVENLABS_API_KEY",
    ]:
        if not getattr(config, key):
            missing_config.append(key)

    if missing_config:
        print("\nWarning: The following configuration values are missing:")
        for config_name in missing_config:
            print(f"- {config_name}")
        print("Please ensure these are set in your .env file.")
    else:
        print("\nAll configuration values are set.")

    # Test the get method with a default value
    print(f"\nTesting get method with default value:")
    print(f"NON_EXISTENT_KEY: {config.get('NON_EXISTENT_KEY', 'Default Value')}")


if __name__ == "__main__":
    main()
