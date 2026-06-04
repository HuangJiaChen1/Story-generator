# ============================================================
# image_generator_gemini.py - 文生图工具（使用谷歌 Gemini Vertex AI）
# ============================================================

import os
import json
import base64
import re

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


def truncate_to_complete_sentence(text: str, max_length: int = 100) -> str:
    """
    将文本截取到第一个完整句子结束的位置，确保每个场景只对应一个完整句子
    
    Args:
        text: 原始文本
        max_length: 最大长度
        
    Returns:
        截取后的完整句子
    """
    if len(text) <= max_length:
        return text.strip()
    
    # 英文句子分隔符（优先找完整句子结束）
    sentence_endings = ['. ', '! ', '? ', '.\n', '!\n', '?\n', '." ', '!" ', '?" ']
    
    # 从前往后找第一个完整句子结束位置（只取第一个句子）
    for ending in sentence_endings:
        pos = text.find(ending)
        if pos != -1 and pos > 0:
            # 返回第一个完整句子
            result = text[:pos + len(ending)].strip()
            # 如果句子太长，截取到合理长度
            if len(result) > max_length:
                # 在最大长度内找最近的句子结束符
                search_end = min(max_length + 10, len(result))
                sub_pos = result.rfind('. ', max_length - 20, search_end)
                if sub_pos != -1:
                    result = result[:sub_pos + 2].strip()
                else:
                    result = result[:max_length].strip()
            return result
    
    # 如果没找到句子结束符，返回原始文本的前max_length字符
    return text[:max_length].strip()


def extract_nth_sentence(text: str, n: int = 0, max_length: int = 100) -> str:
    """
    从文本中提取第n个完整句子（n从0开始）
    
    Args:
        text: 原始文本
        n: 要提取的句子索引（0=第一个句子，1=第二个句子，以此类推）
        max_length: 最大长度
        
    Returns:
        第n个完整句子，如果没有足够的句子则返回最后一个句子
    """
    if not text.strip():
        return ""
    
    # 英文句子分隔符
    sentence_endings = ['. ', '! ', '? ', '.\n', '!\n', '?\n', '." ', '!" ', '?" ']
    
    sentences = []
    remaining = text
    
    # 分割句子
    while remaining:
        found = False
        for ending in sentence_endings:
            pos = remaining.find(ending)
            if pos != -1:
                sentences.append(remaining[:pos + len(ending)].strip())
                remaining = remaining[pos + len(ending):].strip()
                found = True
                break
        
        if not found:
            # 没有找到更多句子结束符
            if remaining.strip():
                sentences.append(remaining.strip())
            break
    
    # 获取第n个句子
    if n < len(sentences):
        result = sentences[n]
    else:
        # 如果n超出范围，返回最后一个句子
        result = sentences[-1] if sentences else text[:max_length].strip()
    
    # 如果句子太长，截取到合理长度
    if len(result) > max_length:
        result = truncate_to_complete_sentence(result, max_length)
    
    return result


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
        print("[Image Generator Gemini] 客户端未初始化")
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
                                inline_data = part.inline_data
                                image_data = inline_data.data
                                if image_data:
                                    # 获取 MIME 类型
                                    mime_type = getattr(inline_data, 'mime_type', 'image/png')
                                    print(f"[Image Generator Gemini] 图片数据类型: {type(image_data)}, MIME: {mime_type}")
                                    
                                    # 处理二进制数据或 Base64 字符串
                                    if isinstance(image_data, bytes):
                                        # 二进制数据需要 Base64 编码
                                        encoded_data = base64.b64encode(image_data).decode('utf-8')
                                    elif isinstance(image_data, str):
                                        # 如果已经是 Base64 字符串，直接使用
                                        encoded_data = image_data
                                    else:
                                        print(f"[Image Generator Gemini] 未知的数据类型: {type(image_data)}")
                                        return None
                                    
                                    print("[Image Generator Gemini] 图片生成成功")
                                    return f"data:{mime_type};base64,{encoded_data}"
        
        print("[Image Generator Gemini] 图片生成失败 - 未获取到图片数据")
        return None
        
    except Exception as e:
        print(f"[Image Generator Gemini] 生成异常: {e}")
        import traceback
        print(f"[Image Generator Gemini] 详细错误: {traceback.format_exc()}")
        return None

def generate_story_images(story_text: str, num_images: int = 1, age_group: str = "6-8") -> list:
    """
    根据故事文本生成多张图片
    
    Args:
        story_text: 故事文本
        num_images: 要生成的图片数量（会根据年龄段自动调整）
        age_group: 目标年龄段，可选值: "2-4", "4-6", "6-8"
    
    Returns:
        包含场景描述和图片数据的字典列表: 
        [{"scene": "场景描述", "image": "图片Base64数据"}, ...]
    """
    image_results = []
    num_images = min(num_images, MAX_IMAGES_PER_STORY)
    
    # 分析故事结构，提取关键场景（传递年龄段参数）
    scenes = extract_scenes_from_story(story_text, num_images, age_group)
    
    for i, scene_data in enumerate(scenes):
        # 判断是新格式（字典）还是旧格式（字符串）
        if isinstance(scene_data, dict):
            prompt = scene_data["prompt"]
            story_content = scene_data["story_content"]
        else:
            prompt = scene_data
            story_content = scene_data
        
        print(f"[Image Generator Gemini] 生成场景 {i+1}/{num_images}: {prompt[:50]}...")
        image_data = generate_image(prompt)
        if image_data:
            image_results.append({
                "scene": story_content,
                "image": image_data
            })
    
    return image_results

def extract_scenes_from_story(story_text: str, num_scenes: int = 3, age_group: str = "6-8") -> list:
    """
    从故事文本中提取关键情节场景（排除开头和结尾的问候语）
    
    Args:
        story_text: 故事文本
        num_scenes: 要提取的场景数量（默认值，会根据年龄段调整）
        age_group: 目标年龄段，可选值: "2-4", "4-6", "6-8"
    
    Returns:
        场景描述列表
    """
    scenes = []
    
    # 根据年龄段决定图片数量（所有年龄段都只生成1张图）
    target_scenes = 1
    
    # 清理故事文本，移除类型标签如 "(Type 1: Adventure Series)"
    cleaned_text = re.sub(r'\(Type \d+:.*?\)', '', story_text).strip()
    
    # 按段落分割
    paragraphs = cleaned_text.split('\n')
    paragraphs = [p.strip() for p in paragraphs if p.strip()]
    
    if len(paragraphs) == 0:
        return ["A beautiful children's story scene, no text"]
    
    # 过滤掉开头和结尾的非故事内容（问候语、告别语等）
    content_paragraphs = []
    for p in paragraphs:
        # 跳过问候语（只匹配段落开头，避免误过滤故事内容）
        p_lower = p.lower()
        if p_lower.startswith("hey little friend") or \
           p_lower.startswith("do you want to hear") or \
           p_lower.startswith("remember we talked about") or \
           p_lower.startswith("goodnight") or \
           p_lower.startswith("sweet dreams") or \
           p_lower.startswith("see you tomorrow") or \
           p_lower.startswith("sleep tight"):
            continue
        # 跳过非常短的段落（可能是标签或问候），放宽到10个字符
        if len(p) < 10:
            continue
        content_paragraphs.append(p)
    
    if len(content_paragraphs) == 0:
        # 如果没有过滤后的内容，使用原始段落（排除第一个和最后一个）
        content_paragraphs = paragraphs[1:-1] if len(paragraphs) > 2 else paragraphs
    
    # 根据段落数量决定生成图片数量
    total = len(content_paragraphs)
    
    if total == 0:
        return ["A beautiful children's story scene, no text"]
    
    # 严格排除第一段和最后一段（故事的开头和结尾）
    # 可选择的段落范围：[1, total-2]，即排除索引0和索引total-1
    if total <= 2:
        # 如果只有2段或更少，无法排除首尾，使用全部段落
        available_indices = list(range(total))
    else:
        # 排除第一段（索引0）和最后一段（索引total-1）
        available_indices = list(range(1, total - 1))
    
    available_count = len(available_indices)
    
    if available_count == 0:
        # 如果没有可选择的段落，使用所有段落
        available_indices = list(range(total))
        available_count = total
    
    print(f"[Scene Extract] 总段落数: {total}, 可用段落: {available_count}, 目标图片数: {target_scenes}")
    print(f"[Scene Extract] 可用索引: {available_indices}")
    
    # 从可用段落中均匀选择（支持同一段落提取多个句子）
    indices = []
    
    # 如果可用段落足够，均匀选择不同段落
    if available_count >= target_scenes:
        if target_scenes == 1:
            # 选中间的段落
            indices = [available_indices[available_count // 2]]
        elif target_scenes == 2:
            # 选前1/3和后2/3处的段落
            indices = [
                available_indices[available_count // 3],
                available_indices[2 * available_count // 3]
            ]
        else:
            # 选3个均匀分布的段落
            indices = [
                available_indices[available_count // 4],
                available_indices[available_count // 2],
                available_indices[3 * available_count // 4]
            ]
    else:
        # 如果可用段落不足，重复使用段落（从同一段落提取多个句子）
        # 优先使用中间的段落，因为中间段落通常包含更多情节
        main_idx = available_indices[available_count // 2]
        for i in range(target_scenes):
            # 循环使用可用段落
            indices.append(available_indices[i % available_count])
    
    # 去重（保留顺序）
    seen = set()
    indices = [idx for idx in indices if idx not in seen and not seen.add(idx)]
    
    # 如果去重后数量不够，补充重复的段落索引（允许同一段落生成多张图片）
    while len(indices) < target_scenes:
        # 添加重复的索引，允许从同一段落提取多个句子
        indices.append(indices[-1] if indices else available_indices[0])
    
    print(f"[Scene Extract] 选择索引: {indices}, 数量: {len(indices)}")
    
    # 提取选中的场景
    style_prompts = [
        "Single scene, warm colors, soft lighting, fairy tale style, detailed background, centered composition, no text, clean borders, children's book illustration",
        "Single scene, magical atmosphere, fantasy elements, vibrant colors, dynamic composition, centered focus, no text, clean borders, children's book illustration", 
        "Single scene, dramatic lighting, emotional moment, story climax, detailed characters, centered composition, no text, clean borders, children's book illustration"
    ]
    
    # 跟踪每个段落已经使用了哪些句子位置（用于同一段落多次选中时提取不同句子）
    paragraph_used_positions = {}
    
    for i, idx in enumerate(indices[:target_scenes]):
        if idx < total:
            paragraph = content_paragraphs[idx]
            
            # 如果同一段落被多次选中，提取不同的句子
            if idx not in paragraph_used_positions:
                paragraph_used_positions[idx] = 0
            
            current_pos = paragraph_used_positions[idx]
            
            # 提取第current_pos个完整句子
            scene_desc = extract_nth_sentence(paragraph, current_pos, max_length=100)
            
            # 更新已使用位置
            paragraph_used_positions[idx] += 1
            
            style = style_prompts[i % len(style_prompts)]
            # 使用更明确的提示词格式
            scene = f"Children's story book illustration, one single scene, {scene_desc}, {style}"
            scenes.append({"prompt": scene, "story_content": scene_desc})
    
    # 不补充通用场景，确保所有插图都来自故事内容
    
    return scenes

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
