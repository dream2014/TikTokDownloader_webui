from asyncio import CancelledError
from asyncio import run
import sys

from src.application import TikTokDownloader


async def main():
    async with TikTokDownloader() as downloader:
        try:
            # 检查是否有命令行参数
            if len(sys.argv) > 1 and sys.argv[1] == "--web-ui":
                # 直接启动 Web UI 模式
                await downloader.web_ui()
            else:
                # 正常运行
                await downloader.run()
        except (
                KeyboardInterrupt,
                CancelledError,
        ):
            return


if __name__ == "__main__":
    run(main())
