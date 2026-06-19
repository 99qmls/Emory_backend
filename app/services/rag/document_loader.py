# 文件加载与解析 (支持 PDF, MD, TXT，异步处理)

"""
异步文档加载器：支持多种格式文件的文本提取
- PDF: pdfplumber
- Markdown / TXT: aiofiles
- MP4: 提取字幕 (.srt) 或使用 Whisper 语音识别
- MP3: 使用 Whisper 语音识别
"""

import os
import tempfile
import asyncio
from typing import Optional

from app.utils.minio_client import minio_client
from app.core.config import settings
from app.utils.logger import logger

try:
    import pdfplumber

    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    logger.warning("pdfplumber 未安装，PDF 解析将不可用")

try:
    import aiofiles

    TEXT_AVAILABLE = True
except ImportError:
    TEXT_AVAILABLE = False
    logger.warning("aiofiles 未安装，文本文件读取将降级为同步")

try:
    import whisper

    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    logger.warning("whisper 未安装，音视频语音识别将不可用")

# 尝试导入字幕提取库
try:
    import pysrt

    PYSRT_AVAILABLE = True
except ImportError:
    PYSRT_AVAILABLE = False


async def load_document(file_path: str, file_type: Optional[str] = None, enable_asr: bool = True) -> str:
    """
    从 MinIO 下载文件并提取文本内容
    :param file_path: MinIO 中的对象路径
    :param file_type: MIME 类型，若为 None 则根据扩展名猜测
    :param enable_asr: 是否对音视频文件启用语音识别（若无字幕），默认 True
    :return: 提取的文本字符串
    """
    ext = os.path.splitext(file_path)[1].lower()
    suffix = ext if ext else ".tmp"
    with tempfile.NamedTemporaryFile(delete=True, suffix=suffix) as tmp:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None,
            minio_client.fget_object,
            settings.MINIO_BUCKET,
            file_path,
            tmp.name
        )
        tmp_path = tmp.name
    try:
        # 2. 根据文件类型选择解析器
        if file_type is None:
            file_type = _guess_mime_from_extension(ext)

        if file_type.startswith("application/pdf") or ext == ".pdf":
            return await _parse_pdf(tmp_path)
        elif file_type.startswith("text/") or ext in (".txt", ".md", ".log"):
            return await _parse_text(tmp_path)
        elif file_type.startswith("video/") or ext in (".mp4", ".mkv", ".webm"):
            return await _parse_video(tmp_path, enable_asr)
        elif file_type.startswith("audio/") or ext in (".mp3", ".wav", ".m4a", ".flac"):
            return await _parse_audio(tmp_path, enable_asr)
        else:
            # 兜底尝试作为文本读取
            logger.warning(f"未知文件类型 {file_type}，尝试作为文本读取")
            try:
                return await _parse_text(tmp_path)
            except Exception:
                raise ValueError(f"不支持的文件格式: {file_type}")
    finally:
        # 清理临时文件
        await loop.run_in_executor(None, os.unlink, tmp_path)


def _guess_mime_from_extension(ext: str) -> str:
    mapping = {
        ".pdf": "application/pdf",
        ".txt": "text/plain",
        ".md": "text/markdown",
        ".mp4": "video/mp4",
        ".mp3": "audio/mpeg",
        ".wav": "audio/wav",
    }
    return mapping.get(ext, "application/octet-stream")


# ---------- 具体解析器 ----------
async def _parse_pdf(file_path: str) -> str:
    """异步 PDF 解析"""
    if not PDF_AVAILABLE:
        raise RuntimeError("pdfplumber 未安装，无法解析 PDF")
    loop = asyncio.get_running_loop()

    def extract():
        with pdfplumber.open(file_path) as pdf:
            text = "\n".join(
                page.extract_text() or "" for page in pdf.pages
            )
        return text

    return await loop.run_in_executor(None, extract)


async def _parse_text(file_path: str) -> str:
    """异步文本文件读取"""
    if TEXT_AVAILABLE:
        async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
            return await f.read()
    # 降级为同步读取
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _sync_read_text, file_path)


def _sync_read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


async def _parse_video(file_path: str, enable_asr: bool) -> str:
    """
    视频文本提取策略：
    1. 尝试提取内嵌字幕（.srt 文件）
    2. 若无字幕且 enable_asr=True，则导出音频并调用 Whisper 识别
    """
    # 1. 查找同名字幕文件（假设与视频同目录，可扩展）
    sub_path = _find_subtitle(file_path)
    if sub_path:
        return await _parse_subtitle(sub_path)

    # 2. 无字幕时，提取音频并进行语音识别
    if enable_asr and WHISPER_AVAILABLE:
        audio_path = await _extract_audio_from_video(file_path)
        if audio_path:
            text = await _speech_to_text(audio_path)
            os.unlink(audio_path)
            return text

    return ""


async def _parse_audio(file_path: str, enable_asr: bool) -> str:
    """音频直接转录"""
    if enable_asr and WHISPER_AVAILABLE:
        return await _speech_to_text(file_path)
    return ""


def _find_subtitle(video_path: str) -> Optional[str]:
    """查找与视频同名的字幕文件（.srt、.vtt）"""
    base, _ = os.path.splitext(video_path)
    for ext in (".srt", ".vtt"):
        sub = base + ext
        # if os.path.exists(sub):
        #     return sub
        try:
            minio_client.stat_object(settings.MINIO_BUCKET, sub)
            return sub
        except:
            continue
    return None


async def _parse_subtitle(sub_path: str) -> str:
    """解析字幕文件为纯文本"""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _sync_parse_subtitle, sub_path)


def _sync_parse_subtitle(path: str) -> str:
    if not PYSRT_AVAILABLE:
        # 简单按行读取，去时间戳（.srt 格式）
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        text = []
        for line in lines:
            line = line.strip()
            if line and not line[0].isdigit() and "-->" not in line:
                text.append(line)
        return " ".join(text)
    else:
        import pysrt
        subs = pysrt.open(path)
        return " ".join(sub.text for sub in subs)


async def _extract_audio_from_video(video_path: str) -> Optional[str]:
    """使用 ffmpeg 提取音频为临时 WAV 文件（需要系统安装 ffmpeg）"""
    try:
        import subprocess
        wav_path = video_path + ".wav"
        cmd = [
            "ffmpeg", "-i", video_path,
            "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
            wav_path, "-y"
        ]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            logger.error(f"ffmpeg 提取音频失败: {stderr.decode()}")
            return None
        return wav_path
    except FileNotFoundError:
        logger.error("系统未安装 ffmpeg，无法提取音频")
        return None


async def _speech_to_text(audio_path: str) -> str:
    """使用 OpenAI Whisper 进行语音识别（依赖 whisper 库）"""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _sync_transcribe, audio_path)


# def _sync_transcribe(audio_path: str) -> str:
#     import whisper
#     model = whisper.load_model("base")  # 可配置为 "small" 等
#     result = model.transcribe(audio_path, language="zh")
#     return result["text"]

_WHISPER_MODEL = None


# 防止whisper加载崩溃

def _get_model():
    global _WHISPER_MODEL
    if _WHISPER_MODEL is None:
        _WHISPER_MODEL = whisper.load_model("base")
    return _WHISPER_MODEL


def _sync_transcribe(audio_path: str) -> str:
    model = _get_model()
    return model.transcribe(audio_path, language="zh")
