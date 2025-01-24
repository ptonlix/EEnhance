"""
播客音频生成助手
"""

from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from .text_to_speech import TextToSpeech
import logging
from pathlib import Path
from eenhance.constants import PROJECT_ROOT_PATH

logger = logging.getLogger(__name__)


# TTS Agent的输入参数
class TTSInput(TypedDict):
    blog_content: str
    blog_file_path: str
    tts_provider: str
    tts_is_open: bool


# TTS Agent的输出参数
class TTSOutput(TypedDict):
    audio_file_path: str


# no-op node that should be interrupted on
def human_feedback(state: TTSInput):
    pass


def tts(state: TTSInput) -> TTSOutput:

    if state.get("blog_content"):
        input_text = state["blog_content"]
    else:
        # Read input text from file
        with open(
            state["blog_file_path"],
            "r",
        ) as file:
            input_text = file.read()

    tts_edge = TextToSpeech(model=state["tts_provider"])
    file_name = Path(state["blog_file_path"]).stem + "_tts.mp3"
    tts_output_file = Path(PROJECT_ROOT_PATH) / "data" / "audio" / file_name
    tts_edge.convert_to_speech(input_text, tts_output_file)
    logger.info(f"Convert TTS completed. Output saved to {tts_output_file}")

    return TTSOutput(audio_file_path=tts_output_file)


def router(state: TTSInput):
    if state.get("tts_is_open"):
        return "tts"
    else:
        return "end"


graph = StateGraph(input=TTSInput, output=TTSOutput)
graph.add_node("human_feedback", human_feedback)
graph.add_node("tts", tts)
graph.add_edge(START, "human_feedback")
graph.add_conditional_edges("human_feedback", router, {"tts": "tts", "end": END})
graph.add_edge("tts", "human_feedback")

memory = MemorySaver()
graph = graph.compile(interrupt_before=["human_feedback"], checkpointer=memory)
