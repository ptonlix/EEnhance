from eenhance.main import graph


def console_main():

    # 1.根据文章地址获取文章内容
    input_data = {"content_is_open": False}
    thread = {"configurable": {"thread_id": "1"}}
    for event in graph.stream(input_data, thread, stream_mode="values", subgraphs=True):
        pass

    # 1.获取文章内容
    while True:
        user_input = input("确认是否需要获取文章内容 (y/n): ")
        if user_input.lower() == "y":
            source = input("请输入需要分析的文章地址: ")
            input_data["content_is_open"] = True
            input_data["source"] = source

            state = graph.get_state(thread, subgraphs=True)
            graph.update_state(
                state.tasks[0].state.config, input_data, as_node="human_feedback"
            )
            # 再次运行图
            for update in graph.stream(
                None,
                thread,
                stream_mode="updates",
                subgraphs=True,
            ):
                print(update)
        else:
            input_data["content_is_open"] = False
            state = graph.get_state(thread, subgraphs=True)
            graph.update_state(
                state.tasks[0].state.config, input_data, as_node="human_feedback"
            )
            # 再次运行图
            for update in graph.stream(
                None,
                thread,
                stream_mode="updates",
                subgraphs=True,
            ):
                print(update)
            break

    # 2.根据文章内容获取主题

    additional_info = input("请输入生成研究主题的额外信息: ")
    input_data["out_content"] = (
        "文件分配方法对文件系统的性能和可靠性是基本且重要的。选择分配方法取决于各种因素，包括： 预期文件大小和访问模式 性能要求 存储设备特性 可靠性要求 系统资源 现代文件系统通常采用混合方法，结合多种分配方法，以在不同使用案例中实现最优性能"
    )
    input_data["additional_info"] = additional_info
    input_data["selected_topic"] = None
    input_data["regenerate"] = True

    state = graph.get_state(thread, subgraphs=True)
    graph.update_state(
        state.tasks[0].state.config, input_data, as_node="human_feedback"
    )

    # 再次运行图
    for update in graph.stream(
        None,
        thread,
        stream_mode="updates",
        subgraphs=True,
    ):
        print(update)
    while True:
        user_input = input("确认是否需要生成研究方向 (y/n): ")
        if user_input.lower() == "y":
            state = graph.get_state(thread, subgraphs=True)
            additional_info = input("请输入生成研究主题的额外信息: ")
            input_data["regenerate"] = True
            input_data["additional_info"] = additional_info
            graph.update_state(
                state.tasks[0].state.config, input_data, as_node="human_feedback"
            )
            # 再次运行图
            for update in graph.stream(
                None,
                thread,
                stream_mode="updates",
                subgraphs=True,
            ):
                print(update)
        else:
            # 显示主题列表供用户选择
            state = graph.get_state(thread, subgraphs=True)
            event = state.tasks[0].state.values
            for i, topic in enumerate(event["topics"], 1):
                print(f"{i}. {topic}")

            # 获取用户选择
            while True:
                try:
                    choice = int(input("\n请输入主题序号(1-3): "))
                    if 1 <= choice <= len(event["topics"]):
                        input_data["regenerate"] = False
                        input_data["selected_topic"] = event["topics"][choice - 1]
                        break
                    else:
                        print("无效的选择,请输入1-3之间的数字")
                except ValueError:
                    print("请输入有效的数字")

            graph.update_state(state.tasks[0].state.config, input_data)
            # 再次运行图
            for update in graph.stream(
                None,
                thread,
                stream_mode="updates",
                subgraphs=True,
            ):
                print(update)
            break

    # 3.根据主题生成研究报告
    state = graph.get_state(thread, subgraphs=True)
    input_data["topic"] = input_data["selected_topic"]
    input_data["max_analysts"] = 3
    graph.update_state(state.tasks[0].state.config, input_data, as_node="human_input")
    # 再次运行图
    for update in graph.stream(
        None,
        thread,
        stream_mode="values",
        subgraphs=True,
    ):
        print(update)

    while True:
        user_input = input("确认使用采用这些访问者 (y/n): ")
        if user_input.lower() == "y":
            state = graph.get_state(thread, subgraphs=True)
            input_data["human_analyst_feedback"] = "approve"
            graph.update_state(state.tasks[0].state.config, input_data)
            # 再次运行图
            for update in graph.stream(
                None,
                thread,
                stream_mode="updates",
                subgraphs=True,
            ):
                print(update)
        else:
            state = graph.get_state(thread, subgraphs=True)
            input_data["human_analyst_feedback"] = "reject"
            graph.update_state(state.tasks[0].state.config, input_data)
            # 再次运行图
            for update in graph.stream(
                None,
                thread,
                stream_mode="updates",
                subgraphs=True,
            ):
                print(update)
            break
    # 4.根据研究报告生成博客文案
    state = graph.get_state(thread, subgraphs=True)
    input_data["topic"] = input_data["selected_topic"]
    input_data["max_analysts"] = 3
    graph.update_state(state.tasks[0].state.config, input_data, as_node="human_input")
    # 再次运行图
    for update in graph.stream(
        None,
        thread,
        stream_mode="values",
        subgraphs=True,
    ):
        print(update)
    # 5.根据博客文案生成博客音频


console_main()
