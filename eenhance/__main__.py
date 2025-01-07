from eenhance.main import graph
from eenhance.ui.utils import ConsoleUI
import time
import logging


logger = logging.getLogger(__name__)


def console_main():

    # 显示Logo和欢迎信息
    ui = ConsoleUI()
    ui.init_display_areas()  # 初始化显示区域
    time.sleep(1)

    total_steps = 5
    input_data = {"content_is_open": True}
    thread = {"configurable": {"thread_id": "1"}}
    # 初始化图
    ui.print_step(0, total_steps, "初始化系统")
    for update in graph.stream(
        input_data, thread, stream_mode="values", subgraphs=True
    ):
        pass
    ui.print_success("系统初始化完成")

    time.sleep(2)
    ui.print_step(1, total_steps, "获取文章内容")
    source = ui.get_input("请输入需要分析的文章地址: ")
    input_data["source"] = source
    state = graph.get_state(thread, subgraphs=True)
    graph.update_state(
        state.tasks[0].state.config, input_data, as_node="human_feedback"
    )
    ui.print_progress("内容获取", 1)
    for update in graph.stream(None, thread, stream_mode="updates", subgraphs=True):
        print("\n" + str(update))

    time.sleep(2)
    ui.clear_log_area()
    ui.print_success("文章内容获取完成")
    # 1. 获取文章内容
    while True:
        user_input = ui.get_input("确认是否再次获取文章内容 (y/n): ")
        if user_input.lower() == "y":
            source = ui.get_input("请输入需要分析的文章地址: ")
            input_data["content_is_open"] = True
            input_data["source"] = source
            state = graph.get_state(thread, subgraphs=True)
            graph.update_state(
                state.tasks[0].state.config, input_data, as_node="human_feedback"
            )
            ui.print_progress("内容获取", 1)
            for update in graph.stream(
                None, thread, stream_mode="updates", subgraphs=True
            ):
                print("\n" + str(update))
            time.sleep(2)
            ui.clear_log_area()
            ui.print_success("文章内容获取完成")
        elif user_input.lower():
            input_data["content_is_open"] = False
            state = graph.get_state(thread, subgraphs=True)
            graph.update_state(
                state.tasks[0].state.config, input_data, as_node="human_feedback"
            )
            for update in graph.stream(
                None, thread, stream_mode="updates", subgraphs=True
            ):
                pass
            break

    # 2. 生成研究主题
    ui.print_step(2, total_steps, "生成研究主题")
    additional_info = ui.get_input("请输入生成研究主题的额外信息: ")
    # input_data["out_content"] = (
    #     "文件分配方法对文件系统的性能和可靠性是基本且重要的。选择分配方法取决于各种因素，包括： "
    #     "预期文件大小和访问模式 性能要求 存储设备特性 可靠性要求 系统资源 现代文件系统通常采用混合方法，"
    #     "结合多种分配方法，以在不同使用案例中实现最优性能"
    # )
    input_data["additional_info"] = additional_info
    input_data["selected_topic"] = None
    input_data["regenerate"] = True

    state = graph.get_state(thread, subgraphs=True)
    graph.update_state(
        state.tasks[0].state.config, input_data, as_node="human_feedback"
    )

    with ui.progress_manager("研究主题生成中") as counter:
        total_estimated = 5
        for update in graph.stream(None, thread, stream_mode="updates", subgraphs=True):
            i = next(counter)  # 获取当前迭代次数
            progress = min(i / total_estimated, 1)  # 计算当前进度，确保不超过1
            ui.print_progress("研究主题生成中", progress)

    state = graph.get_state(thread, subgraphs=True)
    event = state.tasks[0].state.values
    while True:
        topic_list = ""
        for i, topic in enumerate(event["topics"], 1):
            topic_list += f"{i}. {topic}\n"
        ui.print_info(f"研究方向列表如下:\n{topic_list}")
        user_input = ui.get_input("确认是否需要生成研究方向 (y/n): ")
        if user_input.lower() == "y":
            state = graph.get_state(thread, subgraphs=True)
            additional_info = ui.get_input("请输入生成研究主题的额外信息: ")
            input_data["regenerate"] = True
            input_data["additional_info"] = additional_info
            graph.update_state(
                state.tasks[0].state.config, input_data, as_node="human_feedback"
            )

            with ui.progress_manager("研究主题生成中") as counter:
                total_estimated = 5
                for update in graph.stream(
                    None, thread, stream_mode="updates", subgraphs=True
                ):
                    i = next(counter)  # 获取当前迭代次数
                    progress = min(i / total_estimated, 1)  # 计算当前进度，确保不超过1
                    ui.print_progress("研究主题生成中", progress)
        else:
            while True:
                try:
                    choice = int(
                        ui.get_input(
                            f"可选主题列表:\n{topic_list}请输入主题序号(1-3): "
                        )
                    )
                    if 1 <= choice <= len(event["topics"]):
                        input_data["regenerate"] = False
                        input_data["selected_topic"] = event["topics"][choice - 1]
                        break
                    else:
                        ui.print_error("无效的选择,请输入1-3之间的数字")
                except ValueError:
                    ui.print_error("请输入有效的数字")

            graph.update_state(state.tasks[0].state.config, input_data)
            for update in graph.stream(
                None, thread, stream_mode="updates", subgraphs=True
            ):
                pass
            break

    # 3. 生成研究报告
    ui.print_step(3, total_steps, "生成研究报告")
    state = graph.get_state(thread, subgraphs=True)
    input_data["topic"] = input_data["selected_topic"]
    input_data["max_analysts"] = 3
    graph.update_state(state.tasks[0].state.config, input_data, as_node="human_input")

    with ui.progress_manager("采访者生成中") as counter:
        total_estimated = 10  # 估计的总迭代次数
        for update in graph.stream(None, thread, stream_mode="values", subgraphs=True):
            i = next(counter)  # 获取当前迭代次数
            progress = min(i / total_estimated, 1)  # 计算当前进度，确保不超过1
            ui.print_progress("采访者生成中", progress)

    while True:
        state = graph.get_state(thread, subgraphs=True)
        event = state.tasks[0].state.values
        analyst_list = ""
        for i, analyst in enumerate(event["analysts"], 1):
            analyst_list += f"{i}. {analyst}\n"
        user_input = ui.get_input(
            f"采访者列表如下:\n{analyst_list}\n确认使用采用这些采访者 (y/n): "
        )
        if user_input.lower() == "y":
            state = graph.get_state(thread, subgraphs=True)
            input_data["human_analyst_feedback"] = "approve"
            graph.update_state(
                state.tasks[0].state.config, input_data, as_node="human_feedback"
            )

            with ui.progress_manager("研究报告生成中") as counter:
                total_estimated = 100
                for update in graph.stream(
                    None, thread, stream_mode="updates", subgraphs=True
                ):
                    i = next(counter)  # 获取当前迭代次数
                    progress = min(i / total_estimated, 1)  # 计算当前进度，确保不超过1
                    ui.print_progress("研究报告生成中", progress)
                    print("\n" + str(update))

            break
        elif user_input.lower() == "n":
            state = graph.get_state(thread, subgraphs=True)
            input_data["human_analyst_feedback"] = "reject"
            graph.update_state(
                state.tasks[0].state.config, input_data, as_node="human_feedback"
            )
            with ui.progress_manager("采访者生成中") as counter:
                total_estimated = 10  # 估计的总迭代次数
                for update in graph.stream(
                    None, thread, stream_mode="values", subgraphs=True
                ):
                    i = next(counter)  # 获取当前迭代次数
                    progress = min(i / total_estimated, 1)  # 计算当前进度，确保不超过1
                    ui.print_progress("采访者生成中", progress)
            ui.clear_log_area()

        else:
            ui.print_error("无效输入，请重试")

    ui.init_display_areas()
    state = graph.get_state(thread, subgraphs=True)
    ui.print_success(f"研究报告生成成功,生成路径:{state.values['final_report_file']}")
    # 4. 生成博客文案
    ui.print_step(4, total_steps, "生成博客文案")
    state = graph.get_state(thread, subgraphs=True)
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
                None, thread, stream_mode="values", subgraphs=True
            ):
                i = next(counter)  # 获取当前迭代次数
                progress = min(i / total_estimated, 1)  # 计算当前进度，确保不超过1
                ui.print_progress("博客文案生成中", progress)

        while True:
            user_input = ui.get_input("确认是否需要再生成博客文案 (y/n): ")
            if user_input.lower() == "y":
                state = graph.get_state(thread, subgraphs=True)
                input_data["regenerate"] = True
                graph.update_state(state.tasks[0].state.config, input_data)

                with ui.progress_manager("博客文案生成中") as counter:
                    total_estimated = 5
                    for update in graph.stream(
                        None, thread, stream_mode="values", subgraphs=True
                    ):
                        i = next(counter)  # 获取当前迭代次数
                        progress = min(
                            i / total_estimated, 1
                        )  # 计算当前进度，确保不超过1
                        ui.print_progress("博客文案生成中", progress)
            elif user_input.lower() == "n":
                state = graph.get_state(thread, subgraphs=True)
                input_data["regenerate"] = False
                graph.update_state(state.tasks[0].state.config, input_data)
                for update in graph.stream(
                    None, thread, stream_mode="updates", subgraphs=True
                ):
                    pass
                break
            else:
                ui.print_error("无效输入，请重试")
    else:
        ui.print_success("跳过博客文案生成")
        return

    ui.init_display_areas()
    state = graph.get_state(thread, subgraphs=True)
    ui.print_success(f"博客文案生成成功,生成路径:{state.values['blog_file_path']}")
    # 5. 生成博客音频
    ui.print_step(5, total_steps, "生成博客音频")
    state = graph.get_state(thread, subgraphs=True)
    tts = ui.get_input("确认是否需要生成博客音频 (y/n): ")
    if tts.lower() == "y":
        tts_model = ui.get_input("请选择需要生成音频模型,如 fish edge: ")
        input_data["tts_provider"] = tts_model
        input_data["tts_is_open"] = True
        graph.update_state(
            state.tasks[0].state.config, input_data, as_node="human_feedback"
        )

        with ui.progress_manager("博客音频生成中") as counter:
            total_estimated = 5
            for update in graph.stream(
                None, thread, stream_mode="values", subgraphs=True
            ):
                i = next(counter)  # 获取当前迭代次数
                progress = min(i / total_estimated, 1)  # 计算当前进度，确保不超过1
                ui.print_progress("博客音频生成中", progress)

        while True:
            user_input = ui.get_input("确认是否需要重新生成博客音频 (y/n): ")
            if user_input.lower() == "y":
                tts_model = ui.get_input("请选择需要生成音频模型,如fish edge: ")
                input_data["tts_provider"] = tts_model
                input_data["tts_is_open"] = True
                state = graph.get_state(thread, subgraphs=True)
                graph.update_state(state.tasks[0].state.config, input_data)

                with ui.progress_manager("博客音频生成中") as counter:
                    total_estimated = 5
                    for update in graph.stream(
                        None, thread, stream_mode="values", subgraphs=True
                    ):
                        i = next(counter)  # 获取当前迭代次数
                        progress = min(
                            i / total_estimated, 1
                        )  # 计算当前进度，确保不超过1
                        ui.print_progress("博客音频生成中", progress)
            elif user_input.lower() == "n":
                input_data["tts_is_open"] = False
                state = graph.get_state(thread, subgraphs=True)
                graph.update_state(state.tasks[0].state.config, input_data)
                for update in graph.stream(
                    None, thread, stream_mode="updates", subgraphs=True
                ):
                    pass
                break
            else:
                ui.print_error("无效输入，请重试")
    else:
        ui.print_success("跳过音频生成")
        return

    ui.init_display_areas()
    state = graph.get_state(thread, subgraphs=True)
    ui.print_success(f"博客音频生成成功,生成路径:{state.values['audio_file_path']}")
    ui.print_info("EEnhance End～")


if __name__ == "__main__":
    try:
        console_main()
    except KeyboardInterrupt:
        print("\n\n程序已终止")
    except Exception as e:
        logger.exception(e)
        print(f"\n\n发生错误: {str(e)}")
