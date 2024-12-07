from bilibili_api import video, Credential, sync, get_real_url
from eenhance.utils.config import load_config
from eenhance.constants import PROJECT_ROOT_PATH
from typing import List
import re
import logging
import requests
import json
from string import Template

logger = logging.getLogger(__name__)

# 视频字幕组合
TEMP_VIDEO_MSG = Template(
    "这是一个视频字幕的信息，详情如下：\n \
视频标题：${title}》\n 视频简介: ${desc}\n\n\
视频字幕(含开始结束时间):\n\
${subtitiles}\n\n\
"
)

TEMP_SUBTITLE_MSG = Template("${start} -->${end}: ${content}")


def get_bilibili_real_url(url: str) -> str:
    return sync(get_real_url(url))


class BiliBiliTranscriber:

    def __init__(self):
        self.bilibili_video: video.Video = None
        self.title = None
        self.author = None
        self.content = None
        self.bgpicurl = None

        self.config = load_config()
        self.bilibili_extractor_config = self.config.get("bilibili_transcriber", {})
        cookies_dir = PROJECT_ROOT_PATH / self.bilibili_extractor_config.get(
            "cookies", "./data/cookies"
        )
        cookies_file = cookies_dir / "bili_cookies.json"

        if not cookies_dir.exists():
            cookies_dir.mkdir(parents=True)
            raise FileNotFoundError(
                f"Cookies directory does not exist. Directory created at: {cookies_dir}, please create bili_cookies.json file in this directory"
            )

        if not cookies_file.exists():
            raise FileNotFoundError(
                f"Cookies file does not exist. Please create bili_cookies.json file in {cookies_dir} directory"
            )

        self.credential = self.get_credential(cookies_file)

    def get_credential(self, cookies_path: str) -> Credential | None:
        with open(cookies_path, "r") as f:
            json_obj = json.load(f)
            sessdata = json_obj["SESSDATA"]
            bili_jct = json_obj["bili_jct"]
            buvid3 = json_obj["buvid3"]
            ac_time_value = json_obj["ac_time_value"]

        # 实例化 Credential 类
        credential = Credential(
            sessdata=sessdata,
            bili_jct=bili_jct,
            buvid3=buvid3,
            ac_time_value=ac_time_value,
        )

        if not sync(credential.check_valid()):
            logger.error("Credential is invalid, skipped.")
            return None

        # 检查 Credential 是否需要刷新
        if sync(credential.check_refresh()):
            try:
                # 刷新 Credentil
                sync(credential.refresh())
                with open(cookies_path, "w") as f:
                    f.write(json.dumps(credential.get_cookies(), indent=4))
                    logger.info("Cookies Saved, Cookies Refreshed.")
            except Exception:
                logger.exception("Failed to refresh credential.")
                return None

        return credential

    """
    获取文章标题
    """

    def get_article_title(self) -> str | None:
        return self.title

    """
    获取文章作者
    """

    def get_article_author(self) -> str | None:
        return self.author

    """
    获取文章内容
    """

    def get_article_content(self) -> str | None:
        return self.content

    """
    获取文章背景图片
    """

    def get_article_bgpicurl(self) -> str | None:
        return self.bgpicurl

    def extract_video_id(self, url: str) -> str:
        pattern = r"video/([^/?]+)"
        match = re.search(pattern, url)
        if match:
            return match.group(1)
        else:
            return None

    def parse_video_content(self, subtitle_url: str, title: str, desc: str) -> str:
        rendered_subtitles = []
        subtitle_list = self.parse_bilibili_subtitle(subtitle_url)
        for start_time, end_time, content in subtitle_list:
            rendered_subtitles.append(
                TEMP_SUBTITLE_MSG.substitute(
                    start=start_time, end=end_time, content=content
                )
            )
        subtitiles = "\n".join(rendered_subtitles)

        return TEMP_VIDEO_MSG.safe_substitute(
            title=title, desc=desc, subtitiles=subtitiles
        )

    def parse_bilibili_subtitle(self, url: str) -> List:
        # 发送请求获取字幕数据
        response = requests.get(url)
        data = response.json()
        # 解析字幕数据
        subtitle_list = []
        for item in data["body"]:
            start_time = item["from"]
            end_time = item["to"]
            content = item["content"]
            subtitle_list.append((start_time, end_time, content))

        return subtitle_list

    async def get_video_info(self):
        # 获取视频信息
        info = await self.bilibili_video.get_info()
        self.title = info["title"]
        self.author = info["owner"]["name"]
        self.bgpicurl = info["pic"]

        # 获取视频字幕
        cid = await self.bilibili_video.get_cid(0)
        # 获取信息
        subtitle_info = await self.bilibili_video.get_subtitle(cid)
        logger.info(f"video subtitle info:{subtitle_info}")
        subtitle_url = "https:" + subtitle_info["subtitles"][0]["subtitle_url"]
        self.content = self.parse_video_content(
            subtitle_url=subtitle_url, title=info["title"], desc=info["desc"]
        )

    def video_http(self, url: str) -> str | None:
        try:
            # 解析vid
            video_id = self.extract_video_id(url=url)
            if not video_id:
                return None
            # 实例化 Video 类
            self.bilibili_video = video.Video(bvid=video_id, credential=self.credential)

            # 获取视频信息
            sync(self.get_video_info())

            # 直接返回解析后的内容字符串
            return self.content

        except Exception as e:
            logger.warning(e)
            return None

    @classmethod
    def get_redirected_url(cls, url: str) -> str | None:
        import requests

        try:
            response = requests.get(url, allow_redirects=True)
            return response.url
        except Exception:
            logger.exception("get_redirected_url Error occurred")
            return None


def main():
    # 测试视频URL（这是一个示例视频链接）
    test_url = "https://www.bilibili.com/video/BV1GJ411x7h7"

    try:
        # 实例化转写器
        transcriber = BiliBiliTranscriber()

        # 测试URL重定向
        print("测试URL重定向...")
        redirected_url = transcriber.get_redirected_url(test_url)
        print(f"重定向后的URL: {redirected_url}\n")

        # 测试视频信息提取
        print("开始提取视频信息...")
        content = transcriber.video_http(redirected_url or test_url)

        if content:
            print("视频信息提取成功！")
            print("-" * 50)
            print(content)
            print("-" * 50)
        else:
            print("视频信息提取失败！")

    except Exception as e:
        print(f"发生错误: {str(e)}")
        logging.exception("测试过程中发生错误")


if __name__ == "__main__":
    # 设置日志级别
    main()
