import os
import sys
import shutil
from .constants import (
    CLEAR_COMMAND,
    PRIMARY_COLOR,
    PROGRESS_BAR_CHAR,
    PROGRESS_BAR_LENGTH,
    SECONDARY_COLOR,
    RESET_COLOR,
    ERROR_COLOR,
    LOGO,
)
import itertools
from contextlib import contextmanager


class ConsoleUI:
    def __init__(self):
        # 获取终端大小
        self.terminal_width, self.terminal_height = shutil.get_terminal_size()
        # Windows系统启用ANSI支持
        if os.name == "nt":
            os.system("color")

        # 定义三个区域的高度比例
        self.top_height = int(self.terminal_height * 0.2)  # 顶部区域占20%
        self.middle_height = int(self.terminal_height * 0.5)  # 中间区域占50%
        self.bottom_height = (
            self.terminal_height - self.top_height - self.middle_height
        )  # 底部区域占剩余30%

        # 初始化区域起始位置
        self.top_start = 0
        self.middle_start = self.top_height
        self.bottom_start = self.middle_start + self.middle_height

        self.middle_content = []  # 添加一个列表来存储中间区域的内容
        self.current_middle_line = self.middle_start  # 跟踪中间区域当前打印位置

    def init_display_areas(self):
        """初始化显示区域"""
        self.clear_screen()
        self.refresh_display()

    def refresh_display(self):
        """刷新显示，确保Logo和分隔线始终可见"""
        self.print_logo()  # 始终打印顶部区域的Logo
        self.draw_separator(self.top_height - 1, "交互面板")  # 始终显示顶部分隔线
        self.draw_separator(
            self.middle_start + self.middle_height - 1, "日志信息"
        )  # 显示中间分隔线

    def clear_log_area(self):
        self.init_display_areas()
        self.print_to_middle_area()

    def draw_separator(self, y_position, keyword=""):
        """在指定位置绘制分隔线,可以在中间显示关键字"""
        sys.stdout.write(f"\033[{y_position};0H")  # 移动到指定位置

        if keyword:
            # 计算关键字两边的分隔线长度
            side_length = (
                self.terminal_width - len(keyword) - 2
            ) // 2  # -2是为了留出关键字两边的空格
            left_sep = "─" * (side_length - 5)
            right_sep = "─" * (self.terminal_width - side_length - len(keyword) - 2)
            sys.stdout.write(
                f"{left_sep} {PRIMARY_COLOR}{keyword}{RESET_COLOR} {right_sep}"
            )
        else:
            sys.stdout.write("─" * self.terminal_width)

        sys.stdout.flush()

    def print_to_area(
        self, message: str, area_start: int, area_height: int, color: str = None
    ):
        """在指定区域打印消息"""
        # 清除该区域
        for i in range(area_height):
            sys.stdout.write(f"\033[{area_start + i};0H\033[K")

        # 移动到区域起始位置
        sys.stdout.write(f"\033[{area_start};0H")

        # 添加颜色支持
        if color:
            sys.stdout.write(f"{color}{message}{RESET_COLOR}")
        else:
            sys.stdout.write(message)

        # 重新绘制分隔线
        if area_start == self.top_start:  # 如果是顶部区域
            self.draw_separator(self.top_height - 1, "交互面板")
        elif area_start == self.middle_start:  # 如果是中间区域
            self.draw_separator(self.middle_start + self.middle_height - 1, "日志信息")

        sys.stdout.flush()

    def print_to_top_area(self, message: str = "", color: str = None):
        """在顶部区域打印消息"""
        self.print_to_area(message, self.top_start, self.top_height, color)

    def print_to_middle_area(self, message: str = "", color: str = None):
        """在中间区域打印消息，采用追加模式"""
        # 存储消息
        self.middle_content.append((message, color))

        # 如果超出显示范围，移除最早的消息
        max_lines = self.middle_height - 2  # 预留空间给分隔线
        if len(self.middle_content) > max_lines:
            self.middle_content = self.middle_content[-max_lines:]

        # 清除中间区域
        for i in range(self.middle_height):
            sys.stdout.write(f"\033[{self.middle_start + i};0H\033[K")

        # 重新打印所有存储的消息
        current_line = self.middle_start
        for msg, clr in self.middle_content:
            sys.stdout.write(f"\033[{current_line};0H")
            if clr:
                if len(msg) == 0:
                    continue
                sys.stdout.write(f"{clr}{msg}{RESET_COLOR}")
            else:
                sys.stdout.write(msg)
            current_line += 1

        # 重新绘制分隔线
        self.draw_separator(self.middle_start + self.middle_height - 1, "日志信息")

        sys.stdout.flush()

    def print_to_bottom_area(self, message: str = "", color: str = None):
        """在底部区域打印消息"""
        self.print_to_area(message, self.bottom_start, self.bottom_height, color)

    @staticmethod
    def clear_screen():
        os.system(CLEAR_COMMAND)

    def print_logo(self):
        """在顶部区域打印Logo"""
        self.print_to_top_area(PRIMARY_COLOR + LOGO + RESET_COLOR)

    def print_step(self, step_number, total_steps, description):
        step_info = f"\n{PRIMARY_COLOR}[步骤 {step_number}/{total_steps}] {description}{RESET_COLOR}\n"
        self.print_to_middle_area(step_info, SECONDARY_COLOR)

    def print_progress(self, description: str, progress: float):
        """在底部区域打印进度条"""
        filled_length = int(PROGRESS_BAR_LENGTH * progress)
        bar = PROGRESS_BAR_CHAR * filled_length + "-" * (
            PROGRESS_BAR_LENGTH - filled_length
        )
        progress_text = f"{description} |{bar}| {progress*100:.1f}%"
        self.print_to_bottom_area(progress_text, SECONDARY_COLOR)

    def print_info(self, message: str):
        """在底部区域打印信息"""
        self.print_to_bottom_area(f"{message}", SECONDARY_COLOR)

    def print_success(self, message: str):
        """在底部区域打印成功消息"""
        self.print_to_bottom_area(f"✓ {message}", SECONDARY_COLOR)

    def print_error(self, message: str):
        """在底部区域打印错误消息"""
        self.print_to_bottom_area(f"✗ {message}", ERROR_COLOR)

    def get_input(self, prompt: str = "", offset: int = 0) -> str:
        """在中间区域获取用户输入"""
        # 保存当前光标位置
        sys.stdout.write("\033[s")

        # 获取当前中间区域的最后一行位置
        last_line = self.middle_start + self.middle_height - 10

        # 移动到中间区域的最后一行
        sys.stdout.write(f"\033[{last_line};0H")

        # 清除当前行并打印提示信息
        sys.stdout.write("\033[K" + prompt)
        sys.stdout.flush()

        # 获取用户输入
        user_input = input()

        # 恢复光标位置
        sys.stdout.write("\033[u")

        return user_input

    @contextmanager
    def progress_manager(self, message):
        counter = itertools.count(start=1)  # 创建一个计数器
        try:
            yield counter  # 允许循环中访问计数器
        finally:
            # 确保进度条完成
            self.print_progress(message, 1)
