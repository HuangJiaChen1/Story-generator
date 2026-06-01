# ============================================================
# image_generator_gemini.py - 文生图工具（使用谷歌 Gemini Vertex AI）
# ============================================================

import os
import json
import base64

# 导入谷歌相关库
from google import genai
from google.genai.types import GenerateContentConfig

# 图片生成配置
IMAGE_SIZE = "1024x1024"  # 适合故事插图的尺寸
MAX_IMAGES_PER_STORY = 3

# 负面提示词（避免生成文字）
NEGATIVE_PROMPT = """
text, words, letters, numbers, symbols, watermark, logo, signature, title, label,
any form of text content, text overlay, characters, handwriting, printed text,
signs, banners, books with text, posters with text
"""

# 加载配置文件
CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config.json')
if os.path.exists(CONFIG_PATH):
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        CONFIG = json.load(f)
else:
    CONFIG = {}

# 获取配置参数
VISION_MODEL_NAME = CONFIG.get('vision_model_name', 'gemini-2.5-flash-image')
PROJECT = CONFIG.get('project', 'elaborate-baton-480304-r8')
LOCATION = CONFIG.get('location', 'us-central1')
TEMPERATURE = CONFIG.get('temperature', 0.3)

# 全局客户端实例
_client = None

def init_gemini_client():
    """初始化 Gemini Vertex AI 客户端"""
    global _client
    
    if _client is not None:
        return _client
    
    try:
        _client = genai.Client(
            vertexai=True,
            project=PROJECT,
            location=LOCATION,
        )
        print(f"[Image Generator Gemini] Vertex AI 客户端初始化成功 | 项目: {PROJECT} | 位置: {LOCATION}")
        return _client
    except Exception as e:
        print(f"[Image Generator Gemini] 初始化失败: {e}")
        return None

def generate_image(prompt: str) -> str:
    """
    使用 Gemini Vertex AI 模型生成图片
    
    Args:
        prompt: 图片描述提示词
    
    Returns:
        生成的图片 Base64 数据（data:image/png;base64,...），失败返回 None
    """
    print(f"[Image Generator Gemini] 开始生成图片: {prompt[:50]}...")
    
    client = init_gemini_client()
    if client is None:
        return None
    
    try:
        # 构建完整提示词
        full_prompt = f"{prompt}\n\nNegative prompt: {NEGATIVE_PROMPT}"
        
        # 调用模型生成图片
        response = client.models.generate_content(
            model=VISION_MODEL_NAME,
            contents=full_prompt,
            config=GenerateContentConfig(
                temperature=TEMPERATURE,
                max_output_tokens=2048,
            ),
        )
        
        # 解析响应
        if response and hasattr(response, 'candidates') and response.candidates:
            for candidate in response.candidates:
                if hasattr(candidate, 'content') and candidate.content:
                    if hasattr(candidate.content, 'parts') and candidate.content.parts:
                        for part in candidate.content.parts:
                            if hasattr(part, 'inline_data') and part.inline_data:
                                image_data = part.inline_data.data
                                if image_data:
                                    print("[Image Generator Gemini] 图片生成成功")
                                    return f"data:image/png;base64,{image_data}"
        
        print("[Image Generator Gemini] 图片生成失败 - 未获取到图片数据")
        return None
        
    except Exception as e:
        print(f"[Image Generator Gemini] 生成异常: {e}")
        return None

def generate_story_images(story_text: str, num_images: int = 1) -> list:
    """
    根据故事文本生成多张图片
    
    Args:
        story_text: 故事文本
        num_images: 要生成的图片数量
    
    Returns:
        图片 Base64 数据列表
    """
    image_results = []
    num_images = min(num_images, MAX_IMAGES_PER_STORY)
    
    # 分析故事结构，提取关键场景
    scenes = extract_scenes_from_story(story_text, num_images)
    
    for i, scene in enumerate(scenes):
        print(f"[Image Generator Gemini] 生成场景 {i+1}/{num_images}: {scene[:50]}...")
        image_data = generate_image(scene)
        if image_data:
            image_results.append(image_data)
    
    return image_results

def extract_scenes_from_story(story_text: str, num_scenes: int = 3) -> list:
    """
    从故事文本中提取关键场景
    
    Args:
        story_text: 故事文本
        num_scenes: 要提取的场景数量
    
    Returns:
        场景描述列表
    """
    scenes = []
    
    paragraphs = story_text.split('\n')
    paragraphs = [p.strip() for p in paragraphs if p.strip()]
    
    if len(paragraphs) == 0:
        return ["A beautiful children's story scene, no text"]
    
    # 提取第一个场景（开头）
    if paragraphs:
        first_paragraph = paragraphs[0]
        scene1 = f"Children's story illustration: {first_paragraph[:100]}... Warm colors, soft lighting, fairy tale style, detailed background, no text"
        scenes.append(scene1)
    
    # 提取中间场景
    if len(paragraphs) >= 3 and num_scenes > 1:
        middle_index = len(paragraphs) // 2
        middle_paragraph = paragraphs[middle_index]
        scene2 = f"Children's story illustration: {middle_paragraph[:100]}... Magical atmosphere, fantasy elements, vibrant colors, no text"
        scenes.append(scene2)
    
    # 提取结尾场景
    if len(paragraphs) >= 2 and num_scenes > 2:
        last_paragraph = paragraphs[-1]
        scene3 = f"Children's story illustration: {last_paragraph[:100]}... Happy ending, peaceful scene, dreamy style, no text"
        scenes.append(scene3)
    
    # 如果场景不够，补充通用场景
    while len(scenes) < num_scenes:
        scenes.append(f"Beautiful fairy tale scene, magical forest, cute animals, children's book illustration style, no text")
    
    return scenes[:num_scenes]

# 测试代码
if __name__ == "__main__":
    test_story = """Once upon a time, there was a little bear who lived in a big forest. 
Every morning, he would wake up and go find delicious honey. 
One day, he met a little rabbit who was lost. 
Together, they became good friends and had many adventures."""
    
    print("测试 Gemini Vertex AI 图片生成:")
    print("=" * 60)
    print(f"故事文本: {test_story[:100]}...")
    print(f"使用模型: {VISION_MODEL_NAME}")
    print()
    
    # 初始化并生成图片
    client = init_gemini_client()
    if client:
        images = generate_story_images(test_story, num_images=2)
        print(f"\n生成的图片数量: {len(images)}")
        for i, data in enumerate(images):
            if data.startswith('data:image'):
                print(f"图片 {i+1}: Base64 数据（{len(data)} 字符）")
            else:
                print(f"图片 {i+1}: {data}")
    else:
        print("Gemini 客户端初始化失败，请检查 Google Cloud 认证配置")
    
    print("\n" + "=" * 60)
