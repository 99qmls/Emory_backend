import logging
from typing import Optional

from mcp import ClientSession
from mcp.client.sse import sse_client

logger = logging.getLogger(__name__)


class MCPBaseClient:

    def __init__(self, url: str):

        self.url = url

        self._streams = None

        self._session: Optional[
            ClientSession
        ] = None

        self._initialized = False

    @property
    def initialized(self):

        return self._initialized

    async def initialize(self):

        if self._initialized:
            return

        logger.info(
            "连接 MCP Server: %s",
            self.url
        )

        self._streams = sse_client(
            self.url
        )

        read_stream, write_stream = (
            await self._streams.__aenter__()
        )

        self._session = ClientSession(
            read_stream,
            write_stream
        )

        await self._session.__aenter__()

        await self._session.initialize()

        tools = await (
            self._session.list_tools()
        )

        logger.info(
            "MCP工具列表: %s",
            [t.name for t in tools.tools]
        )

        self._initialized = True

    async def call_tool(
        self,
        tool_name: str,
        arguments: dict
    ) -> str:

        if not self._initialized:
            raise RuntimeError(
                "MCP Client 未初始化"
            )

        result = await (
            self._session.call_tool(
                tool_name,
                arguments
            )
        )

        texts = []

        for item in result.content:

            if hasattr(item, "text"):
                texts.append(item.text)

        return "\n".join(texts)

    async def close(self):

        try:

            if self._session:

                await self._session.__aexit__(
                    None,
                    None,
                    None
                )

        finally:

            if self._streams:

                await self._streams.__aexit__(
                    None,
                    None,
                    None
                )

        self._initialized = False