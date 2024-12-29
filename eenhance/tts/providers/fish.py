"""Fish TTS provider implementation."""

from typing import List
from ..base import TTSProvider
from fish_audio_sdk import Session, TTSRequest


class FishTTS(TTSProvider):
    def __init__(self, base_url: str = None, api_key: str = None, model: str = None):
        """
        Initialize Fish TTS provider.

        Args:
            base_url (str): Base URL for Fish TTS API
            api_key (str): API key for Fish TTS
            model (str): Model name to use
        """
        self.api_key = api_key
        self.model = model or "default"
        self.session = Session(self.api_key)

    def generate_audio(
        self, text: str, voice: str, model: str = None, voice2: str = None
    ) -> bytes:
        """
        Generate audio using Fish TTS.

        Args:
            text (str): Text to convert to speech
            voice (str): Voice ID to use
            model (str): Model ID to use
            voice2 (str, optional): Secondary voice ID for multi-speaker scenarios

        Returns:
            bytes: Generated audio data

        Raises:
            RuntimeError: If audio generation fails
        """
        try:

            # 生成音频
            audio_chunks = []
            for chunk in self.session.tts(
                TTSRequest(
                    reference_id=voice,  # 使用model作为reference_id
                    text=text,
                )
            ):
                audio_chunks.append(chunk)

            # 合并音频数据
            audio_data = b"".join(audio_chunks)

            return audio_data

        except Exception as e:
            raise RuntimeError(f"Failed to generate audio with Fish TTS: {str(e)}")

    def get_supported_tags(self) -> List[str]:
        """
        Get list of SSML tags supported by Fish TTS.

        Returns:
            List[str]: List of supported SSML tag names
        """
        # 返回基类中定义的通用SSML标签
        # 如果Fish TTS支持额外的标签,可以在这里添加
        supported_tags = self.COMMON_SSML_TAGS.copy()
        return supported_tags
