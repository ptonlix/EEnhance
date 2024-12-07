import pytest
from eenhance.topic.topic_assistant import graph


def test_topic_assistant_workflow():
    """测试主题助手的完整工作流程"""

    # 准备测试数据
    input_data = {
        "content": "人工智能和机器学习正在改变我们的生活方式。深度学习模型能够识别图像、理解自然语言,并在各个领域取得突破性进展。",
        "additional_info": "希望研究AI在医疗领域的应用",
        "selected_topic": None,
        "regenerate": False,
    }

    thread = {"configurable": {"thread_id": "test_1"}}

    # 测试初始状态
    events = list(graph.stream(input_data, thread, stream_mode="values"))
    assert len(events) > 0

    # 测试重新生成主题
    input_data["regenerate"] = True
    graph.update_state(thread, input_data, as_node="human_feedback")
    events = list(graph.stream(None, thread, stream_mode="values"))
    assert len(events) > 0

    # 测试选择主题后结束
    input_data["selected_topic"] = "AI在医疗诊断中的应用研究"
    input_data["regenerate"] = False
    graph.update_state(thread, input_data, as_node="human_feedback")
    events = list(graph.stream(None, thread, stream_mode="values"))
    assert len(events) > 0


def test_topic_assistant_error_handling():
    """测试错误处理情况"""

    # 测试空内容
    input_data = {
        "content": "",
        "additional_info": None,
        "selected_topic": None,
        "regenerate": True,
    }

    thread = {"configurable": {"thread_id": "test_2"}}

    events = list(graph.stream(input_data, thread, stream_mode="values"))
    assert len(events) > 0


def test_topic_assistant_router():
    """测试路由逻辑"""

    # 测试直接结束的情况
    input_data = {
        "content": "测试内容",
        "additional_info": None,
        "selected_topic": "已选择的主题",
        "regenerate": False,
    }

    thread = {"configurable": {"thread_id": "test_3"}}

    events = list(graph.stream(input_data, thread, stream_mode="values"))
    assert len(events) > 0


if __name__ == "__main__":
    pytest.main(["-v", "test_topic_assistant.py"])
