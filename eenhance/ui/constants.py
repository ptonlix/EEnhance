import os
from colorama import Fore, Style

LOGO = """

███████╗███████╗███╗   ██╗██╗  ██╗ █████╗ ███╗   ██╗ ██████╗███████╗
██╔════╝██╔════╝████╗  ██║██║  ██║██╔══██╗████╗  ██║██╔════╝██╔════╝
█████╗  █████╗  ██╔██╗ ██║███████║███████║██╔██╗ ██║██║     █████╗  
██╔══╝  ██╔══╝  ██║╚██╗██║██╔══██║██╔══██║██║╚██╗██║██║     ██╔══╝  
███████╗███████╗██║ ╚████║██║  ██║██║  ██║██║ ╚████║╚██████╗███████╗
╚══════╝╚══════╝╚═╝  ╚═══╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝ ╚═════╝╚══════╝

一个创作效率提升工具 / A tool for improving creative efficiency

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
