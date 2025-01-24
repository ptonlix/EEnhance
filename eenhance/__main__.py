from eenhance.main import graph
from eenhance.ui.utils import ConsoleUI
import time
import logging

logger = logging.getLogger(__name__)

# 常量定义
TOTAL_STEPS = 6
DEFAULT_THREAD = {"configurable": {"thread_id": "1"}}


def initialize_system(ui):
    """初始化系统"""
    ui.print_step(0, TOTAL_STEPS, "初始化系统")
    input_data = {"content_is_open": True}  # 初始化 input_data
    for update in graph.stream(
        input_data, DEFAULT_THREAD, stream_mode="values", subgraphs=True
    ):
        pass
    ui.print_success("系统初始化完成")
    time.sleep(2)


def fetch_article_content(ui):
    """获取文章内容"""
    ui.print_step(1, TOTAL_STEPS, "获取文章内容")
    source = ui.get_input("请输入需要分析的文章地址: ")
    input_data = {"source": source, "content_is_open": True}  # 初始化 input_data
    state = graph.get_state(DEFAULT_THREAD, subgraphs=True)
    graph.update_state(
        state.tasks[0].state.config, input_data, as_node="human_feedback"
    )
    ui.print_progress("内容获取", 1)
    for update in graph.stream(
        None, DEFAULT_THREAD, stream_mode="updates", subgraphs=True
    ):
        print("\n" + str(update))
    time.sleep(2)
    ui.clear_log_area()
    ui.print_success("文章内容获取完成")
    return input_data  # 返回 input_data 以便后续使用


def regenerate_article_content(ui, input_data):
    """重新获取文章内容"""
    while True:
        user_input = ui.get_input("确认是否需要重新获取文章内容 (y/n): ")
        if user_input.lower() == "y":
            source = ui.get_input("请输入需要分析的文章地址: ")
            input_data["source"] = source
            input_data["content_is_open"] = True
            state = graph.get_state(DEFAULT_THREAD, subgraphs=True)
            graph.update_state(
                state.tasks[0].state.config, input_data, as_node="human_feedback"
            )
            ui.print_progress("内容获取", 1)
            for update in graph.stream(
                None, DEFAULT_THREAD, stream_mode="updates", subgraphs=True
            ):
                print("\n" + str(update))
            time.sleep(2)
            ui.clear_log_area()
            ui.print_success("文章内容获取完成")
        else:
            input_data["content_is_open"] = False
            state = graph.get_state(DEFAULT_THREAD, subgraphs=True)
            graph.update_state(
                state.tasks[0].state.config, input_data, as_node="human_feedback"
            )
            for update in graph.stream(
                None, DEFAULT_THREAD, stream_mode="updates", subgraphs=True
            ):
                pass
            break
    return input_data  # 返回 input_data 以便后续使用


def generate_research_topics(ui, input_data):
    """生成研究主题"""
    ui.print_step(2, TOTAL_STEPS, "生成研究主题")
    additional_info = ui.get_input("请为生成研究主题提供额外信息（可选输入无）: ")
    input_data.update(
        {"additional_info": additional_info, "selected_topic": None, "regenerate": True}
    )  # 更新 input_data
    state = graph.get_state(DEFAULT_THREAD, subgraphs=True)
    graph.update_state(
        state.tasks[0].state.config, input_data, as_node="human_feedback"
    )

    with ui.progress_manager("研究主题生成中") as counter:
        total_estimated = 5
        for update in graph.stream(
            None, DEFAULT_THREAD, stream_mode="updates", subgraphs=True
        ):
            i = next(counter)
            progress = min(i / total_estimated, 1)
            ui.print_progress("研究主题生成中", progress)

    while True:
        state = graph.get_state(DEFAULT_THREAD, subgraphs=True)
        event = state.tasks[0].state.values
        topic_list = "\n".join(
            [f"{i}. {topic}" for i, topic in enumerate(event["topics"], 1)]
        )
        ui.print_info(f"研究方向列表如下:\n{topic_list}")
        user_input = ui.get_input("确认是否需要重新生成研究方向 (y/n): ")
        if user_input.lower() == "y":
            additional_info = ui.get_input("请输入生成研究主题的额外信息: ")
            input_data.update(
                {"regenerate": True, "additional_info": additional_info}
            )  # 更新 input_data
            graph.update_state(
                state.tasks[0].state.config, input_data, as_node="human_feedback"
            )

            with ui.progress_manager("研究主题生成中") as counter:
                total_estimated = 5
                for update in graph.stream(
                    None, DEFAULT_THREAD, stream_mode="updates", subgraphs=True
                ):
                    i = next(counter)
                    progress = min(i / total_estimated, 1)
                    ui.print_progress("研究主题生成中", progress)
        else:
            while True:
                try:
                    choice = int(
                        ui.get_input(
                            f"可选主题列表:\n{topic_list}\n请输入主题序号(1-3): "
                        )
                    )
                    if 1 <= choice <= len(event["topics"]):
                        input_data.update(
                            {
                                "regenerate": False,
                                "selected_topic": event["topics"][choice - 1],
                            }
                        )  # 更新 input_data
                        break
                    else:
                        ui.print_error("无效的选择,请输入1-3之间的数字")
                except ValueError:
                    ui.print_error("请输入有效的数字")

            graph.update_state(state.tasks[0].state.config, input_data)
            for update in graph.stream(
                None, DEFAULT_THREAD, stream_mode="updates", subgraphs=True
            ):
                pass
            break
    return input_data  # 返回 input_data 以便后续使用


def generate_research_report(ui, input_data):
    """生成研究报告"""
    ui.print_step(3, TOTAL_STEPS, "生成研究报告")
    state = graph.get_state(DEFAULT_THREAD, subgraphs=True)
    input_data.update(
        {"topic": input_data["selected_topic"], "max_analysts": 3}
    )  # 更新 input_data
    graph.update_state(state.tasks[0].state.config, input_data, as_node="human_input")

    with ui.progress_manager("采访者生成中") as counter:
        total_estimated = 10
        for update in graph.stream(
            None, DEFAULT_THREAD, stream_mode="values", subgraphs=True
        ):
            i = next(counter)
            progress = min(i / total_estimated, 1)
            ui.print_progress("采访者生成中", progress)

    while True:
        state = graph.get_state(DEFAULT_THREAD, subgraphs=True)
        event = state.tasks[0].state.values
        analyst_list = "\n".join(
            [f"{i}. {analyst}" for i, analyst in enumerate(event["analysts"], 1)]
        )
        user_input = ui.get_input(
            f"采访者列表如下:\n{analyst_list}\n确认是否使用采用这些采访者 (y/n): "
        )
        if user_input.lower() == "y":
            input_data["human_analyst_feedback"] = "approve"
            graph.update_state(
                state.tasks[0].state.config, input_data, as_node="human_feedback"
            )

            with ui.progress_manager("研究报告生成中") as counter:
                total_estimated = 100
                for update in graph.stream(
                    None, DEFAULT_THREAD, stream_mode="updates", subgraphs=True
                ):
                    i = next(counter)
                    progress = min(i / total_estimated, 1)
                    ui.print_progress("研究报告生成中", progress)
                    print("\n" + str(update))

            break
        elif user_input.lower() == "n":
            input_data["human_analyst_feedback"] = "reject"
            graph.update_state(
                state.tasks[0].state.config, input_data, as_node="human_feedback"
            )
            with ui.progress_manager("采访者生成中") as counter:
                total_estimated = 10
                for update in graph.stream(
                    None, DEFAULT_THREAD, stream_mode="values", subgraphs=True
                ):
                    i = next(counter)
                    progress = min(i / total_estimated, 1)
                    ui.print_progress("采访者生成中", progress)
            ui.clear_log_area()
        else:
            ui.print_error("无效输入，请重试")

    ui.init_display_areas()
    state = graph.get_state(DEFAULT_THREAD, subgraphs=True)
    ui.print_success(f"研究报告生成成功,生成路径:{state.values['final_report_file']}")
    return input_data  # 返回 input_data 以便后续使用


def generate_blog_post(ui, input_data):
    """生成博客文案"""
    ui.print_step(4, TOTAL_STEPS, "生成博客文案")
    state = graph.get_state(DEFAULT_THREAD, subgraphs=True)
    reg = ui.get_input("确认是否需要生成博客文案 (y/n): ")
    if reg.lower() == "y":
        input_data["regenerate"] = True
        graph.update_state(
            state.tasks[0].state.config, input_data, as_node="human_feedback"
        )
        ui.print_progress("博客文案生成", 1)
        with ui.progress_manager("博客文案生成中") as counter:
            total_estimated = 5
            for update in graph.stream(
                None, DEFAULT_THREAD, stream_mode="values", subgraphs=True
            ):
                i = next(counter)
                progress = min(i / total_estimated, 1)
                ui.print_progress("博客文案生成中", progress)

        while True:
            user_input = ui.get_input("确认是否需要重新生成博客文案 (y/n): ")
            state = graph.get_state(DEFAULT_THREAD, subgraphs=True)
            if user_input.lower() == "y":
                input_data["regenerate"] = True
                graph.update_state(state.tasks[0].state.config, input_data)

                with ui.progress_manager("博客文案生成中") as counter:
                    total_estimated = 5
                    for update in graph.stream(
                        None, DEFAULT_THREAD, stream_mode="values", subgraphs=True
                    ):
                        i = next(counter)
                        progress = min(i / total_estimated, 1)
                        ui.print_progress("博客文案生成中", progress)
            elif user_input.lower() == "n":
                input_data["regenerate"] = False
                graph.update_state(state.tasks[0].state.config, input_data)
                for update in graph.stream(
                    None, DEFAULT_THREAD, stream_mode="values", subgraphs=True
                ):
                    pass
                break
            else:
                ui.print_error("无效输入，请重试")
    else:
        ui.print_success("跳过博客文案生成")
        return input_data  # 返回 input_data 以便后续使用

    ui.init_display_areas()
    state = graph.get_state(DEFAULT_THREAD, subgraphs=True)
    ui.print_success(f"博客文案生成成功,生成路径:{state.values['blog_file_path']}")
    return input_data  # 返回 input_data 以便后续使用


def generate_blog_audio(ui, input_data):
    """生成博客音频"""
    ui.print_step(5, TOTAL_STEPS, "生成博客音频")
    state = graph.get_state(DEFAULT_THREAD, subgraphs=True)
    tts = ui.get_input("确认是否需要生成博客音频 (y/n): ")
    if tts.lower() == "y":
        tts_model = ui.get_input("请选择需要生成音频模型（可输入fish|edge）: ")
        input_data.update(
            {"tts_provider": tts_model, "tts_is_open": True}
        )  # 更新 input_data
        graph.update_state(
            state.tasks[0].state.config, input_data, as_node="human_feedback"
        )

        with ui.progress_manager("博客音频生成中") as counter:
            total_estimated = 5
            for update in graph.stream(
                None, DEFAULT_THREAD, stream_mode="values", subgraphs=True
            ):
                i = next(counter)
                progress = min(i / total_estimated, 1)
                ui.print_progress("博客音频生成中", progress)

        while True:
            state = graph.get_state(DEFAULT_THREAD, subgraphs=True)
            user_input = ui.get_input("确认是否需要重新生成博客音频 (y/n): ")
            if user_input.lower() == "y":
                tts_model = ui.get_input("请选择需要生成音频模型（可输入fish|edge）: ")
                input_data.update(
                    {"tts_provider": tts_model, "tts_is_open": True}
                )  # 更新 input_data
                graph.update_state(state.tasks[0].state.config, input_data)

                with ui.progress_manager("博客音频生成中") as counter:
                    total_estimated = 5
                    for update in graph.stream(
                        None, DEFAULT_THREAD, stream_mode="values", subgraphs=True
                    ):
                        i = next(counter)
                        progress = min(i / total_estimated, 1)
                        ui.print_progress("博客音频生成中", progress)
            elif user_input.lower() == "n":
                input_data["tts_is_open"] = False
                graph.update_state(state.tasks[0].state.config, input_data)
                for update in graph.stream(
                    None, DEFAULT_THREAD, stream_mode="updates", subgraphs=True
                ):
                    pass
                break
            else:
                ui.print_error("无效输入，请重试")
    else:
        ui.print_success("跳过音频生成")
        return input_data  # 返回 input_data 以便后续使用

    ui.init_display_areas()
    state = graph.get_state(DEFAULT_THREAD, subgraphs=True)
    ui.print_success(f"博客音频生成成功,生成路径:{state.values['audio_file_path']}")
    ui.print_step(6, TOTAL_STEPS, "EEnhance工作流已完成, 请检查data目录获取文件")
    return input_data  # 返回 input_data 以便后续使用


def console_main():
    """主函数"""
    ui = ConsoleUI()
    ui.init_display_areas()  # 初始化显示区域
    time.sleep(1)

    initialize_system(ui)
    input_data = fetch_article_content(ui)
    input_data = regenerate_article_content(ui, input_data)
    input_data = generate_research_topics(ui, input_data)
    input_data = generate_research_report(ui, input_data)
    input_data = generate_blog_post(ui, input_data)
    input_data = generate_blog_audio(ui, input_data)


if __name__ == "__main__":
    try:
        console_main()
    except KeyboardInterrupt:
        print("\n\n程序已终止")
    except Exception as e:
        logger.exception(e)
        print(f"\n\n发生错误: {str(e)}")
