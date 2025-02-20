"""
Content Generator Module

This module is responsible for generating Q&A content based on input texts using
LangChain and various LLM backends. It handles the interaction with the AI model and
provides methods to generate and save the generated content.
"""

import os
from typing import Optional, Dict, Any, List
import re


from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from eenhance.utils.config_conversation import load_conversation_config
from eenhance.utils.config import load_config
import logging
from langchain.prompts import HumanMessagePromptTemplate, SystemMessagePromptTemplate
from eenhance.utils.llm import llm_factory
from eenhance.blog.prompt import BOLG_PROMPT_TEMPLATE, LONG_BLOG_PROMPT_TEMPLATE
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class LLMBackend:
    def __init__(
        self,
        temperature: float,
        max_output_tokens: int,
        model_name: str,
    ):
        common_params = {
            "temperature": temperature,
            "presence_penalty": 0.75,
            "frequency_penalty": 0.75,
            "max_completion_tokens": max_output_tokens,
        }

        self.llm = llm_factory.create_llm(
            use_case="blog",
            model=model_name,
            **common_params,
        )


class LongFormContentGenerator:
    """
    Handles generation of long-form podcast conversations by breaking content into manageable chunks.

    Uses a "Content Chunking with Contextual Linking" strategy to maintain context between segments
    while generating longer conversations.

    Attributes:
        LONGFORM_INSTRUCTIONS (str): Constant containing instructions for long-form generation
        llm_chain: The LangChain chain used for content generation
    """

    # Add constant for long-form instructions
    LONGFORM_INSTRUCTIONS = """
    Additional Instructions:
        1. Provide extensive examples and real-world applications
        2. Include detailed analysis and multiple perspectives
        3. Use the "yes, and" technique to build upon points
        4. Incorporate relevant anecdotes and case studies
        5. Balance detailed explanations with engaging dialogue
        6. Maintain consistent voice throughout the extended discussion
        7. Generate a long conversation - output max_output_tokens tokens
    """

    def __init__(
        self,
        chain,
        llm,
        config_conversation: Dict[str, Any],
    ):
        """
        Initialize ConversationGenerator.

        Args:
            llm_chain: The LangChain chain to use for generation
            config_conversation: Conversation configuration dictionary
        """
        self.llm_chain = chain
        self.llm = llm
        self.max_num_chunks = config_conversation.get(
            "max_num_chunks", 10
        )  # Default if not in config
        self.min_chunk_size = config_conversation.get(
            "min_chunk_size", 200
        )  # Default if not in config

    def __calculate_chunk_size(self, input_content: str) -> int:
        """
        Calculate chunk size based on input content length.

        Args:
            input_content: Input text content

        Returns:
            Calculated chunk size that ensures:
            - Returns 1 if content length <= min_chunk_size
            - Each chunk has at least min_chunk_size characters
            - Number of chunks is at most max_num_chunks
        """
        input_length = len(input_content)
        if input_length <= self.min_chunk_size:
            return input_length

        maximum_chunk_size = input_length // self.max_num_chunks
        if maximum_chunk_size >= self.min_chunk_size:
            return maximum_chunk_size

        # Calculate chunk size that maximizes size while maintaining minimum chunks
        return input_length // (input_length // self.min_chunk_size)

    def chunk_content(self, input_content: str, chunk_size: int) -> List[str]:
        """
        Split input content into manageable chunks while preserving context.

        Args:
            input_content (str): The input text to chunk
            chunk_size (int): Maximum size of each chunk

        Returns:
            List[str]: List of content chunks
        """
        sentences = input_content.split(". ")
        chunks = []
        current_chunk = []
        current_length = 0

        for sentence in sentences:
            sentence_length = len(sentence)
            if current_length + sentence_length > chunk_size and current_chunk:
                chunks.append(". ".join(current_chunk) + ".")
                current_chunk = []
                current_length = 0
            current_chunk.append(sentence)
            current_length += sentence_length

        if current_chunk:
            chunks.append(". ".join(current_chunk) + ".")
        return chunks

    def enhance_prompt_params(
        self, prompt_params: Dict, part_idx: int, total_parts: int, chat_context: str
    ) -> Dict:
        """
        Enhance prompt parameters for long-form content generation.

        Args:
            prompt_params (Dict): Original prompt parameters
            part_idx (int): Index of current conversation part
            total_parts (int): Total number of conversation parts
            chat_context (str): Chat context from previous parts

        Returns:
            Dict: Enhanced prompt parameters with part-specific instructions
        """
        enhanced_params = prompt_params.copy()
        # Initialize part_instructions with chat context
        enhanced_params["context"] = chat_context

        COMMON_INSTRUCTIONS = """
            Podcast conversation so far is given in CONTEXT.
            Continue the natural flow of conversation. Follow-up on the very previous point/question without repeating topics or points already discussed!
            Hence, the transition should be smooth and natural. Avoid abrupt transitions.
            Make sure the first to speak is different from the previous speaker. Look at the last tag in CONTEXT to determine the previous speaker. 
            If last tag in CONTEXT is <Person1>, then the first to speak now should be <Person2>.
            If last tag in CONTEXT is <Person2>, then the first to speak now should be <Person1>.
            This is a live conversation without any breaks.
            Hence, avoid statemeents such as "we'll discuss after a short break.  Stay tuned" or "Okay, so, picking up where we left off".
        """

        # Add part-specific instructions
        if part_idx == 0:
            enhanced_params[
                "instruction"
            ] = f"""
            ALWAYS START THE CONVERSATION GREETING THE AUDIENCE: Welcome to {enhanced_params["podcast_name"]} - {enhanced_params["podcast_tagline"]}.
            You are generating the Introduction part of a long podcast conversation.
            Don't cover any topics yet, just introduce yourself and the topic. Leave the rest for later parts, following these guidelines:
            """
        elif part_idx == total_parts - 1:
            enhanced_params[
                "instruction"
            ] = f"""
            You are generating the last part of a long podcast conversation. 
            {COMMON_INSTRUCTIONS}
            For this part, discuss the below INPUT and then make concluding remarks in a podcast conversation format and END THE CONVERSATION GREETING THE AUDIENCE WITH PERSON1 ALSO SAYING A GOOD BYE MESSAGE, following these guidelines:
            """
        else:
            enhanced_params[
                "instruction"
            ] = f"""
            You are generating part {part_idx+1} of {total_parts} parts of a long podcast conversation.
            {COMMON_INSTRUCTIONS}
            For this part, discuss the below INPUT in a podcast conversation format, following these guidelines:
            """

        return enhanced_params

    def generate_long_form(self, input_content: str, prompt_params: Dict) -> str:
        """
        Generate a complete long-form conversation using chunked content.

        Args:
            input_content (str): Input text for conversation
            prompt_params (Dict): Base prompt parameters

        Returns:
            str: Generated long-form conversation
        """
        # Add long-form instructions once at the beginning
        prompt_params["user_instructions"] = (
            prompt_params.get("user_instructions", "") + self.LONGFORM_INSTRUCTIONS
        )

        # Get chunk size
        chunk_size = self.__calculate_chunk_size(input_content)

        chunks = self.chunk_content(input_content, chunk_size)
        conversation_parts = []
        chat_context = input_content
        num_parts = len(chunks)
        print(f"Generating {num_parts} parts")

        for i, chunk in enumerate(chunks):
            enhanced_params = self.enhance_prompt_params(
                prompt_params,
                part_idx=i,
                total_parts=num_parts,
                chat_context=chat_context,
            )
            enhanced_params["input_text"] = chunk
            response = self.llm_chain.invoke(enhanced_params)
            if i == 0:
                chat_context = response
            else:
                chat_context = chat_context + response
            print(f"Generated part {i+1}/{num_parts}: Size {len(chunk)} characters.")
            # print(f"[LLM-START] Step: {i+1} ##############################")
            # print(response)
            # print(f"[LLM-END] Step: {i+1} ##############################")
            conversation_parts.append(response)

        return self.stitch_conversations(conversation_parts)

    def stitch_conversations(self, parts: List[str]) -> str:
        """
        Combine conversation parts with smooth transitions.

        Args:
            parts (List[str]): List of conversation parts

        Returns:
            str: Combined conversation
        """
        # Simply join the parts, preserving all markup
        return "\n".join(parts)


# Make BaseContentCleaner a mixin class
class ContentCleanerMixin:
    """
    Mixin class containing common transcript cleaning operations.

    Provides reusable cleaning methods that can be used by different content generation strategies.
    Methods use protected naming convention (_method_name) as they are intended for internal use
    by the strategies.
    """

    @staticmethod
    def _clean_scratchpad(text: str) -> str:
        """
        Remove scratchpad blocks, plaintext blocks, standalone triple backticks, any string enclosed in brackets, and underscores around words.
        """
        try:
            import re

            pattern = r"```scratchpad\n.*?```\n?|```plaintext\n.*?```\n?|```\n?|\[.*?\]"
            cleaned_text = re.sub(pattern, "", text, flags=re.DOTALL)
            # Remove "xml" if followed by </Person1> or </Person2>
            cleaned_text = re.sub(r"xml(?=\s*</Person[12]>)", "", cleaned_text)
            # Remove underscores around words
            cleaned_text = re.sub(r"_(.*?)_", r"\1", cleaned_text)
            return cleaned_text.strip()
        except Exception as e:
            logger.error(f"Error cleaning scratchpad content: {str(e)}")
            return text

    @staticmethod
    def _clean_tss_markup(
        input_text: str, additional_tags: List[str] = ["Person1", "Person2"]
    ) -> str:
        """
        Remove unsupported TSS markup tags while preserving supported ones.
        """
        try:
            input_text = ContentCleanerMixin._clean_scratchpad(input_text)
            supported_tags = ["speak", "lang", "p", "phoneme", "s", "sub"]
            supported_tags.extend(additional_tags)

            pattern = r"</?(?!(?:" + "|".join(supported_tags) + r")\b)[^>]+>"
            cleaned_text = re.sub(pattern, "", input_text)
            cleaned_text = re.sub(r"\n\s*\n", "\n", cleaned_text)
            cleaned_text = re.sub(r"\*", "", cleaned_text)

            for tag in additional_tags:
                cleaned_text = re.sub(
                    f'<{tag}>(.*?)(?=<(?:{"|".join(additional_tags)})>|$)',
                    f"<{tag}>\\1</{tag}>",
                    cleaned_text,
                    flags=re.DOTALL,
                )

            return cleaned_text.strip()

        except Exception as e:
            logger.error(f"Error cleaning TSS markup: {str(e)}")
            return input_text


class ContentGenerationStrategy(ABC):
    """
    Abstract base class defining the interface for content generation strategies.

    Defines the contract that all concrete strategies must implement, including
    validation, generation, and cleaning operations.
    """

    @abstractmethod
    def validate(self, input_texts: str, image_file_paths: List[str]) -> None:
        """Validate inputs for this strategy."""
        pass

    @abstractmethod
    def generate(
        self, chain, input_texts: str, prompt_params: Dict[str, Any], **kwargs
    ) -> str:
        """Generate content using this strategy."""
        pass

    @abstractmethod
    def clean(self, response: str, config: Dict[str, Any]) -> str:
        """Clean the generated response according to strategy."""
        pass

    @abstractmethod
    def compose_prompt_params(
        self,
        config_conversation: Dict[str, Any],
        image_file_paths: List[str] = [],
        image_path_keys: List[str] = [],
        input_texts: str = "",
    ) -> Dict[str, Any]:
        """Compose prompt parameters according to strategy."""
        pass


class StandardContentStrategy(ContentGenerationStrategy, ContentCleanerMixin):
    """
    Strategy for generating standard-length content.

    Implements basic content generation without chunking or special handling.
    Uses common cleaning operations from ContentCleanerMixin.
    """

    def __init__(
        self,
        llm,
        content_generator_config: Dict[str, Any],
        config_conversation: Dict[str, Any],
    ):
        """
        Initialize StandardContentStrategy.

        Args:
            content_generator_config (Dict[str, Any]): Configuration for content generation
            config_conversation (Dict[str, Any]): Conversation configuration
        """
        self.llm = llm
        self.content_generator_config = content_generator_config
        self.config_conversation = config_conversation

    def validate(self, input_texts: str, image_file_paths: List[str]) -> None:
        """No specific validation needed for standard content."""
        pass

    def generate(
        self, chain, input_texts: str, prompt_params: Dict[str, Any], **kwargs
    ) -> str:
        """Generate standard-length content."""
        return chain.invoke(prompt_params)

    def clean(self, response: str, config: Dict[str, Any]) -> str:
        """Apply basic TSS markup cleaning."""
        return self._clean_tss_markup(response)

    def compose_prompt_params(
        self,
        config_conversation: Dict[str, Any],
        image_file_paths: List[str] = [],
        image_path_keys: List[str] = [],
        input_texts: str = "",
    ) -> Dict[str, Any]:
        """Compose prompt parameters for standard content generation."""
        prompt_params = {
            "input_text": input_texts,
            "conversation_style": ", ".join(
                config_conversation.get("conversation_style", [])
            ),
            "roles_person1": config_conversation.get("roles_person1"),
            "roles_person2": config_conversation.get("roles_person2"),
            "dialogue_structure": ", ".join(
                config_conversation.get("dialogue_structure", [])
            ),
            "podcast_name": config_conversation.get("podcast_name"),
            "podcast_tagline": config_conversation.get("podcast_tagline"),
            "output_language": config_conversation.get("output_language"),
            "engagement_techniques": ", ".join(
                config_conversation.get("engagement_techniques", [])
            ),
        }

        # Add image paths to parameters if any
        for key, path in zip(image_path_keys, image_file_paths):
            prompt_params[key] = path

        return prompt_params


class LongFormContentStrategy(ContentGenerationStrategy, ContentCleanerMixin):
    """
    Strategy for generating long-form content.

    Implements advanced content generation using chunking and context maintenance.
    Includes additional cleaning operations specific to long-form content.

    Note:
        - Only works with text input (no images)
        - Requires non-empty input text
    """

    def __init__(
        self,
        llm,
        content_generator_config: Dict[str, Any],
        config_conversation: Dict[str, Any],
    ):
        """
        Initialize LongFormContentStrategy.

        Args:
            content_generator_config (Dict[str, Any]): Configuration for content generation
            config_conversation (Dict[str, Any]): Conversation configuration
        """
        self.llm = llm
        self.content_generator_config = content_generator_config
        self.config_conversation = config_conversation

    def validate(self, input_texts: str, image_file_paths: List[str]) -> None:
        """Validate inputs for long-form generation."""
        if not input_texts.strip():
            raise ValueError("Long-form generation requires non-empty input text")
        if image_file_paths:
            raise ValueError("Long-form generation is not available with image inputs")

    def generate(
        self, chain, input_texts: str, prompt_params: Dict[str, Any], **kwargs
    ) -> str:
        """Generate long-form content."""
        generator = LongFormContentGenerator(chain, self.llm, self.config_conversation)
        return generator.generate_long_form(input_texts, prompt_params)

    def clean(self, response: str, config: Dict[str, Any]) -> str:
        """Apply enhanced cleaning for long-form content."""
        # First apply standard cleaning using common method
        standard_clean = self._clean_tss_markup(response)
        # Then apply additional long-form specific cleaning
        return self._clean_transcript_response(standard_clean, config)

    def _clean_transcript_response(
        self, transcript: str, config: Dict[str, Any]
    ) -> str:
        """
        Clean transcript using a two-step process with LLM-based cleaning.

        First cleans the markup using a specialized prompt template, then rewrites
        for better flow and consistency using a second prompt template.

        Args:
            transcript (str): Raw transcript text that may contain scratchpad blocks
            config (Dict[str, Any]): Configuration dictionary containing LLM and prompt settings

        Returns:
            str: Cleaned and rewritten transcript with proper tags and improved flow

        Note:
            Falls back to original or partially cleaned transcript if any cleaning step fails
        """
        logger.debug("Starting transcript cleaning process")

        final_transcript = self._fix_alternating_tags(transcript)

        logger.debug("Completed transcript cleaning process")

        return final_transcript

    def _fix_alternating_tags(self, transcript: str) -> str:
        """
        Ensures transcript has properly alternating Person1 and Person2 tags.

        Merges consecutive same-person tags and ensures proper tag alternation
        throughout the transcript.

        Args:
            transcript (str): Input transcript text that may have consecutive same-person tags

        Returns:
            str: Transcript with properly alternating tags and merged content

        Example:
            Input:
                <Person1>Hello</Person1>
                <Person1>World</Person1>
                <Person2>Hi</Person2>
            Output:
                <Person1>Hello World</Person1>
                <Person2>Hi</Person2>

        Note:
            Returns original transcript if cleaning fails
        """
        try:
            # Split into individual tag blocks while preserving tags
            pattern = r"(<Person[12]>.*?</Person[12]>)"
            blocks = re.split(pattern, transcript, flags=re.DOTALL)

            # Filter out empty/whitespace blocks
            blocks = [b.strip() for b in blocks if b.strip()]

            merged_blocks = []
            current_content = []
            current_person = None

            for block in blocks:
                # Extract person number and content
                match = re.match(r"<Person([12])>(.*?)</Person\1>", block, re.DOTALL)
                if not match:
                    continue

                person_num, content = match.groups()
                content = content.strip()

                if current_person == person_num:
                    # Same person - append content
                    current_content.append(content)
                else:
                    # Different person - flush current content if any
                    if current_content:
                        merged_text = " ".join(current_content)
                        merged_blocks.append(
                            f"<Person{current_person}>{merged_text}</Person{current_person}>"
                        )
                    # Start new person
                    current_person = person_num
                    current_content = [content]

            # Flush final content
            if current_content:
                merged_text = " ".join(current_content)
                merged_blocks.append(
                    f"<Person{current_person}>{merged_text}</Person{current_person}>"
                )

            return "\n".join(merged_blocks)

        except Exception as e:
            logger.error(f"Error fixing alternating tags: {str(e)}")
            return transcript  # Return original if fixing fails

    def compose_prompt_params(
        self,
        config_conversation: Dict[str, Any],
        image_file_paths: List[str] = [],
        image_path_keys: List[str] = [],
        input_texts: str = "",
    ) -> Dict[str, Any]:
        """Compose prompt parameters for long-form content generation."""
        return {
            "conversation_style": ", ".join(
                config_conversation.get("conversation_style", [])
            ),
            "roles_person1": config_conversation.get("roles_person1"),
            "roles_person2": config_conversation.get("roles_person2"),
            "dialogue_structure": ", ".join(
                config_conversation.get("dialogue_structure", [])
            ),
            "podcast_name": config_conversation.get("podcast_name"),
            "podcast_tagline": config_conversation.get("podcast_tagline"),
            "output_language": config_conversation.get("output_language"),
            "engagement_techniques": ", ".join(
                config_conversation.get("engagement_techniques", [])
            ),
        }


class ContentGenerator:
    def __init__(
        self,
        model_name: str = None,
        conversation_config: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the ContentGenerator.

        Args:
                model_name (str): Model name to use for generation.
                api_key_label (str): Environment variable name for API key.
                conversation_config (Optional[Dict[str, Any]]): Custom conversation configuration.
        """
        self.config = load_config()
        self.content_generator_config = self.config.get("blog", {})

        self.config_conversation = load_conversation_config(conversation_config)
        self.tts_config = self.config_conversation.get("text_to_speech", {})

        # Get output directories from conversation config
        self.output_directories = self.tts_config.get("output_directories", {})

        # Create output directories if they don't exist
        transcripts_dir = self.output_directories.get("transcripts")

        if transcripts_dir and not os.path.exists(transcripts_dir):
            os.makedirs(transcripts_dir)

        # Initialize LLM backend
        if not model_name:
            model_name = self.content_generator_config.get("llm_model")

        llm_backend = LLMBackend(
            temperature=self.config_conversation.get("creativity", 1),
            max_output_tokens=self.content_generator_config.get(
                "max_output_tokens", 8192
            ),
            model_name=model_name,
        )

        self.llm = llm_backend.llm

        # Initialize strategies with configs
        self.strategies = {
            True: LongFormContentStrategy(
                self.llm, self.content_generator_config, self.config_conversation
            ),
            False: StandardContentStrategy(
                self.llm, self.content_generator_config, self.config_conversation
            ),
        }

    def __compose_prompt(self, num_images: int, longform: bool = False):
        """
        Compose the prompt for the LLM based on the content list.
        """

        # Modify template and commit for longform if configured
        if longform:
            prompt_template = LONG_BLOG_PROMPT_TEMPLATE
        else:
            prompt_template = BOLG_PROMPT_TEMPLATE

        image_path_keys = []
        messages = []

        # Only add text content if input_text is not empty
        text_content = {
            "type": "text",
            "text": "Please analyze this input and generate a conversation. {input_text}",
        }
        messages.append(text_content)

        for i in range(num_images):
            key = f"image_path_{i}"
            image_content = {
                "image_url": {"url": f"{{{key}}}", "detail": "high"},
                "type": "image_url",
            }
            image_path_keys.append(key)
            messages.append(image_content)

        user_instructions = self.config_conversation.get("user_instructions", "")

        user_instructions = (
            "[[MAKE SURE TO FOLLOW THESE INSTRUCTIONS OVERRIDING THE PROMPT TEMPLATE IN CASE OF CONFLICT: "
            + user_instructions
            + "]]"
        )

        new_system_message = prompt_template + "\n" + user_instructions

        composed_prompt_template = ChatPromptTemplate.from_messages(
            [
                SystemMessagePromptTemplate.from_template(new_system_message),
                HumanMessagePromptTemplate.from_template(messages),
            ]
        )

        return composed_prompt_template, image_path_keys

    def generate_qa_content(
        self,
        input_texts: str = "",
        image_file_paths: List[str] = [],
        output_filepath: Optional[str] = None,
        longform: bool = False,
    ) -> str:
        """
        Generate Q&A content based on input texts.

        Args:
            input_texts (str): Input texts to generate content from.
            image_file_paths (List[str]): List of image file paths.
            output_filepath (Optional[str]): Filepath to save the response content.
            model_name (str): Model name to use for generation.
            api_key_label (str): Environment variable name for API key.
            longform (bool): Whether to generate long-form content. Defaults to False.

        Returns:
            str: Generated conversation content

        Raises:
            ValueError: If strategy validation fails
            Exception: If there's an error in generating content.
        """
        try:
            # Get appropriate strategy
            strategy = self.strategies[longform]

            # Validate inputs for chosen strategy
            strategy.validate(input_texts, image_file_paths)

            # Setup chain
            num_images = len(image_file_paths)
            self.prompt_template, image_path_keys = self.__compose_prompt(
                num_images, longform
            )
            self.parser = StrOutputParser()
            self.chain = self.prompt_template | self.llm | self.parser

            # Prepare parameters using strategy
            prompt_params = strategy.compose_prompt_params(
                self.config_conversation, image_file_paths, image_path_keys, input_texts
            )

            # Generate content using selected strategy
            self.response = strategy.generate(self.chain, input_texts, prompt_params)

            # Clean response using the same strategy
            self.response = strategy.clean(self.response, self.content_generator_config)

            logger.info(f"Content generated successfully")

            # Save output if requested
            if output_filepath:
                with open(output_filepath, "w") as file:
                    file.write(self.response)
                logger.info(f"Response content saved to {output_filepath}")
                print(f"Transcript saved to {output_filepath}")

            return self.response

        except Exception as e:
            logger.error(f"Error generating content: {str(e)}")
            raise


if __name__ == "__main__":
    import uuid
    from eenhance.constants import PROJECT_ROOT_PATH

    combined_content = """
# 人工智能在医疗领域的革命性应用

## 引言

随着人工智能（AI）技术的飞速发展，医疗领域正经历一场深刻的变革。本文探讨了AI在个性化医疗中的应用，如何通过提高诊断准确性和优化治疗方案显著改善患者护理。此外，我们还分析了AI驱动的医疗设备如何创新解决方案，助力医疗资源的均衡分配。最后，报告深入探讨了AI在医疗应用中的挑战与机遇，强调了技术进步与伦理考量并重的重要性。通过这些章节，我们将揭示AI如何重塑医疗行业的未来。

---



人工智能（AI）在医疗领域的应用正逐步改变传统的诊断和治疗模式，特别是在提高诊断准确性和个性化治疗方案方面展现出巨大潜力。AI在医疗影像分析中的表现尤为突出，例如在食管胃十二指肠内镜图像处理系统中，AI技术将盲点漏诊率显著降低至5.9%和3.4%[1]。此外，AI在肿瘤筛查中的应用也显示出其强大的潜力，如在肝脏病理图像处理系统中，AI实现了肝细胞癌和胆管癌的自动筛查，准确率高达88.5%[1]。这些案例表明，AI不仅能够提高诊断的准确性，还能在个性化治疗方案的制定中发挥重要作用。

然而，AI在医疗领域的应用也面临诸多挑战，如数据隐私、算法透明度以及技术普及等问题。尽管如此，AI技术的不断进步和优化，预示着其在个性化医疗中的应用前景广阔。

在全球医疗资源分配不均的背景下，AI技术正逐步成为解决这一问题的关键工具。通过智能问诊平台、辅助诊断系统和定制化治疗方案的生成，AI正在构建一个智慧医疗的全新生态。这一融合不仅极大提高了医疗服务的效率与质量，更为医学研究与教育探索开辟了前所未有的广阔空间。然而，AI驱动的医疗仪器具有精密度高、造价昂贵、维护成本高等特点，使得"AI+医疗"难以全面推广[2]。尽管如此，AI在医疗领域的应用正以前所未有的广度和深度拓展，悄然改变着传统医疗模式，为医疗行业带来了前所未有的深刻变革，打造出智慧医疗的新生态[3]。

为了确保AI在医疗领域的应用能够真正惠及所有国家和患者，世卫组织提出了六项指导原则，包括保护人类自主权、促进人类福祉、确保透明度、培养责任感和促进问责制、确保包容性和公平、以及促进具有响应性和可持续性的人工智能[4]。这些原则为各国提供了宝贵的指南，说明如何最大限度地发挥AI的优势，同时最大限度地降低其风险并避免其陷阱。

尽管AI在回顾性研究中表现出色，但在实际医疗环境中的应用仍面临诸多挑战，如数据隐私、算法可解释性和监管问题[2][3]。此外，AI系统的实际效用和其在临床环境中的表现仍需通过随机对照试验（RCT）等前瞻性研究来进一步验证[3]。尽管如此，AI在医疗领域的潜力巨大，未来随着技术和伦理问题的逐步解决，AI有望在医学领域发挥更大的作用[3]。


---

## 结论

本报告深入探讨了人工智能在医疗领域的多方面应用及其面临的挑战。首先，**人工智能在个性化医疗中的应用**展示了其在提高诊断准确性和个性化治疗方案中的潜力，特别是在医疗影像分析和肿瘤筛查中的显著成果。其次，**人工智能驱动的医疗设备**为医疗资源均衡分配提供了创新解决方案，尽管面临高成本和技术普及的挑战。最后，**人工智能在医疗领域的应用与挑战**部分强调了AI在实际医疗环境中的应用仍需克服数据隐私、算法可解释性和监管问题。尽管如此，AI技术的不断进步预示着其在医疗领域的广阔前景。

## 来源

[1] https://developer.aliyun.com/article/1612190  
[2] https://blog.csdn.net/qq_57128262/article/details/144229779  
[3] https://zhuanlan.zhihu.com/p/468836300  
[4] https://www.who.int/zh/news/item/28-06-2021-who-issues-first-global-report-on-ai-in-health-and-six-guiding-principles-for-its-design-and-use
"""
    conv_config = load_conversation_config()

    config = load_config()

    content_generator = ContentGenerator(
        model_name="glm-4-plus",
        conversation_config=conv_config.to_dict(),
    )

    # Generate Q&A content using output directory from conversation config
    random_filename = f"transcript_{uuid.uuid4().hex}.txt"
    transcript_filepath = os.path.join(
        PROJECT_ROOT_PATH,
        "data/transcripts",
        random_filename,
    )
    qa_content = content_generator.generate_qa_content(
        combined_content,
        image_file_paths=[],
        output_filepath=transcript_filepath,
        longform=True,
    )

    print(qa_content)
