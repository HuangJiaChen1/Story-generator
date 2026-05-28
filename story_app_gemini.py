# ============================================================
# story_app_gemini.py - 儿童故事生成交互页面
# ============================================================

import streamlit as st
import time
import re
import json
import os
from google import genai
from google.genai.types import GenerateContentConfig
from story_prompt_English import story_prompt

# ============================================================
# 故事类型映射
# ============================================================

STORY_TYPES = {
    1: {"name": "🏔️ 冒险串联型", "desc": "物体拟人化，出发→遇见→解决→回归"},
    2: {"name": "✨ 魔法连接型", "desc": "用魔法连接无关物体"},
    3: {"name": "🤗 日常温暖型", "desc": "三个小伙伴都陪着你"},
    4: {"name": "😂 搞笑荒诞型", "desc": "意外组合→奇怪事件→幽默结局"}
}

# ============================================================
# AI 生成关键词的提示词
# ============================================================

KEYWORD_GENERATION_PROMPT = """Generate 3 sets of keywords for children's stories. Each set has 3 concrete nouns.

Output format (only output this, no extra words):
set1: word1, word2, word3
set2: word1, word2, word3
set3: word1, word2, word3

Examples:
set1: teddy bear, bouncy ball, cozy sofa
set2: little watering can, sun hat, dandelion
set3: rubber duck, bubble bath, fluffy towel

Now generate 3 sets:"""

# ============================================================
# 加载配置文件
# ============================================================

def load_config():
    """加载 config.json 配置文件"""
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    if not os.path.exists(config_path):
        st.error(f"配置文件不存在: {config_path}")
        return None
    
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    
    return cfg

# ============================================================
# 初始化 Gemini 客户端
# ============================================================

@st.cache_resource
def init_gemini_client():
    """初始化 Gemini 客户端"""
    cfg = load_config()
    if cfg is None:
        return None, None
    
    project = cfg.get("project")
    location = cfg.get("location", "us-central1")
    
    if not project:
        project = "elaborate-baton-480304-r8"
    
    try:
        client = genai.Client(
            vertexai=True,
            project=project,
            location=location,
        )
        st.success(f"✅ Gemini 客户端初始化成功 | 项目: {project} | 位置: {location}")
        return client, cfg
    except Exception as e:
        st.error(f"初始化 Gemini 客户端失败: {e}")
        return None, None

# ============================================================
# 调用 Gemini 生成关键词
# ============================================================

def generate_keywords_gemini(client, model_name):
    """调用 Gemini 生成3组关键词"""
    
    try:
        response = client.models.generate_content(
            model=model_name,
            contents=KEYWORD_GENERATION_PROMPT,
            config=GenerateContentConfig(
                temperature=0.8,
                max_output_tokens=1024,
                top_p=0.9,
                top_k=40
            ),
        )
        
        if response.text:
            return response.text.strip()
        
        if hasattr(response, 'candidates') and response.candidates:
            for candidate in response.candidates:
                if hasattr(candidate, 'content') and candidate.content:
                    if hasattr(candidate.content, 'parts') and candidate.content.parts:
                        for part in candidate.content.parts:
                            if hasattr(part, 'text') and part.text:
                                return part.text.strip()
        
        return None
            
    except Exception as e:
        st.error(f"生成关键词失败: {e}")
        return None

# ============================================================
# 解析关键词
# ============================================================

def parse_keywords(text):
    """从AI返回的文本中解析出关键词列表"""
    keywords_list = []
    lines = text.strip().split('\n')
    
    for line in lines:
        line = line.strip()
        if ':' in line:
            parts = line.split(':', 1)
            if len(parts) == 2:
                kw_part = parts[1].strip()
                words = [w.strip() for w in kw_part.split(',')[:3]]
                if len(words) == 3:
                    keywords_list.append(', '.join(words))
    
    if not keywords_list:
        for line in lines:
            line = line.strip()
            if line and ',' in line:
                words = [w.strip() for w in line.split(',')[:3]]
                if len(words) == 3:
                    keywords_list.append(', '.join(words))
    
    return keywords_list

# ============================================================
# 英文文本分词统计函数
# ============================================================

def count_english_words(text):
    """统计英文文本的单词数量"""
    words = re.findall(r"[A-Za-z]+(?:[-'][A-Za-z]+)?", text)
    return len(words)

# ============================================================
# 故事生成函数
# ============================================================

def generate_story(system_prompt, user_prompt, client, model_name, temperature):
    """调用 Gemini API 生成故事"""
    
    if "last_request_time" not in st.session_state:
        st.session_state.last_request_time = 0
    
    full_prompt = f"{system_prompt}\n\n{user_prompt}"
    
    retry_count = 0
    wait_time = 3
    start_time = time.time()
    max_wait_time = 60
    
    max_tokens = 65536
    
    while True:
        try:
            elapsed = time.time() - st.session_state.last_request_time
            if elapsed < 3.0:
                time.sleep(3.0 - elapsed)
            
            response = client.models.generate_content(
                model=model_name,
                contents=full_prompt,
                config=GenerateContentConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                    top_p=0.9,
                    top_k=40
                ),
            )
            
            st.session_state.last_request_time = time.time()
            
            if hasattr(response, 'candidates') and response.candidates:
                for candidate in response.candidates:
                    if hasattr(candidate, 'finish_reason'):
                        finish_reason = candidate.finish_reason
                        if finish_reason == "MAX_TOKENS":
                            continue
                        elif finish_reason != "STOP":
                            print(f"finish_reason: {finish_reason}")
            
            result_text = response.text
            if result_text is None and response.candidates:
                parts = response.candidates[0].content.parts
                if parts:
                    result_text = "".join([p.text for p in parts if p.text])
            
            return result_text.strip() if result_text else ""
            
        except Exception as e:
            error_msg = str(e)
            
            if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                retry_count += 1
                elapsed_total = time.time() - start_time
                
                if elapsed_total + wait_time > max_wait_time:
                    raise Exception(f"API 繁忙，请稍后再试")
                
                wait_time = min(wait_time * 2, 10)
                time.sleep(wait_time)
            else:
                raise e

# ============================================================
# 初始化 session state
# ============================================================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "last_request_time" not in st.session_state:
    st.session_state.last_request_time = 0

if "generated_keywords" not in st.session_state:
    st.session_state.generated_keywords = ""

# ============================================================
# 初始化 Gemini 客户端
# ============================================================

client, config = init_gemini_client()

if client is None:
    st.stop()

model_name = config.get("model_name", "gemini-3.5-flash")

# ============================================================
# 侧边栏
# ============================================================

with st.sidebar:
    st.header("⚙️ 设置")
    st.caption(f"🤖 模型: {model_name}")
    st.divider()
    
    # 年龄段选择
    age_label = st.selectbox("年龄段", ["2-4岁", "4-6岁", "6-8岁"], index=1)
    age_map = {"2-4岁": 0, "4-6岁": 1, "6-8岁": 2}
    prompt_id = age_map[age_label]
    
    # 随机关键词按钮
    st.divider()
    st.subheader("🎲 随机关键词")
    st.caption("AI 会生成3组关键词，你可以选择一组使用")
    
    if st.button("✨ 生成关键词", use_container_width=True):
        with st.spinner("🤖 AI 正在生成关键词..."):
            keywords_text = generate_keywords_gemini(client, model_name)
            if keywords_text:
                st.session_state.generated_keywords = keywords_text
                st.success("✅ 关键词生成成功！")
                st.rerun()
            else:
                st.error("❌ 关键词生成失败，请重试")
    
    # 故事类型选择
    st.divider()
    st.subheader("📖 故事类型")
    story_type_options = list(STORY_TYPES.keys())
    story_type_labels = [STORY_TYPES[t]["name"] for t in story_type_options]
    
    selected_type_label = st.selectbox(
        "选择故事类型",
        story_type_labels,
        index=2,
        help="选择不同的故事类型，生成不同风格的故事"
    )
    
    for tid, tinfo in STORY_TYPES.items():
        if tinfo["name"] == selected_type_label:
            selected_story_type = tid
            break
    
    st.caption(f"📝 {STORY_TYPES[selected_story_type]['desc']}")
    
    st.divider()
    
    # 温度参数
    temperature = st.slider("创意程度", 0.0, 1.0, 0.7, 0.1)
    st.divider()
    
    st.caption("💡 输入英文关键词，如「teddy bear, ball, sofa」")
    
    if st.button("🗑️ 清空对话", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# ============================================================
# 主界面
# ============================================================

st.title("🐻 儿童故事生成助手")
st.caption(f"当前模型：{model_name} | 年龄段：{age_label} | 创意程度：{temperature} | 故事类型：{STORY_TYPES[selected_story_type]['name']}")

# 显示聊天历史
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant" and "word_count" in msg:
            st.caption(f"📊 {msg['word_count']} words")

# ============================================================
# 显示生成的关键词
# ============================================================

if st.session_state.generated_keywords:
    with st.expander("🎲 AI 生成的关键词（点击展开查看）", expanded=False):
        st.caption("复制下面任意一组关键词，粘贴到输入框中")
        
        keywords_list = parse_keywords(st.session_state.generated_keywords)
        
        if keywords_list:
            cols = st.columns(len(keywords_list))
            for i, (col, kw) in enumerate(zip(cols, keywords_list)):
                with col:
                    st.markdown(f"**第 {i+1} 组**")
                    st.code(kw, language="text")
        else:
            st.text(st.session_state.generated_keywords)

# ============================================================
# 用户输入
# ============================================================

user_input = st.chat_input("输入英文关键词，例如：teddy bear, ball, sofa")

if user_input:
    with st.chat_message("user"):
        st.markdown(f"**关键词：** {user_input}")
    
    st.session_state.messages.append({"role": "user", "content": f"关键词：{user_input}"})
    
    with st.chat_message("assistant"):
        with st.spinner("✨ 正在创作故事..."):
            try:
                messages = story_prompt(user_input, prompt_id=prompt_id, story_type=selected_story_type)
                
                system_prompt = messages[0]["content"]
                user_prompt = messages[1]["content"]
                
                start_time = time.time()
                story = generate_story(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    client=client,
                    model_name=model_name,
                    temperature=temperature
                )
                end_time = time.time()
                
                word_count = count_english_words(story)
                elapsed_ms = int((end_time - start_time) * 1000)
                
                st.markdown(story)
                st.caption(f"⏱️ {elapsed_ms}ms | 📊 {word_count} words")
                
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": story,
                    "word_count": word_count
                })
                
            except Exception as e:
                st.error(f"生成失败：{e}")
                st.info("请稍后再试或检查网络连接")

# ============================================================
# 页脚
# ============================================================

st.divider()
st.caption(f"✨ 由 Google Vertex AI + {model_name} 驱动 | 为孩子创造独一无二的故事 ✨")