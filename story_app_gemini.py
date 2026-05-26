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
# 页面配置
# ============================================================

st.set_page_config(
    page_title="儿童故事生成助手",
    page_icon="🐻",
    layout="centered"
)

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
# 英文文本分词统计函数
# ============================================================

def count_english_words(text):
    """统计英文文本的单词数量"""
    words = re.findall(r"[A-Za-z]+(?:[-'][A-Za-z]+)?", text)
    return len(words)

# ============================================================
# 故事生成函数（max_tokens = 65536）
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
    
    # 设置最大输出 tokens 为 65536
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
            
            # 检查 finish_reason
            if hasattr(response, 'candidates') and response.candidates:
                for candidate in response.candidates:
                    if hasattr(candidate, 'finish_reason'):
                        finish_reason = candidate.finish_reason
                        if finish_reason == "MAX_TOKENS":
                            # 如果超出，尝试增加（但 65536 已经是最大）
                            continue
                        elif finish_reason != "STOP":
                            print(f"finish_reason: {finish_reason}")
            
            # 提取内容
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
# 初始化
# ============================================================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "last_request_time" not in st.session_state:
    st.session_state.last_request_time = 0

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
    
    age_label = st.selectbox("年龄段", ["2-4岁", "4-6岁", "6-8岁"], index=1)
    age_map = {"2-4岁": 0, "4-6岁": 1, "6-8岁": 2}
    prompt_id = age_map[age_label]
    
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
st.caption(f"当前模型：{model_name} | 年龄段：{age_label} | 创意程度：{temperature}")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant" and "word_count" in msg:
            st.caption(f"📊 {msg['word_count']} words")

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
                messages = story_prompt(user_input, prompt_id=prompt_id)
                
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