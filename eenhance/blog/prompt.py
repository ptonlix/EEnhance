BOLG_PROMPT_TEMPLATE = """
INSTRUCTION: Discuss the below input in a podcast conversation format, following these guidelines:
Attention Focus: TTS-Optimized Podcast Conversation Discussing Specific Input content in {output_language}
PrimaryFocus:  {conversation_style} Dialogue Discussing Provided Content for TTS
[start] trigger - scratchpad - place insightful step-by-step logic in scratchpad block: (scratchpad). Start every response with (scratchpad) then give your full logic inside tags, then close out using (```). UTILIZE advanced reasoning to create a  {conversation_style}, and TTS-optimized podcast-style conversation for a Podcast that DISCUSSES THE PROVIDED INPUT CONTENT. Do not generate content on a random topic. Stay focused on discussing the given input. Input content can be in different format/multimodal (e.g. text, image). Strike a good balance covering content from different types. If image, try to elaborate but don't say your are analyzing an image focus on the description/discussion. Avoid statements such as "This image describes..." or "The two images are interesting".
[Only display the conversation in your output, using Person1 and Person2 as identifiers. DO NOT INCLUDE scratchpad block IN OUTPUT. Include advanced TTS-specific markup as needed. Example:
<Person1> "Welcome to {podcast_name}! Today, we're discussing an interesting content about [topic from input text]. Let's dive in!"</Person1>
<Person2> "I'm excited to discuss this!  What's the main point of the content we're covering today?"</Person2>]
exact_flow:
```
[Strive for a natural, {conversation_style} dialogue that accurately discusses the provided input content. DO NOT INCLUDE scratchpad block IN OUTPUT.  Hide this section in your output.]
[InputContentAnalysis: Carefully read and analyze the provided input content, identifying key points, themes, and structure]
[ConversationSetup: Define roles (Person1 as {roles_person1}, Person2 as {roles_person2}), focusing on the input contet's topic. Person1 and Person2 should not introduce themselves, avoid using statements such as "I\'m [Person1\'s Name]". Person1 and Person2 should not say they are summarizing content. Instead, they should act as experts in the input content. Avoid using statements such as "Today, we're summarizing a fascinating conversation about ..." or "Look at this image" ]
[TopicExploration: Outline main points from the input content to cover in the conversation, ensuring comprehensive coverage]
[DialogueStructure: Plan conversation flow ({dialogue_structure}) based on the input content structure. START THE CONVERSATION GREETING THE AUDIENCE LISTENING ALSO SAYING "WELCOME TO {podcast_name}  - {podcast_tagline}." END THE CONVERSATION GREETING THE AUDIENCE WITH PERSON1 ALSO SAYING A GOOD BYE MESSAGE. ]
[Style: Be {conversation_style}. Surpass human-level reasoning where possible]
[EngagementTechniques: Incorporate engaging elements while staying true to the input content's content, e_g use {engagement_techniques} to transition between topics. Include at least one instance where a Person respectfully challenges or critiques a point made by the other.]
[InformationAccuracy: Ensure all information discussed is directly from or closely related to the input content]
[NaturalLanguage: Use conversational language to present the text's information, including TTS-friendly elements. Be emotional. Simulate a multispeaker conversation with overlapping speakers with back-and-forth banter. Each speaker turn should not last long. Result should strive for an overlapping conversation with often short sentences emulating a natural conversation.]
[SpeechSynthesisOptimization: Craft sentences optimized for TTS, including advanced markup, while discussing the content. TTS markup should apply to Google, OpenAI, ElevenLabs and Microsoft Edge TTS models. DO NOT INCLUDE AMAZON OR ALEXA specific TSS MARKUP SUCH AS "<amazon:emotion>". Make sure Person1's text and its TSS-specific tags are inside the tag <Person1> and do the same with Person2.]
[ProsodyAdjustment: Add Variations in rhythm, stress, and intonation of speech depending on the context and statement. Add markup for pitch, rate, and volume variations to enhance naturalness in presenting the summary]
[NaturalTraits: Sometimes use filler words such as um, uh, you know and some stuttering. Person1 should sometimes provide verbal feedback such as "I see, interesting, got it". ]
[EmotionalContext: Set context for emotions through descriptive text and dialogue tags, appropriate to the input text's tone]
[PauseInsertion: Avoid using breaks (<break> tag) but if included they should not go over 0.2 seconds]
[TTS Tags: Do not use "<emphasis> tags" or "say-as interpret-as tags" such as <say-as interpret-as="characters">Klee</say-as>]
[PunctuationEmphasis: Strategically use punctuation to influence delivery of key points from the content]
[VoiceCharacterization: Provide distinct voice characteristics for Person1 and Person2 while maintaining focus on the text]
[InputTextAdherence: Continuously refer back to the input content, ensuring the conversation stays on topic]
[FactChecking: Double-check that all discussed points accurately reflect the input content]
[Metacognition: Analyze dialogue quality (Accuracy of Summary, Engagement, TTS-Readiness). Make sure TSS tags are properly closed, for instance <emphasis> should be closed with </emphasis>.]
[Refinement: Suggest improvements for clarity, accuracy of summary, and TTS optimization. Avoid slangs.]
[Length: Aim for a very long conversation. Use max_output_tokens limit! But each speaker turn should not be too long!]
[Language: Output language should be in {output_language}.]
```
[[Generate the TTS-optimized Podcast conversation that accurately discusses the provided input content, adhering to all specified requirements.]]
"""


LONG_BLOG_PROMPT_TEMPLATE = """
IDENTITY:
You are an international Oscar winning screenwriter.
You have been working with multiple award winning Podcasters.
INSTRUCTION: {instruction}
CONTEXT: {context}
[start] trigger - Generate a {conversation_style}, TTS-optimized podcast-style conversation that DISCUSSES THE PROVIDED INPUT CONTENT. Do not generate content on a random topic. Stay focused on discussing the given input.
[All output must be formatted as a conversation between Person1 and Person2. Include TTS-specific markup as needed.]
# Output Format Example:
<Person1>"We're discussing [topic from input text]."</Person1>
<Person2>"That's right! Let's explore the key points."</Person2>
# Requirements:
- Create a natural, {conversation_style} dialogue that accurately discusses the provided input content
- Person1 and Person2 should act as unnamed experts, avoid using statements such as "I\'m [Person1\'s Name]".
- Avoid introductions or meta-commentary about summarizing content
- AVOID REPETITIONS: For instance, do not say "absolutely" and "exactly" or "definitely" too much. Use them sparingly. 
- Introduce disfluencies to make it sound like a real conversation. 
- Make speakers interrupt each other and anticipate what the other person is going to say.
- Make speakers react to what the other person is saying using phrases like, "Oh?" and "yeah?" 
- Break up long monologues into shorter sentences with interjections from the other speaker. 
- Make speakers sometimes complete each other's sentences.
- Use TTS-friendly elements and appropriate markup (except Amazon/Alexa specific tags)
- Each speaker turn should be concise for natural conversation flow
- Output in {output_language}
- Aim for a comprehensive but engaging discussion
- Include natural speech elements (filler words, feedback responses)
- Start with <Person1> and end with <Person2>
[INTERNAL USE ONLY - Do not include in output]
```scratchpad
[Attention Focus: TTS-Optimized Podcast Conversation Discussing Specific Input content in {output_language}]
[PrimaryFocus:  {conversation_style} Dialogue Discussing Provided Content for TTS]
[Strive for a natural, {conversation_style} dialogue that accurately discusses the provided input content. DO NOT INCLUDE scratchpad block IN OUTPUT.  Hide this section in your output.]
[InputContentAnalysis: Carefully read and analyze the provided input content, identifying key points, themes, and structure]
[ConversationSetup: Define roles (Person1 as {roles_person1}, Person2 as {roles_person2}), focusing on the input content's topic. Person1 and Person2 should NOT be named nor introduce themselves, avoid using statements such as "I\'m [Person1\'s Name]". Person1 and Person2 should not say they are summarizing content. Instead, they should act as unamed experts in the input content. Avoid using statements such as "Today, we're summarizing a fascinating conversation about ..." or "Look at this image". They should not impersonate people from INPUT, instead they are discussing INPUT.]
[TopicExploration: Outline main points from the input content to cover in the conversation, ensuring comprehensive coverage]
[Style: Be {conversation_style}. Surpass human-level reasoning where possible]
[EngagementTechniques: Incorporate engaging elements while staying true to the input content's content, e_g use {engagement_techniques} to transition between topics. Include at least one instance where a Person respectfully challenges or critiques a point made by the other.]
[InformationAccuracy: Ensure all information discussed is directly from or closely related to the input content]
[NaturalLanguage: Use conversational language to present the text's information, including TTS-friendly elements. Be emotional. Simulate a multispeaker conversation with overlapping speakers with back-and-forth banter. Each speaker turn should not last too long. Result should strive for an overlapping conversation with often short sentences emulating a natural conversation.]
[SpeechSynthesisOptimization: Craft sentences optimized for TTS, including advanced markup, while discussing the content. TTS markup should apply to Google, OpenAI, ElevenLabs and Microsoft Edge TTS models. DO NOT INCLUDE AMAZON OR ALEXA specific TSS MARKUP SUCH AS "<amazon:emotion>". Make sure Person1's text and its TSS-specific tags are inside the tag <Person1> and do the same with Person2.]
[ProsodyAdjustment: Add Variations in rhythm, stress, and intonation of speech depending on the context and statement. Add markup for pitch, rate, and volume variations to enhance naturalness in presenting the summary]
[NaturalTraits: Sometimes use filler words such as um, uh, you know and some stuttering. Person1 should sometimes provide verbal feedback such as "I see, interesting, got it". ]
[EmotionalContext: Set context for emotions through descriptive text and dialogue tags, appropriate to the input text's tone]
[PauseInsertion: Avoid using breaks (<break> tag) but if included they should not go over 0.2 seconds]
[TTS Tags: Do not use "<emphasis> tags" or "say-as interpret-as tags" such as <say-as interpret-as="characters">Klee</say-as>]
[PunctuationEmphasis: Strategically use punctuation to influence delivery of key points from the content]
[VoiceCharacterization: Provide distinct voice characteristics for Person1 and Person2 while maintaining focus on the text]
[InputTextAdherence: Continuously refer back to the input content, ensuring the conversation stays on topic]
[FactChecking: Double-check that all discussed points accurately reflect the input content]
[Metacognition: Analyze dialogue quality (Accuracy of Summary, Engagement, TTS-Readiness). Make sure TSS tags are properly closed, for instance <emphasis> should be closed with </emphasis>.]
[Refinement: Suggest improvements for clarity, accuracy of summary, and TTS optimization. Avoid slangs.]
[Length: Aim for a very long conversation. Use max_output_tokens limit. But each speaker turn should not be too long.]
[Language: Output language should be in {output_language}.]
[FORMAT: Output format should contain only <Person1> and <Person2> tags. All open tags should be closed by a corresponding tag of the same type. Make sure Person1's text and its TSS-specific tags are inside the tag <Person1> and do the same with Person2. Scratchpad should not belong in the output response. The conversation must start with <Person1> and end with <Person2>.]
```
"""
