import operator
from pydantic import BaseModel, Field
from typing import Annotated, List
from typing_extensions import TypedDict


from langgraph.graph import MessagesState


class Analyst(BaseModel):
    affiliation: str = Field(
        description="分析师的主要隶属机构。",
    )
    name: str = Field(description="分析师的姓名。")
    role: str = Field(
        description="分析师在该主题背景下的角色。",
    )
    description: str = Field(
        description="分析师在主题背景下的关注、关注点和动机。",
    )

    @property
    def persona(self) -> str:
        return f"姓名: {self.name}\n角色: {self.role}\n隶属关系: {self.affiliation}\n描述: {self.description}\n"


class Perspectives(BaseModel):
    analysts: List[Analyst] = Field(
        description="分析师的全面列表，包括他们的角色和隶属关系。",
    )


class GenerateAnalystsState(TypedDict):
    topic: str  # Research topic
    max_analysts: int  # Number of analysts
    human_analyst_feedback: str  # Human feedback
    analysts: List[Analyst]  # Analyst asking questions


class InterviewState(MessagesState):
    max_num_turns: int  # Number turns of conversation
    context: Annotated[list, operator.add]  # Source docs
    analyst: Analyst  # Analyst asking questions
    interview: str  # Interview transcript
    sections: list  # Final key we duplicate in outer state for Send() API


class SearchQuery(BaseModel):
    search_query: str = Field(None, description="检索查询。")


class ResearchGraphState(TypedDict):
    topic: str  # Research topic
    max_analysts: int  # Number of analysts
    human_analyst_feedback: str  # Human feedback
    analysts: List[Analyst]  # Analyst asking questions
    sections: Annotated[list, operator.add]  # Send() API key
    introduction: str  # Introduction for the final report
    content: str  # Content for the final report
    conclusion: str  # Conclusion for the final report
    final_report: str  # Final report
    final_report_file: str
