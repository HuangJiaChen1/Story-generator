# tts重连5次版
import requests
import json
import os
import wave
import io
import numpy as np
import base64
import sys

# 加载配置
CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config.json')
CONFIG = {}
if os.path.exists(CONFIG_PATH):
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        CONFIG = json.load(f)

# 默认配置
DEFAULT_TTS_URL = CONFIG.get('tts_url', 'https://0636fd4d517e5-pro-hk.51wanxue.com/wonderlens-api')
DEFAULT_SPEED = 0.9  # 根据之前需求，英文语音语速调整为0.9倍


def is_audio_noisy(audio_bytes: bytes, noise_threshold: float = 20.0) -> bool:
    """
    检测音频是否为噪音（通过零交叉率判断）
    
    Args:
        audio_bytes: 音频字节数据
        noise_threshold: 噪音阈值（零交叉率百分比），默认10%
    
    Returns:
        True 如果检测到噪音，False 否则
    """
    try:
        with wave.open(io.BytesIO(audio_bytes), 'rb') as wf:
            frames = wf.readframes(wf.getnframes())
            audio_data = np.frombuffer(frames, dtype=np.int16)
            
            # 计算零交叉率
            zero_crossings = np.sum(np.diff(np.sign(audio_data)) != 0)
            zero_cross_rate = zero_crossings / len(audio_data) * 100
            
            # 输出调试信息
            if hasattr(sys, 'debug_print'):
                print(f"[Noise Check] 零交叉率: {zero_cross_rate:.2f}%, 阈值: {noise_threshold}%")
            
            return zero_cross_rate > noise_threshold
            
    except Exception:
        return False


def synthesize_audio_streaming(text: str, age_tier: int = 2, speed: float = DEFAULT_SPEED,
                                base_url: str = DEFAULT_TTS_URL, debug: bool = False) -> bytes:
    """
    使用 WonderLens TTS one-shot audio 接口生成音频（带重试机制）
    
    Args:
        text: 要转换的文本
        age_tier: 年龄段（1=2-4岁, 2=4-6岁, 3=6-8岁）
        speed: 语速，0.5-2.0，默认0.9
        base_url: TTS API 基础URL
        debug: 是否输出调试信息
    
    Returns:
        音频字节数据
    
    Raises:
        Exception: TTS 请求失败时抛出异常
    """
    if not text or not text.strip():
        raise ValueError("文本内容不能为空")
    
    # 使用 one-shot audio 接口
    url = base_url.rstrip('/') + '/api/v1/tts/synthesize/audio'
    
    payload = {
        "text": text.strip(),
        "age_tier": age_tier
    }
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "audio/*",
        "X-Client-Type": "web-app",
    }
    
    if debug:
        print("[TTS Debug] One-Shot 接口请求URL: " + url)
        print("[TTS Debug] 请求体: " + json.dumps(payload, indent=2))
    
    max_retries = 5  # 增加重试次数
    last_exception = None
    import time
    
    for attempt in range(max_retries):
        try:
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=120  # 增加超时时间到120秒
            )
            
            if debug:
                print("[TTS Debug] 响应状态码: " + str(response.status_code))
                print("[TTS Debug] 响应内容长度: " + str(len(response.content)) + " bytes")
            
            if response.ok:
                return response.content
            elif response.status_code == 504:
                # 服务端超时，重试（指数退避）
                wait_time = 2 ** attempt  # 1, 2, 4, 8, 16秒
                last_exception = Exception(f"TTS 请求超时（第{attempt+1}次尝试）")
                if debug:
                    print(f"[TTS Debug] 超时，等待 {wait_time} 秒后重试...")
                time.sleep(wait_time)
                continue
            else:
                error_msg = "TTS 请求失败，状态码: " + str(response.status_code)
                try:
                    error_data = response.json()
                    if "message" in error_data:
                        error_msg += ", 错误信息: " + error_data["message"]
                except:
                    try:
                        error_msg += ", 响应内容: " + response.text[:500]
                    except:
                        pass
                raise Exception(error_msg)
        
        except requests.exceptions.RequestException as e:
            # 请求异常，重试（指数退避）
            wait_time = 2 ** attempt
            last_exception = Exception(f"TTS 请求异常（第{attempt+1}次尝试）: " + str(e))
            if debug:
                print(f"[TTS Debug] 请求异常: {e}, 等待 {wait_time} 秒后重试...")
            time.sleep(wait_time)
            continue
    
    # 所有重试都失败
    raise last_exception or Exception("TTS 请求失败，所有重试都已耗尽")


def synthesize_audio_streaming_sse(text: str, age_tier: int = 2, speed: float = DEFAULT_SPEED,
                                      base_url: str = DEFAULT_TTS_URL, debug: bool = False) -> bytes:
    """
    使用 WonderLens TTS 流式 SSE 接口生成音频（带重试机制）
    
    Args:
        text: 要转换的文本
        age_tier: 年龄段（1=2-4岁, 2=4-6岁, 3=6-8岁）
        speed: 语速，0.5-2.0，默认0.9
        base_url: TTS API 基础URL
        debug: 是否输出调试信息
    
    Returns:
        音频字节数据
    
    Raises:
        Exception: TTS 请求失败时抛出异常
    """
    if not text or not text.strip():
        raise ValueError("文本内容不能为空")
    
    # 使用流式 SSE 接口
    url = base_url.rstrip('/') + '/api/v1/tts/stream'
    
    payload = {
        "text": text.strip(),
        "age_tier": age_tier
    }
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
        "X-Client-Type": "web-app",
    }
    
    if debug:
        print("[TTS Streaming Debug] 请求URL: " + url)
        print("[TTS Streaming Debug] 请求体: " + json.dumps(payload, indent=2))
    
    max_retries = 5
    last_exception = None
    import time
    
    for attempt in range(max_retries):
        try:
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                stream=True,
                timeout=120
            )
            
            if debug:
                print("[TTS Streaming Debug] 响应状态码: " + str(response.status_code))
            
            if not response.ok:
                if response.status_code == 504:
                    wait_time = 2 ** attempt
                    last_exception = Exception(f"TTS 请求超时（第{attempt+1}次尝试）")
                    if debug:
                        print(f"[TTS Streaming Debug] 超时，等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
                    continue
                else:
                    error_msg = "TTS 请求失败，状态码: " + str(response.status_code)
                    try:
                        error_data = response.json()
                        if "message" in error_data:
                            error_msg += ", 错误信息: " + error_data["message"]
                    except:
                        try:
                            error_msg += ", 响应内容: " + response.text[:500]
                        except:
                            pass
                    raise Exception(error_msg)
            
            # 解析 SSE 事件流
            audio_chunks = []
            chunks_received = 0
            
            for line in response.iter_lines(decode_unicode=True):
                if not line:
                    continue
                
                if line.startswith('data:'):
                    try:
                        data_str = line[5:].strip()
                        envelope = json.loads(data_str)
                        
                        event_type = envelope.get('type')
                        event_data = envelope.get('data', {})
                        
                        if debug:
                            print(f"[TTS Streaming Debug] 收到事件: {event_type}")
                        
                        if event_type == 'audio':
                            chunk_b64 = event_data.get('chunk')
                            if chunk_b64:
                                chunk_bytes = base64.b64decode(chunk_b64)
                                audio_chunks.append(chunk_bytes)
                                chunks_received += 1
                                if debug:
                                    print(f"[TTS Streaming Debug] 收到音频片段 {chunks_received}, 大小: {len(chunk_bytes)} bytes")
                        
                        elif event_type == 'tts_complete':
                            if debug:
                                print(f"[TTS Streaming Debug] TTS 完成，共收到 {chunks_received} 个片段")
                            if len(audio_chunks) == 0:
                                raise Exception("未收到任何音频片段")
                            
                            # 合并音频片段
                            audio_data_parts = []
                            for chunk in audio_chunks:
                                if len(chunk) > 44:
                                    audio_data_parts.append(chunk[44:])
                            
                            audio_data = b''.join(audio_data_parts)
                            first_chunk = audio_chunks[0]
                            wav_header = first_chunk[:44]
                            file_size = 36 + len(audio_data)
                            wav_output = bytearray(wav_header)
                            wav_output[4:8] = file_size.to_bytes(4, 'little')
                            wav_output[40:44] = len(audio_data).to_bytes(4, 'little')
                            
                            return bytes(wav_output) + audio_data
                        
                        elif event_type == 'error':
                            error_msg = event_data.get('message', 'TTS 流式生成失败')
                            raise Exception(error_msg)
                    
                    except json.JSONDecodeError:
                        continue
                    except Exception as e:
                        if debug:
                            print(f"[TTS Streaming Debug] 处理事件失败: {e}")
                        continue
            
            # 如果循环结束但没有收到 tts_complete
            if len(audio_chunks) > 0:
                audio_data_parts = []
                for chunk in audio_chunks:
                    if len(chunk) > 44:
                        audio_data_parts.append(chunk[44:])
                audio_data = b''.join(audio_data_parts)
                first_chunk = audio_chunks[0]
                wav_header = first_chunk[:44]
                file_size = 36 + len(audio_data)
                wav_output = bytearray(wav_header)
                wav_output[4:8] = file_size.to_bytes(4, 'little')
                wav_output[40:44] = len(audio_data).to_bytes(4, 'little')
                return bytes(wav_output) + audio_data
            else:
                raise Exception("未收到任何音频数据")
        
        except requests.exceptions.RequestException as e:
            wait_time = 2 ** attempt
            last_exception = Exception(f"TTS 请求异常（第{attempt+1}次尝试）: " + str(e))
            if debug:
                print(f"[TTS Streaming Debug] 请求异常: {e}, 等待 {wait_time} 秒后重试...")
            time.sleep(wait_time)
            continue
    
    raise last_exception or Exception("TTS 请求失败，所有重试都已耗尽")


def synthesize_audio(text: str, age_tier: int = 2, speed: float = DEFAULT_SPEED, 
                     base_url: str = DEFAULT_TTS_URL, debug: bool = False, 
                     amplify_gain: float = 1.0, check_noise: bool = True) -> bytes:
    """
    调用 WonderLens TTS API 生成音频（根据年龄段选择接口）
    
    Args:
        text: 要转换的文本
        age_tier: 年龄段（1=2-4岁, 2=4-6岁, 3=6-8岁）
        speed: 语速，0.5-2.0，默认0.9
        base_url: TTS API 基础URL
        debug: 是否输出调试信息
        amplify_gain: 音量放大倍数，默认1.0（不放大）
        check_noise: 是否检测噪音，默认开启
    
    Returns:
        音频字节数据
    
    Raises:
        Exception: TTS 请求失败时抛出异常
    """
    if not text or not text.strip():
        raise ValueError("文本内容不能为空")
    
    # 根据年龄段选择接口：
    # - 2-4岁 (age_tier=1) 和 4-6岁 (age_tier=2) 使用 one-shot 接口
    # - 6-8岁 (age_tier=3) 使用流式 SSE 接口
    if age_tier == 3:
        if debug:
            print("[TTS Debug] 6-8岁年龄段，使用流式 SSE 接口")
        content = synthesize_audio_streaming_sse(text, age_tier, speed, base_url, debug)
    else:
        if debug:
            print("[TTS Debug] 2-4岁或4-6岁年龄段，使用 one-shot 接口")
        content = synthesize_audio_streaming(text, age_tier, speed, base_url, debug)
    
    # 验证音频数据
    if len(content) < 44:
        raise Exception("音频数据过短，可能不是有效音频: " + str(len(content)) + " bytes")
    
    # 检查 WAV 文件头
    if content[:4] != b'RIFF':
        if debug:
            print("[TTS Debug] 警告：不是标准 WAV 文件，文件头: " + content[:16].hex())
    
    # 检测噪音
    if check_noise:
        # 临时输出调试信息
        try:
            with wave.open(io.BytesIO(content), 'rb') as wf:
                frames = wf.readframes(wf.getnframes())
                audio_data = np.frombuffer(frames, dtype=np.int16)
                zero_crossings = np.sum(np.diff(np.sign(audio_data)) != 0)
                zero_cross_rate = zero_crossings / len(audio_data) * 100
                if debug:
                    print("[TTS Debug] 零交叉率: " + str(zero_cross_rate)[:5] + "%")
        except Exception:
            pass
        
        if is_audio_noisy(content):
            raise Exception("TTS API 返回的音频数据检测到噪音")
    
    # 如果需要放大音量
    if amplify_gain != 1.0:
        content = amplify_audio(content, gain=amplify_gain)
        if debug:
            print("[TTS Debug] 音量放大 " + str(amplify_gain) + " 倍")
    
    return content


def estimate_audio_duration(text: str, words_per_minute: int = 150) -> float:
    """
    估算音频播放时间（秒）
    
    Args:
        text: 文本内容
        words_per_minute: 每分钟单词数（英文朗读速度）
    
    Returns:
        预计播放时间（秒）
    """
    # 简单估算：按单词数计算
    word_count = len(text.split())
    minutes = word_count / words_per_minute
    return minutes * 60


def format_duration(seconds: float) -> str:
    """
    格式化时间显示
    
    Args:
        seconds: 秒数
    
    Returns:
        格式化的时间字符串（如 "2分30秒"）
    """
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    
    if minutes > 0:
        return str(minutes) + "分" + str(secs) + "秒"
    else:
        return str(secs) + "秒"


def amplify_audio(audio_bytes: bytes, gain: float = 2.0) -> bytes:
    """
    放大音频音量
    
    Args:
        audio_bytes: 原始音频字节数据（WAV格式）
        gain: 放大倍数，默认2.0倍
    
    Returns:
        放大后的音频字节数据
    """
    # 读取WAV文件
    with wave.open(io.BytesIO(audio_bytes), 'rb') as wf:
        params = wf.getparams()
        frames = wf.readframes(wf.getnframes())
    
    sample_width = params.sampwidth
    
    if sample_width == 2:  # 16位
        audio_data = np.frombuffer(frames, dtype=np.int16)
        audio_data = (audio_data * gain).astype(np.int16)
        # 防止溢出
        audio_data = np.clip(audio_data, -32768, 32767)
    elif sample_width == 4:  # 32位
        audio_data = np.frombuffer(frames, dtype=np.int32)
        audio_data = (audio_data * gain).astype(np.int32)
        audio_data = np.clip(audio_data, -2147483648, 2147483647)
    else:  # 8位
        audio_data = np.frombuffer(frames, dtype=np.uint8)
        audio_data = (audio_data - 128) * gain + 128
        audio_data = np.clip(audio_data, 0, 255).astype(np.uint8)
    
    # 写回WAV格式
    output_buffer = io.BytesIO()
    with wave.open(output_buffer, 'wb') as wf:
        wf.setparams(params)
        wf.writeframes(audio_data.tobytes())
    
    return output_buffer.getvalue()


# 测试代码
if __name__ == "__main__":
    test_text = "Hello little friend! Do you want to hear a story about a photo album, a music box, and a rocking chair? Today's story is about Lila, who loved quiet afternoons when rain pattered on the roof like tiny drumbeats. Her grandma’s old wooden rocking chair sat by the window, its green velvet cushion soft and slightly lumpy. On the side table rested a dusty photo album with silver stars on the cover—and next to it, a small music box shaped like a sleepy owl, its brass key twisted just so."
    
    print("测试 WonderLens TTS API:")
    print("=" * 60)
    print("测试文本: " + test_text[:50] + "...")
    print("TTS URL: " + DEFAULT_TTS_URL)
    print("语速: " + str(DEFAULT_SPEED))
    print()
    
    try:
        # 估算时间
        duration = estimate_audio_duration(test_text)
        print("预计播放时间: " + format_duration(duration))
        print()
        
        # 生成音频（启用调试模式，放大音量3倍）
        print("正在生成音频（音量放大3倍）...")
        audio_bytes = synthesize_audio(test_text, age_tier=2, debug=True, amplify_gain=1.0)
        
        # 保存测试文件
        output_path = "test_tts_output1.wav"
        with open(output_path, "wb") as f:
            f.write(audio_bytes)
        
        print()
        print("音频生成成功！")
        print("输出文件: " + output_path)
        print("文件大小: " + str(len(audio_bytes) / 1024)[:5] + " KB")
        
        # 检查文件头
        if audio_bytes[:4] == b'RIFF':
            print("是标准 WAV 文件格式")
        else:
            print("警告：文件头不是 RIFF，实际头: " + audio_bytes[:8].hex())
        
        # 分析音频数据
        print()
        print("音频数据分析:")
        print("-" * 40)
        with wave.open(output_path, 'rb') as wf:
            frames = wf.readframes(wf.getnframes())
            audio_data = np.frombuffer(frames, dtype=np.int16)
            print("采样率: " + str(wf.getframerate()) + " Hz")
            print("声道数: " + str(wf.getnchannels()))
            print("位深度: " + str(wf.getsampwidth() * 8) + " 位")
            print("时长: " + str(wf.getnframes() / wf.getframerate())[:5] + " 秒")
            print("最大值: " + str(audio_data.max()))
            print("最小值: " + str(audio_data.min()))
            print("标准差: " + str(audio_data.std())[:6])
            max_amplitude_percent = audio_data.max() / 32767 * 100
            print("最大振幅占比: " + str(max_amplitude_percent)[:5] + "%")
            
            # 计算零交叉率
            zero_crossings = np.sum(np.diff(np.sign(audio_data)) != 0)
            zero_cross_rate = zero_crossings / len(audio_data) * 100
            print("零交叉率: " + str(zero_cross_rate)[:5] + "%")
            print("是否检测到噪音: " + ("是" if zero_cross_rate > 20 else "否"))
            
            has_signal = np.max(np.abs(audio_data)) > 100
            print("是否有声音信号: " + ("是" if has_signal else "否"))
        
        print()
        print("提示：请用 Windows Media Player 或其他音频播放器打开测试文件")
        
    except Exception as e:
        print("音频生成失败: " + str(e))