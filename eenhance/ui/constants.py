import os
from colorama import Fore, Style

LOGO = """

███████╗███████╗███╗   ██╗██╗  ██╗ █████╗ ███╗   ██╗ ██████╗███████╗
██╔════╝██╔════╝████╗  ██║██║  ██║██╔══██╗████╗  ██║██╔════╝██╔════╝
█████╗  █████╗  ██╔██╗ ██║███████║███████║██╔██╗ ██║██║     █████╗  
██╔══╝  ██╔══╝  ██║╚██╗██║██╔══██║██╔══██║██║╚██╗██║██║     ██╔══╝  
███████╗███████╗██║ ╚████║██║  ██║██║  ██║██║ ╚████║╚██████╗███████╗
╚══════╝╚══════╝╚═╝  ╚═══╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝ ╚═════╝╚══════╝

基于LangGraph的研究报告播客生成Agent / LangGraph based research report podcast generation agent

作者/Author: Baird
版本/Version: 0.0.1
"""

# 终端颜色
PRIMARY_COLOR = Fore.CYAN
SECONDARY_COLOR = Fore.GREEN
ERROR_COLOR = Fore.RED
RESET_COLOR = Style.RESET_ALL

# 终端清屏命令
CLEAR_COMMAND = "cls" if os.name == "nt" else "clear"

# 进度条样式
PROGRESS_BAR_LENGTH = 50
PROGRESS_BAR_CHAR = "█"
