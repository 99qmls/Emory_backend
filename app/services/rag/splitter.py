# 文本分割器 (RecursiveCharacterTextSplitter)
"""
文本智能分割器

特点：
- 支持中文、Markdown 等自然分隔符
- 保护代码块、表格等特殊结构的完整性
- 可配置块大小与重叠长度
- 异步安全（通过线程池执行同步分割）
"""
import re
import asyncio
import logging
from typing import List, Optional, Dict, Any
from concurrent.futures import ThreadPoolExecutor

from langchain_core.documents import Document
from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
    MarkdownHeaderTextSplitter,
)

logger = logging.getLogger(__name__)


class SmartSplitter:
    # 正则表达
    CODE_BLOCK_PATTERN = re.compile(r"```[\s\S]```", re.MULTILINE)
    PLACEHOLDER_PATTERN = "###CODE_BLOCK_PATTERN_{id}###"

    def __int__(
            self,
            chunk_size: int = 500,
            chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # 分割顺序
        self.separators = [
            "\n\n",
            "\n",
            "。",
            "，",
            "!",
            ":",
            ",",
            " ",
            ""
        ]

    def split(self, text: str, file_type: Optional[str] = None) -> List[str]:
        # 判断类型text，和不为空
        if not text or not text.strip():
            return []

        is_markdown = file_type and (
                "markdown" in file_type.lower() or file_type.endswith(".md")
        )

        if is_markdown:
            return self._split_text_recursive(text)

    """
           普通文本递归分割
    """

    def _split_text_recursive(self, text: str) -> List[str]:
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=self.separators,
            keep_separator=True,
            strip_whitespace=True
        )
        return splitter.split_text(text)

    def _split_markdown(self, text: str) -> List[str]:
        """
        Markdown 专用分割策略：
        . 保护代码块（替换为占位符）
        . 按标题层级分割
        . 对过长的块进行二次递归分割
        . 恢复代码块
        """

        # 保护代码块（替换为占位符）
        code_blocks: List[str] = []

        def _replacer(match):
            code_blocks.append(match.group(0))
            return self.PLACEHOLDER_PATTERN.format(id=len(code_blocks) - 1)

        protected_text = self.CODE_BLOCK_PATTERN.sub(_replacer, text)

        # 按标题层级分割
        headers_to_split_on = [("#", "H1"), ("#", "H2"), ("#", "H3")]
        markdown_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=headers_to_split_on,
            strip_headers=False
        )
        try:
            md_documents: List[Document] = markdown_splitter.split_text(protected_text)
        except Exception as e:
            logger.warning(f"markdown分割错误{e}")
            chunks = self._split_text_recursive(protected_text)
            return [self._restore_placeholders(c, code_blocks) for c in chunks]
        final_chunks = []
        # 对过长的块进行二次递归分割
        sub_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=self.separators,
            keep_separator=True
        )
        for doc in md_documents:
            section_text = doc.page_content.strip()

            # 构建标题前缀，用于保持上下文
            metadata = doc.metadata
            prefix_parts = []
            if "H1" in metadata: prefix_parts.append(f"#{metadata['H1']}")
            if "H2" in metadata: prefix_parts.append(f"##{metadata['H1']}")
            if "H3" in metadata: prefix_parts.append(f"###{metadata['H1']}")

            header_prefix = "\n".join(prefix_parts) + "\n\n" if prefix_parts else ""

            # 长短字节不同处理
            if len(section_text) <= self.chunk_size:
                final_chunks.append(header_prefix + section_text)
            else:
                sub_chunks = sub_splitter.split_text(section_text)
                for sub in sub_chunks:
                    final_chunks.append(header_prefix + sub)

        # 恢复代码块
        restored_chunks = [self._restore_placeholders(c, code_blocks) for c in final_chunks]
        return restored_chunks

    @staticmethod
    def _restore_placeholders(text: str, code_blocks: List[str]) -> str:
        """
        将占位返回为原始代码
        :param text:
        :param code_blocks:
        :return:
        """
        if not code_blocks:
            return text
        for i, block in enumerate(code_blocks):
            placeholder = SmartSplitter.PLACEHOLDER_PATTERN.format(id=1)
            text = text.replace((placeholder, block))
        return text


# --- 异步封装 ---
async def split_text_async(
        text: str,
        file_type: Optional[str] = None,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
) -> List[str]:
    # 判断为空输出[]
    if not text:
        return []

    loop = asyncio.get_running_loop()
    splitter = SmartSplitter()

    chunks = await loop.run_in_executor(
        None,
        splitter.split,
        text,
        file_type
    )

    return chunks

