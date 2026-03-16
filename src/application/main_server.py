from textwrap import dedent
from types import SimpleNamespace
from typing import TYPE_CHECKING

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from uvicorn import Config, Server

from ..custom import (
    __VERSION__,
    REPOSITORY,
    SERVER_HOST,
    SERVER_PORT,
    VERSION_BETA,
    is_valid_token,
)
from ..models import (
    Account,
    AccountTiktok,
    Comment,
    DataResponse,
    Detail,
    DetailTikTok,
    GeneralSearch,
    Live,
    LiveSearch,
    LiveTikTok,
    Mix,
    MixTikTok,
    Reply,
    Settings,
    ShortUrl,
    UrlResponse,
    UserSearch,
    VideoSearch,
)
from ..translation import _
from .main_terminal import TikTok

if TYPE_CHECKING:
    from ..config import Parameter
    from ..manager import Database

__all__ = ["APIServer"]


def token_dependency(token: str = Header(None)):
    if not is_valid_token(token):
        raise HTTPException(
            status_code=403,
            detail=_("验证失败！"),
        )


class APIServer(TikTok):
    def __init__(
        self,
        parameter: "Parameter",
        database: "Database",
        server_mode: bool = True,
    ):
        super().__init__(
            parameter,
            database,
            server_mode,
        )
        self.server = None

    async def handle_redirect(self, text: str, proxy: str = None) -> str:
        # 确保客户端始终可用
        await self.parameter.ensure_client()
        return await self.links.run(
            text,
            "",
            proxy,
        )

    async def handle_redirect_tiktok(self, text: str, proxy: str = None) -> str:
        # 确保客户端始终可用
        await self.parameter.ensure_client()
        return await self.links_tiktok.run(
            text,
            "",
            proxy,
        )

    async def run_server(
        self,
        host=SERVER_HOST,
        port=SERVER_PORT,
        log_level="info",
    ):
        self.server = FastAPI(
            debug=VERSION_BETA,
            title="DouK-Downloader",
            version=__VERSION__,
        )
        # 挂载静态文件目录
        from pathlib import Path
        static_dir = Path(__file__).parent.parent.parent / "static" / "web_ui"
        self.server.mount("/web", StaticFiles(directory=static_dir, html=True), name="web")
        self.setup_routes()
        config = Config(
            self.server,
            host=host,
            port=port,
            log_level=log_level,
        )
        server = Server(config)
        await server.serve()

    def setup_routes(self):
        @self.server.get(
            "/",
            summary=_("访问项目 GitHub 仓库"),
            description=_("重定向至项目 GitHub 仓库主页"),
            tags=[_("项目")],
        )
        async def index():
            return RedirectResponse(url=REPOSITORY)

        @self.server.get(
            "/token",
            summary=_("测试令牌有效性"),
            description=_(
                dedent("""
                项目默认无需令牌；公开部署时，建议设置令牌以防止恶意请求！
                
                令牌设置位置：`src/custom/function.py` - `is_valid_token()`
                """)
            ),
            tags=[_("项目")],
            response_model=DataResponse,
        )
        async def handle_test(token: str = Depends(token_dependency)):
            return DataResponse(
                message=_("验证成功！"),
                data=None,
                params=None,
            )

        @self.server.post(
            "/settings",
            summary=_("更新项目全局配置"),
            description=_(
                dedent("""
                更新项目配置文件 settings.json
                
                仅需传入需要更新的配置参数
                
                返回更新后的全部配置参数
                """)
            ),
            tags=[_("配置")],
            response_model=Settings,
        )
        async def handle_settings(
            extract: Settings, token: str = Depends(token_dependency)
        ):
            await self.parameter.set_settings_data(extract.model_dump())
            return Settings(**self.parameter.get_settings_data())

        @self.server.get(
            "/settings",
            summary=_("获取项目全局配置"),
            description=_("返回项目全部配置参数"),
            tags=[_("配置")],
            response_model=Settings,
        )
        async def get_settings(token: str = Depends(token_dependency)):
            return Settings(**self.parameter.get_settings_data())

        @self.server.post(
            "/douyin/share",
            summary=_("获取分享链接重定向的完整链接"),
            description=_(
                dedent("""
                **参数**:
                
                - **text**: 包含分享链接的字符串；必需参数
                - **proxy**: 代理；可选参数
                """)
            ),
            tags=[_("抖音")],
            response_model=UrlResponse,
        )
        async def handle_share(
            extract: ShortUrl, token: str = Depends(token_dependency)
        ):
            if url := await self.handle_redirect(extract.text, extract.proxy):
                return UrlResponse(
                    message=_("请求链接成功！"),
                    url=url,
                    params=extract.model_dump(),
                )
            return UrlResponse(
                message=_("请求链接失败！"),
                url=None,
                params=extract.model_dump(),
            )

        @self.server.post(
            "/douyin/detail",
            summary=_("获取单个作品数据"),
            description=_(
                dedent("""
                **参数**:
                
                - **cookie**: 抖音 Cookie；可选参数
                - **proxy**: 代理；可选参数
                - **source**: 是否返回原始响应数据；可选参数，默认值：False
                - **detail_id**: 抖音作品 ID；必需参数
                """)
            ),
            tags=[_("抖音")],
            response_model=DataResponse,
        )
        async def handle_detail(
            extract: Detail, token: str = Depends(token_dependency)
        ):
            # 如果请求中没有提供cookie，使用存储的cookie
            if not extract.cookie:
                settings_data = self.parameter.get_settings_data()
                extract.cookie = settings_data.get("cookie", None)
            return await self.handle_detail(extract, False)

        @self.server.post(
            "/douyin/account",
            summary=_("获取账号作品数据"),
            description=_(
                dedent("""
                **参数**:
                
                - **cookie**: 抖音 Cookie；可选参数
                - **proxy**: 代理；可选参数
                - **source**: 是否返回原始响应数据；可选参数，默认值：False
                - **sec_user_id**: 抖音账号 sec_uid；必需参数
                - **tab**: 账号页面类型；可选参数，默认值：`post`
                - **earliest**: 作品最早发布日期；可选参数
                - **latest**: 作品最晚发布日期；可选参数
                - **pages**: 最大请求次数，仅对请求账号喜欢页数据有效；可选参数
                - **cursor**: 可选参数
                - **count**: 可选参数
                """)
            ),
            tags=[_("抖音")],
            response_model=DataResponse,
        )
        async def handle_account(
            extract: Account, token: str = Depends(token_dependency)
        ):
            # 如果请求中没有提供cookie，使用存储的cookie
            if not extract.cookie:
                settings_data = self.parameter.get_settings_data()
                extract.cookie = settings_data.get("cookie", None)
            return await self.handle_account(extract, False)

        @self.server.post(
            "/douyin/mix",
            summary=_("获取合集作品数据"),
            description=_(
                dedent("""
                **参数**:
                
                - **cookie**: 抖音 Cookie；可选参数
                - **proxy**: 代理；可选参数
                - **source**: 是否返回原始响应数据；可选参数，默认值：False
                - **mix_id**: 抖音合集 ID
                - **detail_id**: 属于合集的抖音作品 ID
                - **cursor**: 可选参数
                - **count**: 可选参数
                
                **`mix_id` 和 `detail_id` 二选一，只需传入其中之一即可**
                """)
            ),
            tags=[_("抖音")],
            response_model=DataResponse,
        )
        async def handle_mix(extract: Mix, token: str = Depends(token_dependency)):
            # 如果请求中没有提供cookie，使用存储的cookie
            if not extract.cookie:
                settings_data = self.parameter.get_settings_data()
                extract.cookie = settings_data.get("cookie", None)
            is_mix, id_ = self.generate_mix_params(
                extract.mix_id,
                extract.detail_id,
            )
            if not isinstance(is_mix, bool):
                return DataResponse(
                    message=_("参数错误！"),
                    data=None,
                    params=extract.model_dump(),
                )
            if data := await self.deal_mix_detail(
                is_mix,
                id_,
                api=True,
                source=extract.source,
                cookie=extract.cookie,
                proxy=extract.proxy,
                cursor=extract.cursor,
                count=extract.count,
            ):
                return self.success_response(extract, data)
            return self.failed_response(extract)

        @self.server.post(
            "/douyin/live",
            summary=_("获取直播数据"),
            description=_(
                dedent("""
                **参数**:
                
                - **cookie**: 抖音 Cookie；可选参数
                - **proxy**: 代理；可选参数
                - **source**: 是否返回原始响应数据；可选参数，默认值：False
                - **web_rid**: 抖音直播 web_rid
                """)
            ),
            tags=[_("抖音")],
            response_model=DataResponse,
        )
        async def handle_live(extract: Live, token: str = Depends(token_dependency)):
            # 如果请求中没有提供cookie，使用存储的cookie
            if not extract.cookie:
                settings_data = self.parameter.get_settings_data()
                extract.cookie = settings_data.get("cookie", None)
            # if self.check_live_params(
            #     extract.web_rid,
            #     extract.room_id,
            #     extract.sec_user_id,
            # ):
            #     if data := await self.handle_live(
            #         extract,
            #     ):
            #         return self.success_response(extract, data[0])
            #     return self.failed_response(extract)
            # return DataResponse(
            #     message=_("参数错误！"),
            #     data=None,
            #     params=extract.model_dump(),
            # )
            if data := await self.handle_live(
                extract,
            ):
                return self.success_response(extract, data[0])
            return self.failed_response(extract)

        @self.server.post(
            "/douyin/comment",
            summary=_("获取作品评论数据"),
            description=_(
                dedent("""
                **参数**:
                
                - **cookie**: 抖音 Cookie；可选参数
                - **proxy**: 代理；可选参数
                - **source**: 是否返回原始响应数据；可选参数，默认值：False
                - **detail_id**: 抖音作品 ID；必需参数
                - **pages**: 最大请求次数；可选参数
                - **cursor**: 可选参数
                - **count**: 可选参数
                - **count_reply**: 可选参数
                - **reply**: 可选参数，默认值：False
                """)
            ),
            tags=[_("抖音")],
            response_model=DataResponse,
        )
        async def handle_comment(
            extract: Comment, token: str = Depends(token_dependency)
        ):
            # 如果请求中没有提供cookie，使用存储的cookie
            if not extract.cookie:
                settings_data = self.parameter.get_settings_data()
                extract.cookie = settings_data.get("cookie", None)
            if data := await self.comment_handle_single(
                extract.detail_id,
                cookie=extract.cookie,
                proxy=extract.proxy,
                source=extract.source,
                pages=extract.pages,
                cursor=extract.cursor,
                count=extract.count,
                count_reply=extract.count_reply,
                reply=extract.reply,
            ):
                return self.success_response(extract, data)
            return self.failed_response(extract)

        @self.server.post(
            "/douyin/reply",
            summary=_("获取评论回复数据"),
            description=_(
                dedent("""
                **参数**:
                
                - **cookie**: 抖音 Cookie；可选参数
                - **proxy**: 代理；可选参数
                - **source**: 是否返回原始响应数据；可选参数，默认值：False
                - **detail_id**: 抖音作品 ID；必需参数
                - **comment_id**: 评论 ID；必需参数
                - **pages**: 最大请求次数；可选参数
                - **cursor**: 可选参数
                - **count**: 可选参数
                """)
            ),
            tags=[_("抖音")],
            response_model=DataResponse,
        )
        async def handle_reply(extract: Reply, token: str = Depends(token_dependency)):
            # 如果请求中没有提供cookie，使用存储的cookie
            if not extract.cookie:
                settings_data = self.parameter.get_settings_data()
                extract.cookie = settings_data.get("cookie", None)
            if data := await self.reply_handle(
                extract.detail_id,
                extract.comment_id,
                cookie=extract.cookie,
                proxy=extract.proxy,
                pages=extract.pages,
                cursor=extract.cursor,
                count=extract.count,
                source=extract.source,
            ):
                return self.success_response(extract, data)
            return self.failed_response(extract)

        @self.server.post(
            "/douyin/search/general",
            summary=_("获取综合搜索数据"),
            description=_(
                dedent("""
                **参数**:
                
                - **cookie**: 抖音 Cookie；可选参数
                - **proxy**: 代理；可选参数
                - **source**: 是否返回原始响应数据；可选参数，默认值：False
                - **keyword**: 关键词；必需参数
                - **offset**: 起始页码；可选参数
                - **count**: 数据数量；可选参数
                - **pages**: 总页数；可选参数
                - **sort_type**: 排序依据；可选参数
                - **publish_time**: 发布时间；可选参数
                - **duration**: 视频时长；可选参数
                - **search_range**: 搜索范围；可选参数
                - **content_type**: 内容形式；可选参数
                
                **部分参数传入规则请查阅文档**: [参数含义](https://github.com/JoeanAmier/TikTokDownloader/wiki/Documentation#%E9%87%87%E9%9B%86%E6%90%9C%E7%B4%A2%E7%BB%93%E6%9E%9C%E6%95%B0%E6%8D%AE%E6%8A%96%E9%9F%B3)
                """)
            ),
            tags=[_("抖音")],
            response_model=DataResponse,
        )
        async def handle_search_general(
            extract: GeneralSearch, token: str = Depends(token_dependency)
        ):
            # 如果请求中没有提供cookie，使用存储的cookie
            if not extract.cookie:
                settings_data = self.parameter.get_settings_data()
                extract.cookie = settings_data.get("cookie", None)
            return await self.handle_search(extract)

        @self.server.post(
            "/douyin/search/video",
            summary=_("获取视频搜索数据"),
            description=_(
                dedent("""
                **参数**:
                
                - **cookie**: 抖音 Cookie；可选参数
                - **proxy**: 代理；可选参数
                - **source**: 是否返回原始响应数据；可选参数，默认值：False
                - **keyword**: 关键词；必需参数
                - **offset**: 起始页码；可选参数
                - **count**: 数据数量；可选参数
                - **pages**: 总页数；可选参数
                - **sort_type**: 排序依据；可选参数
                - **publish_time**: 发布时间；可选参数
                - **duration**: 视频时长；可选参数
                - **search_range**: 搜索范围；可选参数
                
                **部分参数传入规则请查阅文档**: [参数含义](https://github.com/JoeanAmier/TikTokDownloader/wiki/Documentation#%E9%87%87%E9%9B%86%E6%90%9C%E7%B4%A2%E7%BB%93%E6%9E%9C%E6%95%B0%E6%8D%AE%E6%8A%96%E9%9F%B3)
                """)
            ),
            tags=[_("抖音")],
            response_model=DataResponse,
        )
        async def handle_search_video(
            extract: VideoSearch, token: str = Depends(token_dependency)
        ):
            # 如果请求中没有提供cookie，使用存储的cookie
            if not extract.cookie:
                settings_data = self.parameter.get_settings_data()
                extract.cookie = settings_data.get("cookie", None)
            return await self.handle_search(extract)

        @self.server.post(
            "/douyin/search/user",
            summary=_("获取用户搜索数据"),
            description=_(
                dedent("""
                **参数**:
                
                - **cookie**: 抖音 Cookie；可选参数
                - **proxy**: 代理；可选参数
                - **source**: 是否返回原始响应数据；可选参数，默认值：False
                - **keyword**: 关键词；必需参数
                - **offset**: 起始页码；可选参数
                - **count**: 数据数量；可选参数
                - **pages**: 总页数；可选参数
                - **douyin_user_fans**: 粉丝数量；可选参数
                - **douyin_user_type**: 用户类型；可选参数
                
                **部分参数传入规则请查阅文档**: [参数含义](https://github.com/JoeanAmier/TikTokDownloader/wiki/Documentation#%E9%87%87%E9%9B%86%E6%90%9C%E7%B4%A2%E7%BB%93%E6%9E%9C%E6%95%B0%E6%8D%AE%E6%8A%96%E9%9F%B3)
                """)
            ),
            tags=[_("抖音")],
            response_model=DataResponse,
        )
        async def handle_search_user(
            extract: UserSearch, token: str = Depends(token_dependency)
        ):
            # 如果请求中没有提供cookie，使用存储的cookie
            if not extract.cookie:
                settings_data = self.parameter.get_settings_data()
                extract.cookie = settings_data.get("cookie", None)
            return await self.handle_search(extract)

        @self.server.post(
            "/douyin/search/live",
            summary=_("获取直播搜索数据"),
            description=_(
                dedent("""
                **参数**:
                
                - **cookie**: 抖音 Cookie；可选参数
                - **proxy**: 代理；可选参数
                - **source**: 是否返回原始响应数据；可选参数，默认值：False
                - **keyword**: 关键词；必需参数
                - **offset**: 起始页码；可选参数
                - **count**: 数据数量；可选参数
                - **pages**: 总页数；可选参数
                """)
            ),
            tags=[_("抖音")],
            response_model=DataResponse,
        )
        async def handle_search_live(
            extract: LiveSearch, token: str = Depends(token_dependency)
        ):
            # 如果请求中没有提供cookie，使用存储的cookie
            if not extract.cookie:
                settings_data = self.parameter.get_settings_data()
                extract.cookie = settings_data.get("cookie", None)
            return await self.handle_search(extract)

        @self.server.post(
            "/tiktok/share",
            summary=_("获取分享链接重定向的完整链接"),
            description=_(
                dedent("""
            **参数**:

            - **text**: 包含分享链接的字符串；必需参数
            - **proxy**: 代理；可选参数
            """)
            ),
            tags=["TikTok"],
            response_model=UrlResponse,
        )
        async def handle_share_tiktok(
            extract: ShortUrl, token: str = Depends(token_dependency)
        ):
            if url := await self.handle_redirect_tiktok(extract.text, extract.proxy):
                return UrlResponse(
                    message=_("请求链接成功！"),
                    url=url,
                    params=extract.model_dump(),
                )
            return UrlResponse(
                message=_("请求链接失败！"),
                url=None,
                params=extract.model_dump(),
            )

        @self.server.post(
            "/tiktok/detail",
            summary=_("获取单个作品数据"),
            description=_(
                dedent("""
                **参数**:

                - **cookie**: TikTok Cookie；可选参数
                - **proxy**: 代理；可选参数
                - **source**: 是否返回原始响应数据；可选参数，默认值：False
                - **detail_id**: TikTok 作品 ID；必需参数
                """)
            ),
            tags=["TikTok"],
            response_model=DataResponse,
        )
        async def handle_detail_tiktok(
            extract: DetailTikTok, token: str = Depends(token_dependency)
        ):
            # 如果请求中没有提供cookie，使用存储的cookie
            if not extract.cookie:
                settings_data = self.parameter.get_settings_data()
                extract.cookie = settings_data.get("cookie_tiktok", None)
            return await self.handle_detail(extract, True)

        @self.server.post(
            "/tiktok/account",
            summary=_("获取账号作品数据"),
            description=_(
                dedent("""
                **参数**:

                - **cookie**: TikTok Cookie；可选参数
                - **proxy**: 代理；可选参数
                - **source**: 是否返回原始响应数据；可选参数，默认值：False
                - **sec_user_id**: TikTok 账号 secUid；必需参数
                - **tab**: 账号页面类型；可选参数，默认值：`post`
                - **earliest**: 作品最早发布日期；可选参数
                - **latest**: 作品最晚发布日期；可选参数
                - **pages**: 最大请求次数，仅对请求账号喜欢页数据有效；可选参数
                - **cursor**: 可选参数
                - **count**: 可选参数
                """)
            ),
            tags=["TikTok"],
            response_model=DataResponse,
        )
        async def handle_account_tiktok(
            extract: AccountTiktok, token: str = Depends(token_dependency)
        ):
            # 如果请求中没有提供cookie，使用存储的cookie
            if not extract.cookie:
                settings_data = self.parameter.get_settings_data()
                extract.cookie = settings_data.get("cookie_tiktok", None)
            return await self.handle_account(extract, True)

        @self.server.post(
            "/tiktok/mix",
            summary=_("获取合辑作品数据"),
            description=_(
                dedent("""
                **参数**:

                - **cookie**: TikTok Cookie；可选参数
                - **proxy**: 代理；可选参数
                - **source**: 是否返回原始响应数据；可选参数，默认值：False
                - **mix_id**: TikTok 合集 ID；必需参数
                - **cursor**: 可选参数
                - **count**: 可选参数
                """)
            ),
            tags=["TikTok"],
            response_model=DataResponse,
        )
        async def handle_mix_tiktok(
            extract: MixTikTok, token: str = Depends(token_dependency)
        ):
            # 如果请求中没有提供cookie，使用存储的cookie
            if not extract.cookie:
                settings_data = self.parameter.get_settings_data()
                extract.cookie = settings_data.get("cookie_tiktok", None)
            if data := await self.deal_mix_detail(
                True,
                extract.mix_id,
                api=True,
                source=extract.source,
                cookie=extract.cookie,
                proxy=extract.proxy,
                cursor=extract.cursor,
                count=extract.count,
            ):
                return self.success_response(extract, data)
            return self.failed_response(extract)

        @self.server.post(
            "/tiktok/live",
            summary=_("获取直播数据"),
            description=_(
                dedent("""
                **参数**:

                - **cookie**: TikTok Cookie；可选参数
                - **proxy**: 代理；可选参数
                - **source**: 是否返回原始响应数据；可选参数，默认值：False
                - **room_id**: TikTok 直播 room_id；必需参数
                """)
            ),
            tags=["TikTok"],
            response_model=DataResponse,
        )
        async def handle_live_tiktok(
            extract: Live, token: str = Depends(token_dependency)
        ):
            # 如果请求中没有提供cookie，使用存储的cookie
            if not extract.cookie:
                settings_data = self.parameter.get_settings_data()
                extract.cookie = settings_data.get("cookie_tiktok", None)
            if data := await self.handle_live(
                extract,
                True,
            ):
                return self.success_response(extract, data[0])
            return self.failed_response(extract)

        @self.server.post(
            "/download",
            summary=_('下载作品'),
            description=_('''**参数**:

                - **link**: 抖音或 TikTok 链接，支持多条链接（换行分隔）；必需参数
                - **platform**: 平台，可选值：douyin, tiktok；必需参数
                - **proxy**: 代理；可选参数
                '''),
            tags=[_('下载')],
            response_model=DataResponse,
        )
        async def handle_download(
            request: dict, token: str = Depends(token_dependency)
        ):
            link = request.get('link')
            platform = request.get('platform')
            proxy = request.get('proxy')
            try:
                # 处理多条链接（按换行分隔）
                links = link.split('\n')
                detail_ids = []
                
                for link_item in links:
                    link_item = link_item.strip()
                    if not link_item:
                        continue
                    
                    # 处理链接
                    if platform == "douyin":
                        if not (url := await self.handle_redirect(link_item, proxy)):
                            return DataResponse(
                                message=_('链接解析失败！'),
                                data=None,
                                params={"link": link, "platform": platform, "proxy": proxy},
                            )
                        # 提取作品ID
                        import re
                        match = re.search(r"video/(\d+)", url)
                        if not match:
                            # 尝试匹配图片合集链接（抖音）
                            match = re.search(r"note/(\d+)", url)
                            if not match:
                                # 尝试匹配图片合集链接（TikTok）
                                match = re.search(r"photo/(\d+)", url)
                                if not match:
                                    # 尝试匹配其他可能的链接格式
                                    match = re.search(r"aweme/(\d+)", url)
                                    if not match:
                                        return DataResponse(
                                            message=_('无法从链接中提取作品ID！'),
                                            data=None,
                                            params={"link": link, "platform": platform, "proxy": proxy},
                                        )
                        detail_id = match.group(1)
                        detail_ids.append(detail_id)
                    elif platform == "tiktok":
                        if not (url := await self.handle_redirect_tiktok(link_item, proxy)):
                            return DataResponse(
                                message=_('链接解析失败！'),
                                data=None,
                                params={"link": link, "platform": platform, "proxy": proxy},
                            )
                        # 提取作品ID
                        import re
                        match = re.search(r"video/(\d+)", url)
                        if not match:
                            # 尝试匹配图片合集链接（抖音）
                            match = re.search(r"note/(\d+)", url)
                            if not match:
                                # 尝试匹配图片合集链接（TikTok）
                                match = re.search(r"photo/(\d+)", url)
                                if not match:
                                    # 尝试匹配其他可能的链接格式
                                    match = re.search(r"aweme/(\d+)", url)
                                    if not match:
                                        return DataResponse(
                                            message=_('无法从链接中提取作品ID！'),
                                            data=None,
                                            params={"link": link, "platform": platform, "proxy": proxy},
                                        )
                        detail_id = match.group(1)
                        detail_ids.append(detail_id)
                    else:
                        return DataResponse(
                            message=_('平台参数错误！'),
                            data=None,
                            params={"link": link, "platform": platform, "proxy": proxy},
                        )
                
                if not detail_ids:
                    return DataResponse(
                        message=_('未找到有效的作品ID！'),
                        data=None,
                        params={"link": link, "platform": platform, "proxy": proxy},
                    )
                
                # 下载作品
                # 从配置文件中获取cookie
                settings_data = self.parameter.get_settings_data()
                cookie = settings_data.get("cookie_tiktok" if platform == "tiktok" else "cookie", None)
                # 确保cookie是字符串类型
                from ..tools import cookie_dict_to_str
                if isinstance(cookie, dict):
                    cookie = cookie_dict_to_str(cookie)
                elif cookie is None:
                    cookie = ""
                
                root, params, logger = self.record.run(self.parameter)
                async with logger(root, console=self.console, **params) as record:
                    if data := await self._handle_detail(
                        detail_ids,
                        platform == "tiktok",
                        record,
                        False,
                        False,
                        cookie,
                        proxy,
                    ):
                        return DataResponse(
                            message=_('下载成功！'),
                            data={"save_path": str(root)},
                            params={"link": link, "platform": platform, "proxy": proxy},
                        )
            except Exception as e:
                return DataResponse(
                    message=_('下载失败：{error}').format(error=str(e)),
                    data=None,
                    params={"link": link, "platform": platform, "proxy": proxy},
                )
            return DataResponse(
                message=_('下载失败！'),
                data=None,
                params={"link": link, "platform": platform, "proxy": proxy},
            )

        @self.server.post(
            "/get-cookie",
            summary=_('从浏览器获取Cookie'),
            description=_("""**参数**:

                - **platform**: 平台，可选值：douyin, tiktok；必需参数
                - **browser**: 浏览器名称；必需参数
                """),
            tags=[_('Cookie')],
            response_model=DataResponse,
        )
        async def handle_get_cookie(
            request: dict, token: str = Depends(token_dependency)
        ):
            platform = request.get('platform')
            browser = request.get('browser')
            try:
                # 导入必要的模块
                from ..module import Cookie
                from ..tools import Browser
                
                # 初始化Cookie和Browser对象
                cookie_object = Cookie(self.parameter.settings, self.console)
                browser_object = Browser(self.parameter, cookie_object)
                
                # 确定是否为TikTok平台
                tiktok = platform == "tiktok"
                
                # 从浏览器获取Cookie
                cookie = browser_object.get(browser, browser_object.PLATFORM[tiktok].domain)
                
                if cookie:
                    # 保存Cookie到配置文件
                    browser_object._Browser__save_cookie(cookie, tiktok)
                    # 更新内存中的Cookie
                    settings_data = self.parameter.get_settings_data()
                    if tiktok:
                        self.parameter.set_cookie(settings_data.get("cookie", None), cookie)
                    else:
                        self.parameter.set_cookie(cookie, settings_data.get("cookie_tiktok", None))
                    return DataResponse(
                        message=_('Cookie获取成功！'),
                        data=None,
                        params={"platform": platform, "browser": browser},
                    )
                else:
                    return DataResponse(
                        message=_('Cookie获取失败：未找到对应的Cookie数据'),
                        data=None,
                        params={"platform": platform, "browser": browser},
                    )
            except Exception as e:
                return DataResponse(
                    message=_('Cookie获取失败：{error}').format(error=str(e)),
                    data=None,
                    params={"platform": platform, "browser": browser},
                )

        @self.server.post(
            "/delete-cookie",
            summary=_('删除服务器上保存的Cookie'),
            description=_('''**参数**:

                - **platform**: 平台，可选值：douyin, tiktok；必需参数
                '''),
            tags=[_('Cookie')],
            response_model=DataResponse,
        )
        async def handle_delete_cookie(
            request: dict, token: str = Depends(token_dependency)
        ):
            platform = request.get('platform')
            try:
                # 确定是否为TikTok平台
                tiktok = platform == "tiktok"
                
                # 从配置文件中删除Cookie
                settings_data = self.parameter.get_settings_data()
                if tiktok:
                    # 删除TikTok Cookie
                    settings_data.pop("cookie_tiktok", None)
                    settings_data.pop("browser_info_tiktok", None)
                else:
                    # 删除抖音 Cookie
                    settings_data.pop("cookie", None)
                    settings_data.pop("browser_info", None)
                
                # 保存到配置文件
                await self.parameter.set_settings_data(settings_data)
                # 更新内存中的Cookie
                self.parameter.set_cookie(settings_data.get("cookie", None), settings_data.get("cookie_tiktok", None))
                
                return DataResponse(
                    message=_('Cookie删除成功！'),
                    data=None,
                    params={"platform": platform},
                )
            except Exception as e:
                return DataResponse(
                    message=_('Cookie删除失败：{error}').format(error=str(e)),
                    data=None,
                    params={"platform": platform},
                )

        @self.server.get(
            "/accounts",
            summary=_('获取账号列表'),
            description=_('获取所有已保存的抖音和TikTok账号'),
            tags=[_('账号管理')],
            response_model=DataResponse,
        )
        async def get_accounts(token: str = Depends(token_dependency)):
            try:
                # 从配置文件读取账号信息
                accounts = self.parameter.accounts_urls
                accounts_tiktok = self.parameter.accounts_urls_tiktok
                
                # 转换为前端需要的格式
                account_list = []
                for account in accounts:
                    if account.enable:
                        account_list.append({
                            "id": account.url,  # 使用url作为唯一标识
                            "platform": "douyin",
                            "username": account.mark,
                            "sec_user_id": account.url
                        })
                
                for account in accounts_tiktok:
                    if account.enable:
                        account_list.append({
                            "id": account.url,  # 使用url作为唯一标识
                            "platform": "tiktok",
                            "username": account.mark,
                            "sec_user_id": account.url
                        })
                
                return DataResponse(
                    message=_('获取账号列表成功！'),
                    data=account_list,
                    params=None,
                )
            except Exception as e:
                return DataResponse(
                    message=_('获取账号列表失败：{error}').format(error=str(e)),
                    data=None,
                    params=None,
                )

        @self.server.post(
            "/accounts",
            summary=_('添加账号'),
            description=_("""**参数**:

                - **platform**: 平台，可选值：douyin, tiktok；必需参数
                - **username**: 账号名称；必需参数
                - **sec_user_id**: 账号Sec User ID；必需参数
                """),
            tags=[_('账号管理')],
            response_model=DataResponse,
        )
        async def add_account(
            request: dict, token: str = Depends(token_dependency)
        ):
            platform = request.get('platform')
            username = request.get('username')
            sec_user_id = request.get('sec_user_id')
            
            try:
                # 验证Sec User ID或链接
                if platform == "douyin":
                    # 验证抖音Sec User ID或链接
                    if not sec_user_id:
                        return DataResponse(
                            message=_('Sec User ID或链接不能为空！'),
                            data=None,
                            params=request,
                        )
                    
                    # 从链接中提取Sec User ID
                    import re
                    match = re.search(r"user/([^/]+)", sec_user_id)
                    if match:
                        sec_user_id = match.group(1)
                    # 去除可能的查询参数
                    sec_user_id = sec_user_id.split('?')[0]
                    
                    # 检查是否已存在
                    for account in self.parameter.accounts_urls:
                        if account.url == sec_user_id:
                            return DataResponse(
                                message=_('账号已存在！'),
                                data=None,
                                params=request,
                            )
                    
                    # 尝试获取用户信息
                    try:
                        from ..interface import User
                        from ..tools import cookie_dict_to_str
                        # 使用最新的cookie
                        settings_data = self.parameter.get_settings_data()
                        cookie = settings_data.get("cookie_tiktok" if platform == "tiktok" else "cookie", None)
                        # 确保cookie是字符串类型
                        if isinstance(cookie, dict):
                            cookie = cookie_dict_to_str(cookie)
                        elif cookie is None:
                            cookie = ""
                        user_data = await User(self.parameter, cookie, None, sec_user_id).run()
                        if user_data and user_data.get('nickname'):
                            username = user_data['nickname']
                        else:
                            return DataResponse(
                                message=_('获取用户信息失败：未找到用户昵称！'),
                                data=None,
                                params=request,
                            )
                    except Exception as e:
                        # 获取用户信息失败，返回错误信息
                        self.logger.warning(f"获取用户信息失败: {str(e)}")
                        return DataResponse(
                            message=_('获取用户信息失败：{error}').format(error=str(e)),
                            data=None,
                            params=request,
                        )
                    
                    # 添加到抖音账号列表
                    new_account = SimpleNamespace(
                        mark=username,
                        url=sec_user_id,
                        tab="",
                        earliest="",
                        latest="",
                        enable=True
                    )
                    self.parameter.accounts_urls.append(new_account)
                elif platform == "tiktok":
                    # 验证TikTok Sec User ID或链接
                    if not sec_user_id:
                        return DataResponse(
                            message=_('Sec User ID或链接不能为空！'),
                            data=None,
                            params=request,
                        )
                    
                    # 从链接中提取Sec User ID
                    import re
                    match = re.search(r"@([^/?]+)", sec_user_id)
                    if match:
                        sec_user_id = match.group(1)
                    
                    # 检查是否已存在
                    for account in self.parameter.accounts_urls_tiktok:
                        if account.url == sec_user_id:
                            return DataResponse(
                                message=_('账号已存在！'),
                                data=None,
                                params=request,
                            )
                    
                    # 尝试获取用户信息
                    try:
                        from ..interface import User
                        from ..tools import cookie_dict_to_str
                        # 使用最新的cookie
                        settings_data = self.parameter.get_settings_data()
                        cookie = settings_data.get("cookie_tiktok" if platform == "tiktok" else "cookie", None)
                        # 确保cookie是字符串类型
                        if isinstance(cookie, dict):
                            cookie = cookie_dict_to_str(cookie)
                        elif cookie is None:
                            cookie = ""
                        user_data = await User(self.parameter, cookie, None, sec_user_id).run()
                        if user_data and user_data.get('nickname'):
                            username = user_data['nickname']
                        else:
                            return DataResponse(
                                message=_('获取用户信息失败：未找到用户昵称！'),
                                data=None,
                                params=request,
                            )
                    except Exception as e:
                        # 获取用户信息失败，返回错误信息
                        self.logger.warning(f"获取用户信息失败: {str(e)}")
                        return DataResponse(
                            message=_('获取用户信息失败：{error}').format(error=str(e)),
                            data=None,
                            params=request,
                        )
                    
                    # 添加到TikTok账号列表
                    new_account = SimpleNamespace(
                        mark=username,
                        url=sec_user_id,
                        tab="",
                        earliest="",
                        latest="",
                        enable=True
                    )
                    self.parameter.accounts_urls_tiktok.append(new_account)
                else:
                    return DataResponse(
                        message=_('平台参数错误！'),
                        data=None,
                        params=request,
                    )
                
                # 保存到配置文件
                settings_data = self.parameter.get_settings_data()
                settings_data["accounts_urls"] = [vars(a) for a in self.parameter.accounts_urls]
                settings_data["accounts_urls_tiktok"] = [vars(a) for a in self.parameter.accounts_urls_tiktok]
                await self.parameter.set_settings_data(settings_data)
                
                return DataResponse(
                    message=_('添加账号成功！'),
                    data={
                        "id": sec_user_id,
                        "platform": platform,
                        "username": username,
                        "sec_user_id": sec_user_id
                    },
                    params=request,
                )
            except Exception as e:
                return DataResponse(
                    message=_('添加账号失败：{error}').format(error=str(e)),
                    data=None,
                    params=request,
                )

        @self.server.put(
            "/accounts/{account_id}",
            summary=_('编辑账号'),
            description=_("""**参数**:

                - **account_id**: 账号ID；必需参数
                - **username**: 账号名称；必需参数
                - **sec_user_id**: 账号Sec User ID；必需参数
                """),
            tags=[_('账号管理')],
            response_model=DataResponse,
        )
        async def edit_account(
            account_id: str, request: dict, token: str = Depends(token_dependency)
        ):
            username = request.get('username')
            sec_user_id = request.get('sec_user_id')
            
            try:
                # 查找并编辑账号
                updated = False
                for account in self.parameter.accounts_urls:
                    if account.url == account_id:
                        account.mark = username
                        account.url = sec_user_id
                        updated = True
                        break
                
                if not updated:
                    for account in self.parameter.accounts_urls_tiktok:
                        if account.url == account_id:
                            account.mark = username
                            account.url = sec_user_id
                            updated = True
                            break
                
                if not updated:
                    return DataResponse(
                        message=_('账号不存在！'),
                        data=None,
                        params=request,
                    )
                
                # 保存到配置文件
                settings_data = self.parameter.get_settings_data()
                settings_data["accounts_urls"] = [vars(a) for a in self.parameter.accounts_urls]
                settings_data["accounts_urls_tiktok"] = [vars(a) for a in self.parameter.accounts_urls_tiktok]
                await self.parameter.set_settings_data(settings_data)
                
                return DataResponse(
                    message=_('编辑账号成功！'),
                    data={
                        "id": sec_user_id,
                        "username": username,
                        "sec_user_id": sec_user_id
                    },
                    params=request,
                )
            except Exception as e:
                return DataResponse(
                    message=_('编辑账号失败：{error}').format(error=str(e)),
                    data=None,
                    params=request,
                )

        @self.server.delete(
            "/accounts/{account_id}",
            summary=_('删除账号'),
            description=_('根据账号ID删除账号'),
            tags=[_('账号管理')],
            response_model=DataResponse,
        )
        async def delete_account(
            account_id: str, token: str = Depends(token_dependency)
        ):
            try:
                # 查找并删除账号
                deleted = False
                for i, account in enumerate(self.parameter.accounts_urls):
                    if account.url == account_id:
                        self.parameter.accounts_urls.pop(i)
                        deleted = True
                        break
                
                if not deleted:
                    for i, account in enumerate(self.parameter.accounts_urls_tiktok):
                        if account.url == account_id:
                            self.parameter.accounts_urls_tiktok.pop(i)
                            deleted = True
                            break
                
                if not deleted:
                    return DataResponse(
                        message=_('账号不存在！'),
                        data=None,
                        params={"account_id": account_id},
                    )
                
                # 保存到配置文件
                settings_data = self.parameter.get_settings_data()
                settings_data["accounts_urls"] = [vars(a) for a in self.parameter.accounts_urls]
                settings_data["accounts_urls_tiktok"] = [vars(a) for a in self.parameter.accounts_urls_tiktok]
                await self.parameter.set_settings_data(settings_data)
                
                return DataResponse(
                    message=_('删除账号成功！'),
                    data=None,
                    params={"account_id": account_id},
                )
            except Exception as e:
                return DataResponse(
                    message=_('删除账号失败：{error}').format(error=str(e)),
                    data=None,
                    params={"account_id": account_id},
                )

        @self.server.post(
            "/accounts/{account_id}/download",
            summary=_('批量下载账号作品'),
            description=_("""**参数**:

                - **account_id**: 账号ID；必需参数
                - **tab**: 作品类型，可选值：post, favorite, collection；默认值：post
                """),
            tags=[_('账号管理')],
            response_model=DataResponse,
        )
        async def download_account_works(
            account_id: str, request: dict, token: str = Depends(token_dependency)
        ):
            tab = request.get('tab', 'post')
            
            try:
                # 查找账号
                account = None
                tiktok = False
                for acc in self.parameter.accounts_urls:
                    if acc.url == account_id:
                        account = acc
                        break
                
                if not account:
                    for acc in self.parameter.accounts_urls_tiktok:
                        if acc.url == account_id:
                            account = acc
                            tiktok = True
                            break
                
                if not account:
                    return DataResponse(
                        message=_('账号不存在！'),
                        data=None,
                        params={"account_id": account_id},
                    )
                
                # 先获取账号作品数据以获取真实的视频总数
                # 从配置文件中获取cookie
                settings_data = self.parameter.get_settings_data()
                cookie = settings_data.get("cookie_tiktok" if tiktok else "cookie", None)
                # 确保cookie是字符串类型
                from ..tools import cookie_dict_to_str
                if isinstance(cookie, dict):
                    cookie = cookie_dict_to_str(cookie)
                elif cookie is None:
                    cookie = ""
                
                acquirer = self._get_account_data_tiktok if tiktok else self._get_account_data
                account_data, earliest, latest = await acquirer(
                    cookie=cookie,
                    sec_user_id=account.url,
                    tab=tab
                )
                
                # 计算真实的视频总数
                total_videos = len(account_data)
                
                # 批量下载账号作品
                # 从配置文件中获取cookie
                settings_data = self.parameter.get_settings_data()
                cookie = settings_data.get("cookie_tiktok" if tiktok else "cookie", None)
                # 确保cookie是字符串类型
                from ..tools import cookie_dict_to_str
                if isinstance(cookie, dict):
                    cookie = cookie_dict_to_str(cookie)
                elif cookie is None:
                    cookie = ""
                
                root, params, logger = self.record.run(self.parameter)
                async with logger(root, console=self.console, **params) as record:
                    if await self.deal_account_detail(
                        1,  # index
                        account.url,  # sec_user_id
                        tab=tab,
                        mark=account.mark,
                        api=False,
                        cookie=cookie,
                        tiktok=tiktok
                    ):
                        return DataResponse(
                            message=_('批量下载账号作品成功！'),
                            data={"save_path": str(root), "total_videos": total_videos},
                            params={"account_id": account_id, "tab": tab},
                        )
                    else:
                        return DataResponse(
                            message=_('批量下载账号作品失败！'),
                            data=None,
                            params={"account_id": account_id, "tab": tab},
                        )
            except Exception as e:
                return DataResponse(
                    message=_('批量下载账号作品失败：{error}').format(error=str(e)),
                    data=None,
                    params={"account_id": account_id, "tab": tab},
                )

        