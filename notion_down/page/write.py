from typing import Dict, List, Tuple
from pathlib import Path
import os.path as P
import requests

from notion.utils import slugify

from notion_down.page.page import NotionPage
from notion_down import GIT_VERSION, logger, VERSION
from notion_down.page.block import PageBaseBlock, PageBlockJoiner, PageImageBlock


class NotionPageWriter:
    """Merge version of NotionPageWriter and HexoWriter"""

    def __init__(self, output_root: Path, cat: str):
        self.output_root = output_root
        self.category = Path(cat)

        self.block_joiner: PageBlockJoiner = PageBlockJoiner()
        self.image_downloader: ImageDownloader = ImageDownloader()

        self.assets_dir = Path("assets")
        self.post_dir = Path("_posts")
        self.draft_dir = Path("_drafts")
        (self.output_root / self.assets_dir).mkdir(parents=True, exist_ok=True)
        (self.output_root / self.post_dir).mkdir(parents=True, exist_ok=True)
        (self.output_root / self.draft_dir).mkdir(parents=True, exist_ok=True)

    def parse_file_path(self, notion_page: NotionPage) -> Path:
        base_path = self.output_root
        if notion_page.is_published():
            return base_path / self.post_dir / self.category / notion_page.get_file_name()
        else:
            return base_path / self.draft_dir / self.category / notion_page.get_file_name()

    def _start_writing(self, notion_page: NotionPage) -> List[str]:
        page_lines = []
        page_lines.extend(self._write_header(notion_page))
        page_lines.extend(self._write_blocks(notion_page.blocks))
        page_lines.extend(self._write_tail(notion_page))
        return page_lines

    def _write_header(self, notion_page: NotionPage):
        page_lines = []
        page_lines.append("")

        front_matter_lines = self._write_front_matter(notion_page)
        if len(front_matter_lines) > 0:
            page_lines.extend(front_matter_lines)
            page_lines.append("")
        return page_lines

    def _write_front_matter(self, notion_page: NotionPage) -> List[str]:
        """
        :see https://hexo.io/docs/front-matter
        """
        if len(notion_page.properties) == 0:
            return []

        front_matter = {
            "title": notion_page.get_title(),
            "date": notion_page.get_date(),
            "tags": notion_page.get_tags(),
            "categories": notion_page.get_categories(),
            "layout": None,
            "updated": None,
            "comments": None,
            "permalink": None,
            "texcerptags": None,
            "disableNunjucks": None,
            "lang": None,
            "thumbnail": None,
        }
        # Write front matter
        lines = ["---"]

        if notion_page.cover:
            image_url =  notion_page.cover
            image_path = self.image_downloader.get_image_path(notion_page.cover, "Page Cover")
            image_source = self.assets_dir / self.category / image_path  # relative path
            image_file = self.output_root / image_source
            # Check if downloaded before
            if not image_file.exists():
                self.image_downloader.download_image(image_url, image_file)
            front_matter["thumbnail"] = image_source

        for key in front_matter.keys():
            if not front_matter[key]:
                continue
            if type(front_matter[key]) == list:
                lines.append("{}:".format(key))
                lines.append("\n".join([" - {}".format(it) for it in front_matter[key]]))
            else:
                lines.append("{}: {}".format(key, front_matter[key]))
        lines.append("---")

        return lines

    def _write_blocks(self, blocks: List[PageBaseBlock]) -> List[str]:
        page_lines = []
        for idx, block in enumerate(blocks):
            if self._on_write_block(block):
                logger.debug(f"Skip block {block.id}:{block.title}")
                continue

            # Check prefix-separator
            if self.block_joiner.should_add_separator_before(blocks, idx):
                page_lines.append("")

            # Curr block
            if block.type in ["bulleted_list", "numbered_list", "undefined"]:
                page_lines.append(self._write_curr_block(block, depth=0))
            else:
                page_lines.extend(
                    [
                        self._write_curr_block(block, depth=0),
                        ""
                    ]
                )

            # Check suffix-separator
            if self.block_joiner.should_add_separator_after(blocks, idx):
                page_lines.append("")
        return page_lines

    def _on_write_block(self, block):
        if block.type == "channel_block":
            if str(block.channel).lower():
                logger.error("Skip channel block: {}".format(block.channel))
                return True
        if block.type == "table_of_contents":
            return True
        return False

    def _write_curr_block(self, block: PageBaseBlock, depth) -> str:
        if block.is_group():
            # def handler(blocks: List[PageBaseBlock]) -> str:
            #     lines = []
            #     for it in blocks:
            #         if type(it) == list:
            #             for _i in it:
            #                 lines.extend(self._write_curr_block(_i, depth + 1))
            #         else:
            #             lines.extend(self._write_curr_block(it, depth + 1))
            #     return "".join(lines)

            # block.on_write_children(handler)
            return block.write_block()

        if self.image_downloader.need_download_image(block):
            # Download image to assets dir
            image_path = self.image_downloader.get_image_path(block.image_url, block.image_caption)
            image_source = self.assets_dir / image_path  # relative path

            block.image_file = self.output_root / self.assets_dir / image_path
            # Check if downloaded before
            if not block.image_file.exists():
                self.image_downloader.download_image(block.image_url, block.image_file)

            return block.write_image_block(Path("/") / image_source)

        return block.write_block()

    def _write_tail(self, notion_page: NotionPage) -> List[str]:
        page_lines = []
        page_lines.append("")
        page_lines.append(f"<!-- Generated by {type(self).__name__}")
        page_lines.append(f"notion-down.version = {VERSION}")
        page_lines.append(f"notion-down.revision = {GIT_VERSION}")
        for key in notion_page.properties.keys():
            page_lines.append("{} = {}".format(key, notion_page.properties[key]))
        page_lines.append("-->")
        return page_lines


class ImageDownloader:
    def need_download_image(self, block) -> bool:
        if block.type != "image":
            return False
        if not str(block.image_url).startswith("http"):
            logger.warning("image not stored in http mode")
            return False
        return "keep-url-source=true" not in str(block.image_url).lower()

    def download_image(self, image_url: str, image_file: Path) -> True:
        if image_url.startswith("https://"):
            image_url = image_url.replace("https://", "http://")

        try:
            r = requests.get(image_url, allow_redirects=True, timeout=(5, 10))
            open(image_file, "wb").write(r.content)
            return True
        except requests.exceptions.RequestException as e:
            logger.warning(f"Image download failed {e}")
            return False

    def get_image_path(self, image_url, image_caption, def_ext=".jpg") -> Path:
        prefix = image_url
        if "?" in image_url:
            prefix = image_url[: image_url.find("?")]
        file_name = prefix
        if "/" in prefix:
            file_name = prefix[prefix.rfind("/") + len("/") :]
            if len(file_name) <= 0 or str(file_name).lower().startswith("untitled."):
                prefix = image_url[: image_url.rfind("/")]
                if "/" in prefix:
                    file_name = "{}-{}".format(prefix[prefix.rfind("/") + len("/") :], file_name)
                    pass

        if image_caption and len(image_caption) > 0:
            file_name = image_caption + "-" + file_name
        splitext = P.splitext(file_name)
        return Path(slugify(splitext[0]) + (splitext[1] if splitext[1] else def_ext))


def write_page(notion_page: NotionPage, writer: NotionPageWriter, override_mode=2):
    """
    override_mode:
        - 0: not override
        - 1: override if newer
        - 2: always override
    """
    if not notion_page.is_markdown_able():
        logger.warning("Skip non-markdownable page: " + notion_page.get_identify())
    if not notion_page.is_output_able():
        logger.warning("Skip non-outputable page: " + notion_page.get_identify())

    filtered_lines = writer._start_writing(notion_page)
    file_path: Path = writer.parse_file_path(notion_page)
    if file_path.exists():
        if override_mode == 0:
            logger.info(f"Skip write to file {file_path}")
            return
        elif override_mode == 1:
            logger.info(f"Skip write to file {file_path}")
            return

    file_path.parent.mkdir(parents=True, exist_ok=True)
    with file_path.open("w") as f:
        for line in filtered_lines:
            f.write(line + "\n")
