import os
from typing import Dict, List, NamedTuple
import re
from tqdm import tqdm

try:
    from notion_client.client import BaseClient as SDKCBaseClient
    from notion_client import APIResponseError, APIErrorCode
except:
    pass
try:
    from notion.client import NotionClient as NotionClient
    from notion.block import PageBlock
except Exception as e:
    raise e

from notion_down import logger
from notion_down.page.page import NotionPage
from notion_down.parser.main import parse


def filter_page(page_block: PageBlock, pattern: re.Pattern):
    # filter pages
    if not hasattr(page_block, "title"):
        logger.info(f"`{page_block.id}` is used")
        return True
    elif pattern.match(page_block.title):
        logger.info(f"{page_block.id}: `{page_block.title}` is used")
        return True
    else:
        logger.warning(f"{page_block.id}: `{page_block.title}` is skipped")
        return False


def recurse_read(page: PageBlock, level=-1, max_level=-1):
    """recursive read pages, list mode
    1) If level == max_level: OK -> level+=1 -> return
    2) If level < max_level: OK -> level+=1 -> recurse
    """
    assert level != -1 and max_level != -1

    level += 1  # update level
    if level == max_level:
        return []

    page_blocks = []
    if len(page.children) != 0:
        for subpage in page.children:
            _children = recurse_read(subpage, level, max_level)
            page_blocks.extend(_children)

    return page_blocks


def format_category(cat: str) -> str:
    cat = re.sub('[!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~ ]', "-", cat)
    cat = re.sub('[＂＃＄％＆＇（）＊＋，－／：；＜＝＞＠［＼］＾＿｀｛｜｝～｟｠｢｣､\u3000、〃〈〉《》「」『』【】〔〕〖〗〘〙〚〛〜〝〞〟〰〾〿–—‘’‛“”„‟…‧﹏﹑﹔·！？｡。]', "", cat)
    return cat.lower()


class NotionReader:
    """See BaseClient for more details"""

    def __init__(self, client: NotionClient, url: str, match_patterns: Dict[str,re.Pattern]):
        self.client = client
        self.url = url
        self.patterns = match_patterns
        self.catories = {}

    def handle(self) -> Dict[str, List[NotionPage]]:
        logger.info("Handling Posts")
        try:
            main_block = self.client.get_block(self.url)
        except Exception as e:
            if "401 Client Error: Unauthorized" in str(e):
                raise Exception("Please make sure your notion_token_v2 is up-to-date!")
            else:
                raise e

        def check_child(child):
            """check child is pageable"""
            if isinstance(child, PageBlock):
                return child.title
            else:
                return ""


        ### Load data
        catories = {}
        for child in main_block.children:
            title = format_category(child.title)
            if check_child(child):
                catories[title] = []
                for grandson in child.children:
                    if check_child(grandson):
                        catories[title].append(grandson)
                    else:
                        logger.warning(f"From category {title}: {grandson.title}")
            else:
                logger.warning(f"From root: {title}")

        ### Filter data
        self.catories = {}
        for cat, children in catories.items():
            if cat in self.patterns:
                pattern = self.patterns[cat]
            else:
                pattern = self.patterns["default"]

            # not changeable
            children = tuple(filter(lambda child: filter_page(child, pattern), children))

            logger.info(f"Category {cat} has {len(children)} subpages to render")
            self.catories[cat] = children

        #### Render to Local Markdown Page
        rendered_catories = {}
        for cat, children in self.catories.items():
            new_children = [parse(child) for child in tqdm(children[:2])]
            rendered_catories[cat] = new_children

        return rendered_catories