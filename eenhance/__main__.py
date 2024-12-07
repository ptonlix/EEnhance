from eenhance.topic import topic_assistant


def test_topic_assistant():
    # 准备测试输入数据
    input_data = {
        "content": "人工智能和机器学习正在改变我们的生活方式。深度学习模型能够识别图像、理解自然语言,并在各个领域取得突破性进展。",
        "additional_info": "希望研究AI在医疗领域的应用",
        "selected_topic": None,
        "regenerate": False,
    }

    # 创建线程配置
    thread = {"configurable": {"thread_id": "1"}}

    # 第一次运行图直到中断
    for event in topic_assistant.graph.stream(input_data, thread, stream_mode="values"):
        print(event)

    # 获取用户输入
    user_input = input("是否需要重新生成主题? (y/n): ")
    if user_input.lower() == "y":
        input_data["regenerate"] = True
    else:
        input_data["regenerate"] = False
    # 获取用户输入并更新状态
    print(input_data)

    # 更新状态
    topic_assistant.graph.update_state(thread, input_data, as_node="human_feedback")

    # 再次运行图
    for event in topic_assistant.graph.stream(
        None,
        thread,
        stream_mode="values",
    ):
        print(event)
    # 显示主题列表供用户选择
    print("\n请选择一个主题:")
    for i, topic in enumerate(event["topics"], 1):
        print(f"{i}. {topic}")

    # 获取用户选择
    while True:
        try:
            choice = int(input("\n请输入主题序号(1-3): "))
            if 1 <= choice <= len(event["topics"]):
                input_data["selected_topic"] = event["topics"][choice - 1]
                break
            else:
                print("无效的选择,请输入1-3之间的数字")
        except ValueError:
            print("请输入有效的数字")

    print(input_data)

    # 更新状态
    topic_assistant.graph.update_state(thread, input_data, as_node="human_feedback")

    # 最后运行图
    for event in topic_assistant.graph.stream(
        None,
        thread,
        stream_mode="values",
    ):
        print(event)


if __name__ == "__main__":
    from eenhance.utils.config import load_config

    config = load_config()
    print(config)

    test_topic_assistant()
