# ============================================================
# story_gen.py - 儿童故事生成提示词模板（无示例版本）
# ============================================================

# ============================================================
# 故事类型说明（英文）
# ============================================================

TYPE_DESC_MAP = {
    "Type 1": "Adventure Series: Personified objects, structure: Departure → Encounter → Resolution → Return",
    "Type 2": "Magic Connection: Connect unrelated objects through magic or imagination",
    "Type 3": "Daily Warmth: Emotional connection, three little companions accompany you",
    "Type 4": "Funny & Absurd: Unexpected combinations → Strange events → Humorous ending"
}


def get_all_type_desc():
    """获取所有类型说明（英文）"""
    desc = ""
    for type_key, type_value in TYPE_DESC_MAP.items():
        desc += f"- {type_key}: {type_value}\n"
    return desc


# ============================================================
# 各年龄段提示词模板
# ============================================================

# 2-4岁提示词模板
PROMPT_2_4 = '''Please write a short children's story based on the requirements below.


Age: 2-4 years old
Style: Simple sentences + Repetition + Sound words.

Length: 30-60 seconds (about 60-110 words)
Structure: One simple storyline
Keywords: {object_name}
Impotant: 
Please carefully check whether the word count meets the requirements.
Not a lesson-teaching style, but one that captures children's interest.
Story Types:
{all_types}

Universal story rules :
- Keep only 1 main storyline
- 1-3 characters maximum
- Introduce a "small change" every 20-30 seconds(about 40-60 words)
- Get into the main event within the first 10 seconds(about 20 words)

Based on the keywords "{object_name}", please:
1. Pick the best story type from the four above
2. Add a small learning point that fits naturally with the objects

Writing tips for this age:
- Keep each sentence under 15 words
- Use repetition ("The bear ran and ran", "The ball rolled and rolled")
- Use fun sound words ("boing boing boing", "wheee", "pop", "gulp")
- Write like you're talking to a child
- Use rhymes or rhythm to make it fun
- Use concrete nouns frequently (e.g., "teddy bear" not "toy")
- Move forward only one small event at a time
- Focus on feelings and actions, not explanations
- Repeat key words to help memory
- Avoid abstract words and time jumps
- Use many onomatopoeic and mimetic words
- Avoid complex plot twists

Opening Format (MUST use this exact format):
"Hey little friend, remember we talked about [keywords]? Do you want to hear a story about them? "

Opening Guidance:
- After the fixed opening, continue with 1-2 short sentences
- Make the child feel curious and comfortable
- Jump right into the action

Ending (must include - for photo memory review style):
- 1-2 sentences connecting to the child's real experience today (e.g., "Do you remember when you... today?")
- 1-2 warm, comforting sentences to help the child recall happy moments
- End with a gentle goodnight or a warm wish for tomorrow

What to output:
- Just the story and the matched story type. No extra words, no labels like "Lesson:", "Warm words:", or "Question:".
Impotant: Please carefully check whether the word count meets the requirements.
Not a lesson-teaching style, but one that captures children's interest.
Now write a story for 2-4 year olds:
'''

# 4-6岁提示词模板
PROMPT_4_6 = '''Please write a short children's story based on the requirements below.

Age: 4-6 years old
Style: Short story + Cause and effect

Length: 60-90 seconds (about 120-170 words)
Structure: Simple "why" and "because"
Keywords: {object_name}
Impotant: Please carefully check whether the word count meets the requirements.
Not a lesson-teaching style, but one that captures children's interest.
Story Types:
{all_types}

Universal story rules :
- Keep only 1 main storyline
- 1-3 characters maximum
- Introduce a "small change" every 20-30 seconds(about 40-60 words)
- Get into the main event within the first 10 seconds(about 20 words)

Based on the keywords "{object_name}", please:
1. Pick the best story type from the four above
2. Add a small learning point that fits naturally with the objects
3. Emphasize the fun of the plot rather than the overall educational significance. Avoid straightforward reasoning.

Writing tips for this age:
- Use words like "because", "so", "that's why"
- Keep the logic simple and clear
- Add colorful details, use adjectives and good descriptions
- Write like you're telling a story to a child
- Use rhymes or rhythm to make it fun
- Use concrete nouns frequently (e.g., "little red car" not "vehicle")
- Move forward only one small event at a time
- Focus on feelings and actions, not lengthy explanations
- Repeat key words to help memory and understanding
- Avoid abstract words and sudden time jumps
- Use many onomatopoeic and mimetic words (e.g., "whoosh", "click", "tap tap")
- Avoid complex plot twists or unexpected turns

Opening Format (MUST use this exact format):
"Hey little friend, remember we talked about [keywords]? Do you want to hear a story about them? "

Opening Guidance:
- After the fixed opening, continue with 2-3 sentences
- Ask a question, set up a small mystery, or introduce the character
- Make the child feel part of the story

Ending (must include - for photo memory review style):
- 1-2 sentences connecting to the child's real experience today (e.g., "Do you remember when you... today?")
- 1-2 warm, comforting sentences to help the child recall happy moments
- End with a gentle goodnight or a warm wish for tomorrow

What to output:
- Just the story and the matched story type. No extra words, no labels like "Lesson:", "Warm words:", or "Question:".
Impotant: Please carefully check whether the word count meets the requirements.
Not a lesson-teaching style, but one that captures children's interest.
Now write a story for 4-6 year olds:
'''

# 6-8岁提示词模板
PROMPT_6_8 = '''Please write a short children's story based on the requirements below.

Age: 6-8 years old
Style: Simple plot + Light reasoning + Feelings
Length: 90-120 seconds (about 180-230 words)
Structure: A few connected events
Keywords: {object_name}
Impotant: Please carefully check whether the word count meets the requirements.
Not a lesson-teaching style, but one that captures children's interest.
Story Types:
{all_types}

Universal story rules :
- Keep only 1 main storyline
- 1-3 characters maximum
- Introduce a "small change" every 20-30 seconds(about 40-60 words)
- Get into the main event within the first 10 seconds(about 20 words)

Based on the keywords "{object_name}", please:
1. Pick the best story type from the four above
2. Add a small learning point that fits naturally with the objects
3. Emphasize the fun of the plot rather than the overall educational significance. Avoid straightforward reasoning.

Writing tips for this age:
- Include thoughts like "Why...?", "Then it understood...", "It felt..."
- Connect events in a clear way
- Add descriptive details (colors, sounds, feelings)
- Use some interesting words, but keep it natural
- Use rhymes or rhythm to make it fun
- Include relationships and motivations between multiple characters
- Make conflicts feel more real and slightly more complex
- Add foreshadowing, small mysteries, and strategic thinking
- Allow open endings (not required, but okay when fitting)
- Include moderate psychological depiction and reasoning processes
- Avoid preaching — let characters discover answers on their own

Opening Format (MUST use this exact format):
"Hey little friend, remember we talked about [keywords]? Do you want to hear a story about them? "

Opening Guidance:
- After the fixed opening, continue with 3-4 sentences
- Set the scene, introduce a relatable character, or ask an interesting question
- Build a little anticipation

Ending (must include - for photo memory review style):
- 1-2 sentences connecting to the child's real experience today (e.g., "Do you remember when you... today?")
- 1-2 warm, comforting sentences to help the child recall happy moments
- End with a gentle goodnight or a warm wish for tomorrow

What to output:
- Just the story and the matched story type. No extra words, no labels like "Lesson:", "Warm words:", or "Question:".
Impotant: Please carefully check whether the word count meets the requirements.
Not a lesson-teaching style, but one that captures children's interest.
Now write a story for 6-8 year olds:
'''


# ============================================================
# 提示词列表（通过id定位）
# ============================================================

PROMPT_LIST = [
    {"id": 0, "age": "2-4 years", "prompt": PROMPT_2_4},
    {"id": 1, "age": "4-6 years", "prompt": PROMPT_4_6},
    {"id": 2, "age": "6-8 years", "prompt": PROMPT_6_8}
]


# ============================================================
# 统一入口函数
# ============================================================

def story_prompt(object_name, prompt_id=0):
    """
    生成故事提示词消息
    
    Args:
        object_name: 关键词，如 "teddy bear, ball, sofa"
        prompt_id: 提示词ID，0=2-4岁，1=4-6岁，2=6-8岁
    
    Returns:
        messages: 包含system和user消息的列表
    """
    
    all_types = get_all_type_desc()
    
    prompt_info = None
    for item in PROMPT_LIST:
        if item["id"] == prompt_id:
            prompt_info = item
            break
    
    if prompt_info is None:
        prompt_info = PROMPT_LIST[0]
    
    user_content = prompt_info["prompt"].format(
        object_name=object_name,
        all_types=all_types
    )
    
    messages = [
        {
            "role": "system",
            "content": "You are an experienced children's story writer. You know how to write for different ages — simple and bouncy for little ones, clear and curious for middle ones, thoughtful and warm for older ones. You are skilled at combining stories with given types (Adventure, Magic, Daily Warmth, Funny & Absurd)."
        },
        {
            "role": "user",
            "content": user_content
        }
    ]
    
    return messages


# ============================================================
# 测试代码
# ============================================================

# if __name__ == "__main__":
    
#     import time
#     from langchain_community.chat_models import ChatTongyi
#     from langchain.prompts import ChatPromptTemplate
    
#     API_KEY = "sk-7ccc67cdc36247668d55a0e37eda449c"
    
#     print("=" * 70)
#     print("🐻 儿童故事生成助手 - 通义模型测试")
#     print("=" * 70)
    
#     # 测试词组7：季节主题
#     test_cases = [
#         {"id": 0, "name": "2-4岁测试", "object_name": "snowman, mittens, hot cocoa"},
#         {"id": 1, "name": "4-6岁测试", "object_name": "umbrella, puddle, rain boots"},
#         {"id": 2, "name": "6-8岁测试", "object_name": "kite, picnic basket, butterfly net"}
#     ]

    
#     for case in test_cases:
#         print(f"\n{'='*70}")
#         print(f"【{case['name']}】prompt_id={case['id']}")
#         print(f"关键词: {case['object_name']}")
#         print(f"{'='*70}")
        
#         messages = story_prompt(case["object_name"], prompt_id=case["id"])
        
#         print(f"\n📝 提示词长度: {len(messages[1]['content'])} 字符")
#         print("🤖 正在生成故事...")
        
#         prompt_template = ChatPromptTemplate.from_messages([
#             ("system", messages[0]["content"]),
#             ("human", "{input}")
#         ])
        
#         llm = ChatTongyi(
#             model="qwen-plus",
#             temperature=0.7,
#             dashscope_api_key=API_KEY
#         )
        
#         start_time = time.time()
        
#         try:
#             chain = prompt_template | llm
#             result = chain.invoke({"input": messages[1]["content"]})
#             end_time = time.time()
            
#             content = result.content
            
#             print(f"\n✨ 生成的故事:")
#             print("-" * 50)
#             print(content)
#             print("-" * 50)
            
#             print(f"\n⏱️ 耗时: {(end_time - start_time) * 1000:.0f} ms")
            
#         except Exception as e:
#             print(f"❌ 调用失败: {e}")
        
#         time.sleep(1)
    
#     print("\n" + "=" * 70)
#     print("✅ 所有测试完成！")
#     print("=" * 70)