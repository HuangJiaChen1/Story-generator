# ============================================================
# story_gen.py - 儿童故事生成提示词模板（支持类型参数）
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


# ============================================================
# 结尾风格配置（支持不同场景）
# ============================================================

ENDING_STYLES = {
    "bedtime": """Ending (must include - for photo memory review style):
- 1-2 sentences connecting to the child's real experience today (e.g., "Do you remember when you... today?")
- 1-2 warm, comforting sentences to help the child recall happy moments
- End with a gentle goodnight or a warm wish for tomorrow""",
    
    "daytime": """Ending (must include - for active daytime style):
- 1-2 sentences encouraging the child to explore or play
- 1-2 sentences linking to things they can do later today
- End with excitement for the next adventure or activity""",
    
    "weekend": """Ending (must include - for weekend fun style):
- 1-2 sentences about fun weekend activities or plans
- 1-2 sentences about spending time with family or friends
- End with looking forward to tomorrow's fun"""
}


def get_ending_style(scene_type: str) -> str:
    """根据场景类型获取结尾风格"""
    return ENDING_STYLES.get(scene_type, ENDING_STYLES["bedtime"])


# ============================================================
# 故事类型专属开头模板（与故事类型一一对应）
# ============================================================

STORY_TYPE_OPENINGS = {
    1: {  # 冒险串联型
        "name": "冒险开场",
        "format": """Opening Format (MUST use this exact format):
"Ready for an adventure? Today {keywords} are going on a big journey! Want to come along? "

Opening Guidance:
- After the fixed opening, introduce the starting point of the adventure
- Set up a goal or destination for the characters
- Use energetic and exciting language to build anticipation""",
        "description": "充满活力的冒险开场，适合探险主题"
    },
    2: {  # 魔法连接型
        "name": "魔法开场",
        "format": """Opening Format (MUST use this exact format):
"Guess what magical secret {keywords} share? Let me tell you their mysterious story! "

Opening Guidance:
- After the fixed opening, hint at the magical connection between objects
- Create a sense of wonder and mystery
- Build curiosity about what will happen next""",
        "description": "神秘奇幻的魔法开场，适合魔法主题"
    },
    3: {  # 日常温暖型
        "name": "温馨开场",
        "format": """Opening Format (MUST use this exact format):
"Hi there! Do you know how special {keywords} are? Let me tell you a warm little story about them. "

Opening Guidance:
- After the fixed opening, connect to everyday experiences
- Highlight the emotional bond between the objects
- Create a cozy and comforting atmosphere""",
        "description": "温暖亲切的日常开场，适合温馨主题"
    },
    4: {  # 搞笑荒诞型
        "name": "幽默开场",
        "format": """Opening Format (MUST use this exact format):
"Get ready to laugh! {keywords} are about to do something funny! Want to see? "

Opening Guidance:
- After the fixed opening, set up a funny situation
- Use playful and absurd language
- Make the child smile and feel lighthearted""",
        "description": "轻松幽默的搞笑开场，适合荒诞主题"
    }
}


def get_opening_by_story_type(story_type: int) -> str:
    """根据故事类型获取对应的开头模板"""
    opening_info = STORY_TYPE_OPENINGS.get(story_type, STORY_TYPE_OPENINGS[3])
    return opening_info["format"]


def get_all_type_desc():
    """获取所有类型说明（英文）"""
    desc = ""
    for type_key, type_value in TYPE_DESC_MAP.items():
        desc += f"- {type_key}: {type_value}\n"
    return desc


def get_type_name(type_id: int) -> str:
    """根据类型ID获取类型名称"""
    type_names = {
        1: "Adventure Series",
        2: "Magic Connection", 
        3: "Daily Warmth",
        4: "Funny & Absurd"
    }
    return type_names.get(type_id, "Daily Warmth")


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
Story Type: {type_name}
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

Based on the keywords "{object_name}" and story type "{type_name}", please:
1. Follow the selected story type to create the story
2. Add a small learning point that fits naturally with the objects

Word restrictions (MUST follow):
- Avoid using the following words or similar inappropriate/risky terms: 
  silly, stupid, dumb, idiot, hate, kill, die, blood, gun, weapon, scary monster, ghost, 
  hurt badly, attack, hit hard, cry loudly, ugly, fat, lazy, weird, crazy, mad.
- Use only positive, gentle, and child-friendly language.
- Do not use any word that may cause fear, sadness, or negative feelings in young children.
- Before output, please double-check your story to ensure none of these words appear.

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

{opening_style}

{ending_style}

What to output:
- Just the story. No extra words, no labels like "Lesson:", "Warm words:", or "Question:".
- MUST use line breaks between paragraphs (at least one blank line between each paragraph).
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
Story Type: {type_name}
Impotant: Please carefully check whether the word count meets the requirements.
Not a lesson-teaching style, but one that captures children's interest.
Story Types:
{all_types}

Universal story rules :
- Keep only 1 main storyline
- 1-3 characters maximum
- Introduce a "small change" every 20-30 seconds(about 40-60 words)
- Get into the main event within the first 10 seconds(about 20 words)

Based on the keywords "{object_name}" and story type "{type_name}", please:
1. Follow the selected story type to create the story
2. Add a small learning point that fits naturally with the objects
3. Emphasize the fun of the plot rather than the overall educational significance. Avoid straightforward reasoning.

Word restrictions (MUST follow):
- Avoid using the following words or similar inappropriate/risky terms: 
  silly, stupid, dumb, idiot, hate, kill, die, blood, gun, weapon, scary monster, ghost, 
  hurt badly, attack, hit hard, cry loudly, ugly, fat, lazy, weird, crazy, mad.
- Use only positive, gentle, and child-friendly language.
- Do not use any word that may cause fear, sadness, or negative feelings in young children.
- Before output, please double-check your story to ensure none of these words appear.

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

{opening_style}

{ending_style}

What to output:
- Just the story. No extra words, no labels like "Lesson:", "Warm words:", or "Question:".
- MUST use line breaks between paragraphs (at least one blank line between each paragraph).
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
Story Type: {type_name}
Impotant: Please carefully check whether the word count meets the requirements.
Not a lesson-teaching style, but one that captures children's interest.
Story Types:
{all_types}

Universal story rules :
- Keep only 1 main storyline
- 1-3 characters maximum
- Introduce a "small change" every 20-30 seconds(about 40-60 words)
- Get into the main event within the first 10 seconds(about 20 words)

Based on the keywords "{object_name}" and story type "{type_name}", please:
1. Follow the selected story type to create the story
2. Add a small learning point that fits naturally with the objects
3. Emphasize the fun of the plot rather than the overall educational significance. Avoid straightforward reasoning.

Word restrictions (MUST follow):
- Avoid using the following words or similar inappropriate/risky terms: 
  silly, stupid, dumb, idiot, hate, kill, die, blood, gun, weapon, scary monster, ghost, 
  hurt badly, attack, hit hard, cry loudly, ugly, fat, lazy, weird, crazy, mad.
- Use only positive, gentle, and child-friendly language.
- Do not use any word that may cause fear, sadness, or negative feelings in young children.
- Before output, please double-check your story to ensure none of these words appear.

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

{opening_style}

{ending_style}

What to output:
- Just the story. No extra words, no labels like "Lesson:", "Warm words:", or "Question:".
- MUST use line breaks between paragraphs (at least one blank line between each paragraph).
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

def story_prompt(object_name, prompt_id=0, story_type=3, scene_type="bedtime"):
    """
    生成故事提示词消息
    
    Args:
        object_name: 关键词，如 "teddy bear, ball, sofa"
        prompt_id: 提示词ID，0=2-4岁，1=4-6岁，2=6-8岁
        story_type: 故事类型ID，1=冒险串联型，2=魔法连接型，3=日常温暖型，4=搞笑荒诞型
        scene_type: 场景类型，可选值: bedtime(睡前), daytime(日间), weekend(周末)
    
    Returns:
        messages: 包含system和user消息的列表
    """
    
    all_types = get_all_type_desc()
    type_name = get_type_name(story_type)
    ending_style = get_ending_style(scene_type)
    
    # 根据故事类型自动匹配开头风格
    opening_style = get_opening_by_story_type(story_type)
    
    prompt_info = None
    for item in PROMPT_LIST:
        if item["id"] == prompt_id:
            prompt_info = item
            break
    
    if prompt_info is None:
        prompt_info = PROMPT_LIST[0]
    
    user_content = prompt_info["prompt"].format(
        object_name=object_name,
        all_types=all_types,
        type_name=type_name,
        ending_style=ending_style,
        opening_style=opening_style
    )
    
    messages = [
        {
            "role": "system",
            "content": "You are an experienced children's story writer. You know how to write for different ages — simple and bouncy for little ones, clear and curious for middle ones, thoughtful and warm for older ones. You are skilled at combining stories with given types (Adventure, Magic, Daily Warmth, Funny & Absurd). You always use positive, gentle, and child-friendly language, and strictly avoid any negative or potentially upsetting words (e.g., silly, stupid, hate, kill, scary monster, etc.)."
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

if __name__ == "__main__":
    
    import time
    from langchain_community.chat_models import ChatTongyi
    from langchain.prompts import ChatPromptTemplate
    
    API_KEY = "sk-7ccc67cdc36247668d55a0e37eda449c"
    
    print("=" * 70)
    print("🐻 儿童故事生成助手 - 通义模型测试")
    print("=" * 70)
    
    # 测试用例：不同年龄 + 不同类型 + 不同场景
    test_cases = [
        # 2-4岁 + 冒险串联型 + 睡前场景
        {"prompt_id": 0, "story_type": 1, "scene_type": "bedtime", "name": "2-4岁-冒险型-睡前", "object_name": "teddy bear, ball, sofa"},
        # 4-6岁 + 魔法连接型 + 日间场景
        {"prompt_id": 1, "story_type": 2, "scene_type": "daytime", "name": "4-6岁-魔法型-日间", "object_name": "paper cup, flashlight, white wall"},
        # 6-8岁 + 日常温暖型 + 周末场景
        {"prompt_id": 2, "story_type": 3, "scene_type": "weekend", "name": "6-8岁-温暖型-周末", "object_name": "old sneakers, medal, family photo"},
        # 4-6岁 + 搞笑荒诞型 + 睡前场景（默认）
        {"prompt_id": 1, "story_type": 4, "scene_type": "bedtime", "name": "4-6岁-搞笑型-睡前", "object_name": "toothbrush, jelly, alarm clock"}
    ]
    
    for case in test_cases:
        print(f"\n{'='*70}")
        print(f"【{case['name']}】prompt_id={case['prompt_id']}, story_type={case['story_type']}, scene_type={case.get('scene_type', 'bedtime')}")
        print(f"关键词: {case['object_name']}")
        print(f"{'='*70}")
        
        messages = story_prompt(
            object_name=case["object_name"], 
            prompt_id=case["prompt_id"],
            story_type=case["story_type"],
            scene_type=case.get("scene_type", "bedtime")
        )
        
        print(f"\n📝 提示词长度: {len(messages[1]['content'])} 字符")
        print("🤖 正在生成故事...")
        
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", messages[0]["content"]),
            ("human", "{input}")
        ])
        
        llm = ChatTongyi(
            model="qwen-plus",
            temperature=0.7,
            dashscope_api_key=API_KEY
        )
        
        start_time = time.time()
        
        try:
            chain = prompt_template | llm
            result = chain.invoke({"input": messages[1]["content"]})
            end_time = time.time()
            
            content = result.content
            
            print(f"\n✨ 生成的故事:")
            print("-" * 50)
            print(content)
            print("-" * 50)
            
            print(f"\n⏱️ 耗时: {(end_time - start_time) * 1000:.0f} ms")
            
        except Exception as e:
            print(f"❌ 调用失败: {e}")
        
        time.sleep(1)
    
    print("\n" + "=" * 70)
    print("✅ 所有测试完成！")
    print("=" * 70)