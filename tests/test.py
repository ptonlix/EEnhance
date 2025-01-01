from eenhance.tts import tts_assistant
from eenhance.topic import topic_assistant
from eenhance.research import research_assistant
from eenhance.blog import blog_assistant
import os
from eenhance.constants import PROJECT_ROOT_PATH
from langchain_community.tools.tavily_search import TavilySearchResults


def test_tavily_search():
    # Search
    tavily_search = TavilySearchResults(max_results=3)

    # Search
    search_docs = tavily_search.invoke("LangChain")
    print(search_docs)
    for doc in search_docs:
        print(doc)


def test_tts_assistant():
    # 创建线程配置
    file_path = os.path.join(
        PROJECT_ROOT_PATH,
        "data/transcripts/research_report_blog.txt",
    )
    input_data = {
        "blog_content": "",
        "blog_file_path": file_path,
        "tts_provider": "fish",
        "tts_is_open": True,
    }
    thread = {"configurable": {"thread_id": "1"}}

    # 第一次运行图直到中断
    for event in tts_assistant.graph.stream(input_data, thread, stream_mode="values"):
        print(event)

    # 获取用户输入
    user_input = input("是否需要重新生成音频? (y/n): ")

    # 再次运行图
    for event in tts_assistant.graph.stream(
        None,
        thread,
        stream_mode="values",
    ):
        print(event)


def test_blog_assistant():
    input_data = {
        "research_report": "人工智能和机器学习正在改变我们的生活方式。深度学习模型能够识别图像、理解自然语言,并在各个领域取得突破性进展。",
        "research_report_file": "data/reports/research_report.txt",
        "regenerate": False,
    }
    thread = {"configurable": {"thread_id": "1"}}
    for event in blog_assistant.graph.stream(input_data, thread, stream_mode="values"):
        print(event)

    # 获取用户输入
    while True:
        user_input = input("是否需要生成博客文案? (y/n): ")
        if user_input.lower() == "y":
            input_data["regenerate"] = True
            # 更新状态
            blog_assistant.graph.update_state(
                thread, input_data, as_node="human_feedback"
            )
            # 再次运行图
            for event in blog_assistant.graph.stream(
                None,
                thread,
                stream_mode="values",
            ):
                print(event)
        else:
            break


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


def test_research_assistant():
    input_data = {"topic": "人工智能在医疗领域的应用", "max_analysts": 3}
    thread = {"configurable": {"thread_id": "1"}}
    for event in research_assistant.graph.stream(
        input_data, thread, stream_mode="values"
    ):
        # Review
        analysts = event.get("analysts", "")
        if analysts:
            for analyst in analysts:
                print(f"Name: {analyst.name}")
                print(f"Affiliation: {analyst.affiliation}")
                print(f"Role: {analyst.role}")
                print(f"Description: {analyst.description}")
                print("-" * 50)
    # We now update the state as if we are the human_feedback node
    human_feedback = input("请输入反馈: ")
    research_assistant.graph.update_state(
        thread,
        {"human_analyst_feedback": human_feedback},
        as_node="human_feedback",
    )

    for event in research_assistant.graph.stream(None, thread, stream_mode="values"):
        # Review
        analysts = event.get("analysts", "")
        if analysts:
            for analyst in analysts:
                print(f"Name: {analyst.name}")
                print(f"Affiliation: {analyst.affiliation}")
                print(f"Role: {analyst.role}")
                print(f"Description: {analyst.description}")
                print("-" * 50)
    # We now update the state as if we are the human_feedback node
    human_feedback = input("请输入反馈: ")
    research_assistant.graph.update_state(
        thread,
        {"human_analyst_feedback": human_feedback},
        as_node="human_feedback",
    )

    # Continue
    for event in research_assistant.graph.stream(None, thread, stream_mode="updates"):
        print("--Node--")
        node_name = next(iter(event.keys()))
        print(node_name)

    final_state = research_assistant.graph.get_state(thread)
    report = final_state.values.get("final_report")
    print(report)


if __name__ == "__main__":
    from eenhance.utils.config import load_config

    config = load_config()
    print(config)

    test_tavily_search()
    # test_topic_assistant()

    # test_research_assistant()

    # test_tts_assistant()
    # test_blog_assistant()
