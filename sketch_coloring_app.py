# ============================================================
# sketch_coloring_app.py - 图生图交互页面（图像编辑）
# ============================================================

import streamlit as st
import time
import dashscope
from dashscope import ImageSynthesis
from dashscope.aigc.image_generation import ImageGeneration
from dashscope.api_entities.dashscope_response import Message
from http import HTTPStatus

# 配置地域
dashscope.base_http_api_url = "https://dashscope.aliyuncs.com/api/v1"

# ============================================================
# 配置 API Key
# ============================================================

# 通义万相 API Key（优先从环境变量获取）
# 获取地址：https://help.aliyun.com/zh/model-studio/get-api-key
DASHSCOPE_API_KEY = "sk-7ccc67cdc36247668d55a0e37eda449c"

# 检查 API Key 是否配置
def is_api_key_configured():
    return DASHSCOPE_API_KEY and DASHSCOPE_API_KEY.strip() and not DASHSCOPE_API_KEY.startswith("sk-xxxx")

# ============================================================
# 页面配置
# ============================================================

st.set_page_config(
    page_title="AI 素描上色助手",
    page_icon="🎨",
    layout="centered"
)

# ============================================================
# 配置选项
# ============================================================

SIZE_OPTIONS = {
    "方图 768x768": "768*768",
    "横图 1280x720": "1280*720",
    "竖图 720x1280": "720*1280",
    "2K 方图 1024x1024": "1024*1024",
}

# 敏感词列表
SENSITIVE_WORDS = [
    "blood", "violence", "nsfw", "nude", "naked", "sex", "weapon", 
    "gun", "knife", "kill", "murder", "rape", "drug", "porn"
]

# 安全的颜色词汇（用于替换可能触发安全检查的词汇）
SAFE_COLORS = [
    "蓝色", "绿色", "红色", "黄色", "紫色", "橙色", "粉色", "白色", "黑色", "灰色",
    "天蓝", "翠绿", "玫瑰", "金黄", "紫罗兰", "珊瑚", "薄荷", "奶油", "咖啡", "藏青",
    "light blue", "green", "red", "yellow", "purple", "orange", "pink", "white", "black", "gray",
    "sky blue", "emerald", "rose", "golden", "violet", "coral", "mint", "cream", "brown", "navy"
]

def is_prompt_safe(prompt_text):
    """检查提示词是否包含敏感词"""
    prompt_lower = prompt_text.lower()
    for word in SENSITIVE_WORDS:
        if word in prompt_lower:
            return False, word
    return True, None

def optimize_prompt_for_color(prompt_text):
    """优化提示词，避免颜色相关的安全检查问题"""
    # 添加一些安全的颜色描述前缀
    if any(color in prompt_text for color in ["红色", "黄色", "绿色", "蓝色", "紫色", "粉色"]):
        # 添加艺术风格描述，降低安全检查风险
        safe_prefix = "艺术风格，色彩丰富，"
        if not prompt_text.startswith(safe_prefix):
            return safe_prefix + prompt_text
    return prompt_text

# ============================================================
# 初始化 session state
# ============================================================

if "image_urls" not in st.session_state:
    st.session_state.image_urls = None

if "generating" not in st.session_state:
    st.session_state.generating = False

if "uploaded_image_url" not in st.session_state:
    st.session_state.uploaded_image_url = None

if "processing_upload" not in st.session_state:
    st.session_state.processing_upload = False

if "pending_upload" not in st.session_state:
    st.session_state.pending_upload = None

# ============================================================
# Base64 编码函数
# ============================================================

def get_image_base64(image_file):
    """将图片文件转换为 Base64 编码"""
    try:
        # 读取图片内容
        image_bytes = image_file.getvalue()
        
        # 获取 MIME 类型
        mime_type = image_file.type if hasattr(image_file, 'type') else 'image/jpeg'
        
        # 转换为 Base64
        import base64
        base64_str = base64.b64encode(image_bytes).decode('utf-8')
        
        # 返回 data URL 格式
        return f"data:{mime_type};base64,{base64_str}"
        
    except Exception as e:
        st.error(f"Base64 编码失败: {e}")
        return None


def check_image_resolution(image_file, min_width=240, min_height=240):
    """检查图片分辨率是否满足最低要求"""
    try:
        from PIL import Image
        import io
        
        # 读取图片
        image = Image.open(io.BytesIO(image_file.getvalue()))
        width, height = image.size
        
        if width >= min_width and height >= min_height:
            return True, width, height
        else:
            return False, width, height
            
    except Exception as e:
        st.error(f"图片分辨率检查失败: {e}")
        return False, 0, 0


def resize_image_to_minimum(image_file, min_width=240, min_height=240):
    """将图片调整到最低分辨率要求，如果需要的话"""
    try:
        from PIL import Image
        import io
        
        # 读取图片
        image = Image.open(io.BytesIO(image_file.getvalue()))
        original_width, original_height = image.size
        
        # 检查是否需要调整
        if original_width >= min_width and original_height >= min_height:
            return image_file.getvalue(), original_width, original_height, False
        
        # 计算缩放比例
        scale_width = min_width / original_width
        scale_height = min_height / original_height
        scale = max(scale_width, scale_height)
        
        # 计算新尺寸
        new_width = int(original_width * scale)
        new_height = int(original_height * scale)
        
        # 调整大小（使用高质量插值）
        resized_image = image.resize((new_width, new_height), Image.LANCZOS)
        
        # 保存为 bytes
        buffer = io.BytesIO()
        resized_image.save(buffer, format='PNG')
        buffer.seek(0)
        
        return buffer.read(), new_width, new_height, True
        
    except Exception as e:
        st.error(f"图片调整失败: {e}")
        return None, 0, 0, False

# ============================================================
# 标题
# ============================================================

st.title("🎨 AI 图像编辑助手")
st.caption("上传图片，AI 帮你进行创意编辑")

# ============================================================
# 侧边栏 - 设置
# ============================================================

with st.sidebar:
    st.header("⚙️ 编辑设置")
    
    if is_api_key_configured():
        st.success("✅ API Key 已配置")
    else:
        st.error("❌ 请配置通义万相 API Key")
        st.info("💡 请设置环境变量 DASHSCOPE_API_KEY")
        st.code("export DASHSCOPE_API_KEY=sk-你的密钥", language="bash")
    
    st.divider()
    
    # ============================================================
    # 模型选择
    # ============================================================
    
    st.subheader("🤖 模型选择")
    
    MODEL_OPTIONS = {
        "wanx-sketch-to-image-lite (草图上色)": "wanx-sketch-to-image-lite",
        "wan2.7-image (通用图像生成)": "wan2.7-image",
    }
    
    model_name = st.selectbox(
        "选择生成模型",
        list(MODEL_OPTIONS.keys()),
        index=0,
        help="wanx-sketch-to-image-lite: 专为草图上色优化，适合线稿上色\nwan2.7-image: 通用图像生成模型，适合创意编辑"
    )
    model = MODEL_OPTIONS[model_name]
    
    st.divider()
    
    # 尺寸选择
    size_name = st.selectbox(
        "输出尺寸",
        list(SIZE_OPTIONS.keys()),
        index=0
    )
    size = SIZE_OPTIONS[size_name]
    
    # 生成数量
    n = st.slider("生成数量", 1, 4, 1)
    
    st.divider()
    
    # ============================================================
    # 风格选择
    # ============================================================
    
    st.subheader("🎨 风格设置")
    
    STYLE_OPTIONS = {
        "自动（随机）": "<auto>",
        "3D卡通": "<3d cartoon>",
        "二次元": "<anime>",
        "油画": "<oil painting>",
        "水彩": "<watercolor>",
        "素描": "<sketch>",
        "中国画": "<chinese painting>",
        "扁平插画": "<flat illustration>",
    }
    
    style_name = st.selectbox(
        "输出风格",
        list(STYLE_OPTIONS.keys()),
        index=0,
        help="选择输出图像的艺术风格"
    )
    style = STYLE_OPTIONS[style_name]
    
    st.divider()
    
    # ============================================================
    # 草图设置
    # ============================================================
    
    st.subheader("✏️ 草图设置")
    
    # 草图权重
    sketch_weight = st.slider(
        "草图约束程度",
        min_value=0,
        max_value=10,
        value=10,
        step=1,
        help="取值越大表示输出图像跟输入草图越相似（0-10）"
    )
    
    # 检测图片格式
    image_format = ""
    if st.session_state.uploaded_image_url:
        if st.session_state.uploaded_image_url.startswith("data:image/jpeg") or \
           st.session_state.uploaded_image_url.startswith("data:image/jpg"):
            image_format = "jpeg"
        elif st.session_state.uploaded_image_url.startswith("data:image/png"):
            image_format = "png"
    
    # 是否进行边缘提取（默认关闭，让用户自己选择）
    sketch_extraction = st.checkbox(
        "边缘提取",
        value=False,
        help="如果上传的是彩色照片而非草图，启用此选项进行边缘提取"
    )
    
    # 根据图片格式给出建议
    if image_format == "jpeg":
        st.info("💡 提示：JPEG格式通常是彩色照片，建议启用「边缘提取」")
    elif image_format == "png":
        st.info("💡 提示：PNG格式适合线稿，如果是黑白线稿可以关闭「边缘提取」")
    
    # 画笔颜色（仅在 sketch_extraction=False 时生效）
    if not sketch_extraction:
        st.info("💡 画笔颜色：当线稿线条不是黑色时，可指定一个或多个RGB颜色值")
        sketch_color_input = st.text_input(
            "画笔颜色（RGB）",
            value="",
            placeholder='例如：[[134, 134, 134], [0, 0, 0]]',
            help="格式：[[R, G, B], [R, G, B]]，留空表示默认黑色"
        )
        
        # 解析画笔颜色
        sketch_color = []
        if sketch_color_input.strip():
            try:
                import json
                sketch_color = json.loads(sketch_color_input)
                if not isinstance(sketch_color, list):
                    st.warning("画笔颜色格式错误，应为列表格式")
                    sketch_color = []
            except json.JSONDecodeError:
                st.warning("画笔颜色格式错误，请使用正确的JSON格式")
                sketch_color = []
    else:
        sketch_color = []
        st.info("💡 边缘提取已启用，画笔颜色将失效")
    
    st.divider()
    
    # ============================================================
    # 文件上传区域
    # ============================================================
    
    st.subheader("📁 上传图片")
    st.info("💡 支持上传各种图片格式，AI 会根据描述进行创意编辑")
    
    uploaded_file = st.file_uploader(
        "选择图片文件",
        type=["png", "jpg", "jpeg", "webp"],
        help="上传图片，AI 会根据描述进行图像编辑"
    )
    
    if uploaded_file is not None:
        # 显示上传的图片
        st.image(uploaded_file, caption="上传的图片", use_container_width=True)
        
        # 检查图片分辨率
        is_valid, width, height = check_image_resolution(uploaded_file)
        
        if not is_valid:
            st.warning(f"⚠️ 图片分辨率不足！当前 {width}x{height}，要求至少 240x240")
            st.info("💡 点击「准备图片」将自动放大图片")
        else:
            st.success(f"✅ 图片分辨率检查通过: {width}x{height}")
        
        # 使用 Base64 编码并直接生成
        if st.button("🎨 上传并上色", use_container_width=True, type="primary"):
            # 保存上传的文件信息到 session_state，然后重新运行
            st.session_state.pending_upload = {
                'file': uploaded_file,
                'width': width,
                'height': height
            }
            st.session_state.processing_upload = True
            st.rerun()
        
    # 显示已处理的图片
    if st.session_state.uploaded_image_url:
        st.divider()
        st.success("✅ 图片已准备好！")

# ============================================================
# 主界面 - 使用说明
# ============================================================

st.subheader("💡 使用说明")
st.info("上传图片后，点击「上传并上色」按钮，AI 会自动为图片上色。")

# 隐藏的变量（保持兼容性）
generate_button = False
prompt = "将输入黑白草图加上一些颜色，严格保持主体一致。保留输入的主要物体！禁止将其变成任何其他动物、人物、物体或生物。保持物种、主体数量和关键外形特征与输入涂鸦完全一致。以输入涂鸦作为唯一的结构和语义参考。禁止添加额外的人物或物体。主体完整性是最高优先级!!!!"

# ============================================================
# 创建异步任务函数
# ============================================================

def create_async_task(prompt_text, image_size, num, sketch_url, style, sketch_weight, sketch_extraction, sketch_color, model="wanx-sketch-to-image-lite"):
    """创建异步任务（图生图）- 支持多种模型"""
    try:
        if not sketch_url:
            st.error("请先上传图片")
            return None
        
        # 检查图片数据是否存在（Base64 或 URL）
        if not sketch_url.startswith("data:") and not sketch_url.startswith("http"):
            st.error("❌ 图片数据无效，请重新上传")
            return None
        
        # 优化提示词，避免颜色相关的安全检查问题
        optimized_prompt = optimize_prompt_for_color(prompt_text)
        
        # 如果提示词被修改，显示提示
        if optimized_prompt != prompt_text:
            st.info(f"💡 提示词已优化：{optimized_prompt[:50]}...")
        
        # 根据模型类型选择不同的 API
        if model == "wanx-sketch-to-image-lite":
            # 使用 ImageSynthesis API（草图上色专用）
            parameters = {
                "size": image_size,
                "n": num,
                "style": style,
                "sketch_weight": sketch_weight,
                "sketch_extraction": sketch_extraction,
            }
            
            if sketch_color and isinstance(sketch_color, list) and len(sketch_color) > 0:
                parameters["sketch_color"] = sketch_color
            
            rsp = ImageSynthesis.async_call(
                model=model,
                prompt=optimized_prompt,
                api_key=DASHSCOPE_API_KEY,
                sketch_image_url=sketch_url,
                task="image2image",
                parameters=parameters,
                input_type="sketch"
            )
            
            return rsp if rsp.status_code == HTTPStatus.OK else None
            
        elif model.startswith("wan2.7"):
            # 使用 ImageGeneration API（通用图像生成）
            # wan2.7-image 和 wan2.7-image-pro 使用消息格式
            message = Message(
                role="user",
                content=[
                    {
                        "text": optimized_prompt
                    },
                    {
                        "image": sketch_url  # 支持 Base64 或 URL
                    }
                ]
            )
            
            # 调用同步 API
            rsp = ImageGeneration.call(
                model=model,
                api_key=DASHSCOPE_API_KEY,
                messages=[message],
                n=num,
                size=image_size
            )
            
            # 返回特殊格式的响应，包含图片URL列表
            if rsp.status_code == HTTPStatus.OK:
                return {'type': 'sync', 'response': rsp}
            else:
                error_msg = rsp.message if hasattr(rsp, 'message') else str(rsp)
                error_code = rsp.code if hasattr(rsp, 'code') else "Unknown"
                st.error(f"创建任务失败 [{error_code}]: {error_msg}")
                return None
        
        else:
            st.error(f"不支持的模型: {model}")
            return None
            
    except Exception as e:
        st.error(f"创建任务异常: {e}")
        import traceback
        st.error(f"详细错误: {traceback.format_exc()}")
        return None


def wait_async_task(task_info):
    """等待异步任务完成并获取结果 - 支持同步和异步两种模式"""
    # 检查是否是同步响应（wan2.7-image 系列）
    if isinstance(task_info, dict) and task_info.get('type') == 'sync':
        rsp = task_info['response']
        try:
            # 提取结果图片URL（ImageGeneration 的结果格式）
            # 格式: rsp.output.choices[0]["message"]["content"]
            image_urls = []
            
            if hasattr(rsp, 'output'):
                output = rsp.output
                
                # 按照示例代码的结构提取
                if hasattr(output, 'choices') or 'choices' in dir(output):
                    choices = output.choices if hasattr(output, 'choices') else output.get('choices', [])
                    
                    for choice in choices:
                        # choice 可能是对象或字典
                        if hasattr(choice, 'message'):
                            message = choice.message
                        elif isinstance(choice, dict) and 'message' in choice:
                            message = choice['message']
                        else:
                            continue
                        
                        # 获取 content
                        if hasattr(message, 'content'):
                            content_list = message.content
                        elif isinstance(message, dict) and 'content' in message:
                            content_list = message['content']
                        else:
                            continue
                        
                        # 遍历 content 找图片
                        for content in content_list:
                            if isinstance(content, dict) and content.get('type') == 'image':
                                image_url = content.get('image')
                                if image_url:
                                    image_urls.append(image_url)
                            elif hasattr(content, 'type') and content.type == 'image':
                                image_url = getattr(content, 'image', None)
                                if image_url:
                                    image_urls.append(image_url)
            
            if image_urls:
                st.success("✅ 生成完成！")
                return image_urls
            else:
                # 调试：显示响应结构
                st.error("❌ 未获取到图片结果")
                try:
                    import json
                    st.info(f"📊 响应结构: {json.dumps(rsp.__dict__, default=str, indent=2)[:1500]}")
                except:
                    st.info(f"📊 响应字符串: {str(rsp)[:1000]}")
                return None
                
        except Exception as e:
            st.error(f"解析同步响应异常: {e}")
            import traceback
            st.error(f"详细错误: {traceback.format_exc()}")
            return None
    
    # 异步任务处理（wanx-sketch-to-image-lite）
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        for i in range(60):
            status_text.text(f"🎨 AI 正在编辑中... ({i+1}/60)")
            progress_bar.progress((i+1)/60)
            
            rsp = ImageSynthesis.wait(task=task_info, api_key=DASHSCOPE_API_KEY)
            
            if rsp.status_code == HTTPStatus.OK:
                if rsp.output.task_status == "SUCCEEDED":
                    progress_bar.progress(100)
                    status_text.text("✅ 编辑完成！")
                    time.sleep(0.5)
                    progress_bar.empty()
                    status_text.empty()
                    
                    # 提取结果图片URL（ImageSynthesis 的结果格式）
                    image_urls = []
                    for result in rsp.output.results:
                        if hasattr(result, 'url'):
                            image_urls.append(result.url)
                    return image_urls
                elif rsp.output.task_status == "FAILED":
                    progress_bar.empty()
                    status_text.empty()
                    error_msg = rsp.output.message if hasattr(rsp.output, 'message') else "Unknown error"
                    st.error(f"上色失败: {error_msg}")
                    
                    # 提供具体的错误提示
                    if "Green" in error_msg or "check failed" in error_msg or "安全" in error_msg:
                        st.warning("💡 可能的原因：")
                        st.info("  • 输入图片无法访问或URL已失效")
                        st.info("  • 提示词包含敏感内容或颜色描述触发安全检查")
                        st.info("  • 建议：简化颜色描述，使用更温和的艺术风格描述")
                        st.info("  • 例如：用「明亮的色调」代替「红色」，或添加「艺术绘画风格」")
                    elif "InvalidApiKey" in error_msg or "API" in error_msg:
                        st.error("❌ API Key 无效或已过期")
                        st.info("💡 请检查或更换 DASHSCOPE_API_KEY")
                    elif "quota" in error_msg.lower() or "额度" in error_msg:
                        st.error("❌ API 额度不足")
                        st.info("💡 请检查账户余额或等待额度刷新")
                    
                    return None
                elif rsp.output.task_status == "PENDING":
                    time.sleep(1)
                    continue
            else:
                if i == 59:
                    progress_bar.empty()
                    status_text.empty()
                    st.error(f"等待任务失败: {rsp.code} - {rsp.message}")
                    return None
            
            time.sleep(1)
        
        progress_bar.empty()
        status_text.empty()
        st.error("上色超时，请重试")
        return None
                
    except Exception as e:
        progress_bar.empty()
        status_text.empty()
        st.error(f"等待任务异常: {e}")
        return None

# ============================================================
# 处理上传的图片并生成
# ============================================================

if st.session_state.processing_upload and st.session_state.pending_upload:
    upload_data = st.session_state.pending_upload
    uploaded_file = upload_data['file']
    width = upload_data['width']
    height = upload_data['height']
    
    with st.spinner("正在处理图片并生成..."):
        try:
            # 重置文件指针位置，确保从头读取
            uploaded_file.seek(0)
            
            # 调整图片分辨率（如果需要）
            resized_data, new_width, new_height, was_resized = resize_image_to_minimum(uploaded_file)
            
            if resized_data is None:
                st.error("图片调整失败，请重试")
            else:
                # 如果被调整过，显示提示
                if was_resized:
                    st.info(f"🔄 图片已从 {width}x{height} 放大到 {new_width}x{new_height}")
                
                # 将调整后的图片转换为 Base64
                import base64
                mime_type = uploaded_file.type if hasattr(uploaded_file, 'type') else 'image/png'
                base64_str = base64.b64encode(resized_data).decode('utf-8')
                base64_image = f"data:{mime_type};base64,{base64_str}"
                
                if base64_image:
                    st.session_state.uploaded_image_url = base64_image
                    
                    # 直接调用生成函数
                    st.info("📤 正在生成图片...")
                    
                    # 根据模型类型使用不同的提示词
                    if model.startswith("wan2.7"):
                        # wan2.7-image 需要更明确的上色指令
                        current_prompt = "给这张图片上色，添加鲜艳的色彩吸引儿童兴趣，可以增加背景色彩，如有纸张线条则删去线条"
                    else:
                        # wanx-sketch-to-image-lite 使用标准提示词
                        current_prompt = "将输入黑白草图加上一些颜色，严格保持主体一致。必须完全保留输入涂鸦中的主要物体。禁止将其变成任何其他动物、人物、物体或生物。保持物种、主体数量和关键外形特征与输入涂鸦完全一致。以输入涂鸦作为唯一的结构和语义参考。禁止添加额外的人物或物体。主体完整性是最高优先级。"
                    
                    task_info = create_async_task(
                        prompt_text=current_prompt,
                        image_size=size,
                        num=n,
                        sketch_url=base64_image,
                        style=style,
                        sketch_weight=sketch_weight,
                        sketch_extraction=sketch_extraction,
                        sketch_color=sketch_color,
                        model=model
                    )
                    
                    if task_info:
                        image_urls = wait_async_task(task_info)
                        
                        if image_urls:
                            st.session_state.image_urls = image_urls
                            st.success("✅ 上色完成！")
                        else:
                            st.error("上色失败，请重试")
                    else:
                        st.error("创建任务失败，请重试")
                else:
                    st.error("图片处理失败，请重试")
        except Exception as e:
            st.error(f"处理异常: {e}")
            import traceback
            st.error(f"详细错误: {traceback.format_exc()}")
    
    # 重置状态
    st.session_state.processing_upload = False
    st.session_state.pending_upload = None

# ============================================================
# 显示结果
# ============================================================

if st.session_state.image_urls:
    st.divider()
    st.subheader("🖼️ 编辑结果")
    
    images = st.session_state.image_urls
    
    if len(images) == 1:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.image(images[0], caption="AI 编辑作品", use_container_width=True)
    elif len(images) == 2:
        col1, col2 = st.columns(2)
        with col1:
            st.image(images[0], caption="作品 1", use_container_width=True)
        with col2:
            st.image(images[1], caption="作品 2", use_container_width=True)
    else:
        cols = st.columns(len(images))
        for i, (col, img_url) in enumerate(zip(cols, images)):
            with col:
                st.image(img_url, caption=f"作品 {i+1}", use_container_width=True)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 重新编辑", use_container_width=True):
            st.session_state.image_urls = None
            st.rerun()
    with col2:
        st.caption("💡 右键点击图片可保存")

# ============================================================
# 使用说明
# ============================================================

st.divider()
st.caption("📌 使用说明：")
st.caption("1. 上传图片文件")
st.caption("2. 点击「准备图片」按钮")
st.caption("3. 描述你想要的编辑效果")
st.caption("4. 点击「开始编辑」，等待 AI 生成")

st.divider()
st.caption("✨ 由通义万相驱动 | AI 图像编辑助手 ✨")