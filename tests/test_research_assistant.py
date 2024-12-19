import pytest
from eenhance.research.research_assistant import graph
from eenhance.research.research_assistant import Analyst, Perspectives


def test_research_assistant_workflow():
    """测试研究助手的完整工作流程"""

    # 准备测试数据
    input_data = {
        "topic": "人工智能在医疗领域的应用",
        "max_analysts": 2,
        "human_analyst_feedback": "approve",
    }

    thread = {"configurable": {"thread_id": "test_1"}}

    # 测试创建分析师
    events = list(graph.stream(input_data, thread, stream_mode="values"))
    assert len(events) > 0
    assert "analysts" in events[0]
    analysts = events[0]["analysts"]
    assert isinstance(analysts, list)
    assert len(analysts) <= input_data["max_analysts"]

    # 验证分析师对象
    for analyst in analysts:
        assert isinstance(analyst, Analyst)
        assert analyst.name
        assert analyst.role
        assert analyst.affiliation
        assert analyst.description


def test_research_assistant_error_handling():
    """测试错误处理情况"""

    # 测试���效输入
    input_data = {"topic": "", "max_analysts": 0, "human_analyst_feedback": None}

    thread = {"configurable": {"thread_id": "test_2"}}

    with pytest.raises(ValueError):
        list(graph.stream(input_data, thread, stream_mode="values"))


def test_research_assistant_feedback():
    """测试人工反馈流程"""

    input_data = {
        "topic": "区块链技术的未来发展",
        "max_analysts": 2,
        "human_analyst_feedback": "需要更多关注金融科技领域的分析师",
    }

    thread = {"configurable": {"thread_id": "test_3"}}

    # 测试反馈后重新生成分析师
    events = list(graph.stream(input_data, thread, stream_mode="values"))
    assert len(events) > 0

    # 验证新生成的分析师是否符合反馈要求
    analysts = events[0]["analysts"]
    assert any("金融" in analyst.description for analyst in analysts)


if __name__ == "__main__":
    pytest.main(["-v", "test_research_assistant.py"])
