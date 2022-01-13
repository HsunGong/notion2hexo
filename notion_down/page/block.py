# From notion.collection
from typing import Callable, List
import re

from notion.block import CollectionViewBlock, TextBlock

TAB = 2


class PageBaseBlock:
    def __init__(self, _id="unknown", _type="unknown", _children=[]):
        self.id = _id
        self.type = _type
        self.children: List[PageBaseBlock] = _children
        self.title = ""

    def write_block(self):
        return f"<!-- unsupported page block type: {self.type} {self._wip_msg()} -->" ""

    def _wip_msg(self):
        return "notion id: " + self.id

    def is_group(self):
        return self.children is not None and len(self.children) != 0


GROUP_MAP = {
    "group_block": "Group",
    "transclusion_container": "SyncedSourceBlock",
    "transclusion_reference": "SyncedCopyBlock",
    "channel_block": "Channel",
    "column_list": "ColumnList",
    "column": "Column",
    "short_code_block": "ShortCode",
}


class PageGroupBlock(PageBaseBlock):
    def __init__(self, _id="undefined", _type="group_block", _name="", _children=[]):
        super().__init__()
        self.type = _type
        self.children: List[PageBaseBlock] = _children

        self.group = GROUP_MAP[_type]
        self.name = _name
        self.on_write_children_handler: Callable[[List[PageBaseBlock]], str] = None

    def on_write_children(self, handler: Callable[[List[PageBaseBlock]], str]):
        self.on_write_children_handler = handler
        pass

    def write_block(self):
        if not self.on_write_children_handler:
            def handler(blocks: List[PageBaseBlock]) -> str:
                lines = [it.write_block() for it in blocks]
                return "\n".join(lines)

            self.on_write_children_handler = handler
        text = self.on_write_children_handler(self.children)
        return f"{self.write_begin()}\n{text}\n{self.write_end()}"

    def write_begin(self):
        return "<!-- {} BGN{} -->".format(self.group, "" if len(self.name) == 0 else " " + self.name)

    def write_end(self):
        return "<!-- {} END{} -->".format(self.group, "" if len(self.name) == 0 else " " + self.name)


class PageSyncedSourceBlock(PageGroupBlock):
    def write_block(self):
        if not self.on_write_children_handler:

            def handler(blocks: List[PageBaseBlock]) -> str:
                lines = [it.write_block() for it in blocks]
                return "\n".join(lines)

            self.on_write_children_handler = handler
        text = self.on_write_children_handler(self.children)
        return text


class PageSyncedCopyBlock(PageGroupBlock):
    def write_block(self):
        lines = [it.write_block() for it in self.children]
        return "<!-- SyncedBlock: {}\nThis is a reference block. {}\n-->".format(self.name, "\n".join(lines))


class PageShortCodeBlock(PageGroupBlock):
    def write_block(self):
        lines = [it.write_block() for it in self.children]
        return "<!-- ShortCode: {}\n{}\n-->".format(self.name, "\n".join(lines))


class PageChannelBlock(PageGroupBlock):
    channel = ""

    def write_begin(self):
        return "<!-- For {} only BGN: {} -->".format(self.group, self.channel)

    def write_end(self):
        return "<!-- For {} only END: {} -->".format(self.group, self.channel)


class PageColumnListBlock(PageGroupBlock):
    def write_block(self):
        if not self.on_write_children_handler:
            def handler(blocks: List[PageBaseBlock]) -> str:
                column_lines = []
                for idx, column_block in enumerate(blocks):
                    column_lines.append(
                        "{}<!-- Column {} start -->\n{}\n<!-- Column end -->".format(
                            "\n" if idx > 0 else "", idx, column_block.write_block()
                        )
                    )
                return "\n".join(column_lines)

            self.on_write_children_handler = handler
        return super().write_block()
    def write_begin(self):
        return "<table border=\"0\"><tr>"
    def write_end(self):
        return "</tr></table>"


# noinspection PyMethodMayBeStatic,PyUnusedLocal
class PageBlockJoiner:
    def should_add_separator_before(self, blocks: List[PageBaseBlock], curr_idx) -> bool:
        block = blocks[curr_idx]
        block_pre = None if curr_idx <= 0 else blocks[curr_idx - 1]
        block_nxt = None if curr_idx >= len(blocks) - 1 else blocks[curr_idx + 1]
        result = False

        # Check prefix-separator
        if isinstance(block, PageEnterBlock):
            pass
        else:
            if not block_pre:
                pass
            else:
                if isinstance(block_pre, PageEnterBlock):
                    pass
                else:
                    if isinstance(block_pre, (PageBulletedListBlock, PageNumberedListBlock)):
                        if isinstance(block, (PageBulletedListBlock, PageNumberedListBlock)):
                            pass
                        else:
                            result = True
                    elif isinstance(block, PageTextBlock):
                        pass
                    else:
                        result = True

        return result

    def should_add_separator_after(self, blocks: List[PageBaseBlock], curr_idx) -> bool:
        block = blocks[curr_idx]
        block_pre = None if curr_idx <= 0 else blocks[curr_idx - 1]
        block_nxt = None if curr_idx >= len(blocks) - 1 else blocks[curr_idx + 1]
        result = False

        # Check suffix-separator
        if block_nxt is None:
            result = True

        return result


class PageColumnBlock(PageGroupBlock):
    def __init__(self, _id="undefined", _type="group_block", _name="", _children=[]):
        super().__init__(_id=_id, _type=_type, _name=_name, _children=_children)
        self.children: List[PageBaseBlock] = []
        self.block_joiner: PageBlockJoiner = PageBlockJoiner()

    def write_block(self):
        if not self.on_write_children_handler:
            def handler(blocks: List[PageBaseBlock]) -> str:
                lines = []
                for idx in range(len(blocks)):
                    block = self.children[idx]
                    if self.block_joiner.should_add_separator_before(self.children, idx):
                        lines.append("")
                    lines.append(block.write_block())
                    if self.block_joiner.should_add_separator_after(self.children, idx):
                        lines.append("")
                return "".join(lines)
            self.on_write_children_handler = handler

        return super().write_block()

    def write_begin(self):
        return "<td style=\"vertical-align:top;\">"
    def write_end(self):
        return "</td>"


class PageTocBlock(PageBaseBlock):
    def __init__(self, _id="unknown", _type="unknown", _blocks=[]):
        super().__init__(_id=_id, _type=_type)
        self.page_blocks = _blocks

    def write_block(self):
        """
        # Table of Contents
        -. [Example](#example)
        -. [Example2](#example2)
        -.   [Third Example](#third-example)
        -.   [Fourth Example](#fourth-examplehttpwwwfourthexamplecom)
        """

        block_lines = []
        for block in self.page_blocks:
            if block.type == "header":
                block_lines.append(
                    " * [{}](#{})".format(block.text, str(block.text).lower().replace(" ", "-"))
                )
            if block.type == "sub_header":
                block_lines.append(
                    " * {}[{}](#{})".format(
                        "&nbsp;" * 4, block.text, str(block.text).lower().replace(" ", "-")
                    )
                )
            if block.type == "sub_sub_header":
                block_lines.append(
                    " * {}[{}](#{})".format(
                        "&nbsp;" * 8, block.text, str(block.text).lower().replace(" ", "-")
                    )
                )

        return ("\n".join(block_lines)) if len(block_lines) > 0 else ""


# noinspection DuplicatedCode,PyMethodMayBeStatic
class PageTableBlock(PageBaseBlock):
    def __init__(self, _id, _type, _block):
        super().__init__(_id=_id, _type=_type)
        self.block: CollectionViewBlock = _block

    @staticmethod
    def find_one(array, predicate):
        finds = [it for it in array if predicate(it)]
        if finds:
            return finds[0]
        return finds

    def write_block(self):
        if not self.block:
            return ""
        block_lines = []

        column_properties = self.block.collection.get_schema_properties()
        ordered_column_ids = self.block.views[0].get("format.table_properties")

        ordered_column_properties = []
        for id in ordered_column_ids:
            ordered_column_properties.append(
                self.find_one(column_properties, lambda it: it["id"] == id["property"])
            )

        slugs = [it["slug"] for it in ordered_column_properties]
        types = [it["type"] for it in ordered_column_properties]

        block_lines.append(
            "{}".format(
                " | ".join([str(it["name"]).replace("|", "&#124;") for it in ordered_column_properties])
            )
        )
        block_lines.append("{}".format(" | ".join([":---:" for it in ordered_column_properties])))

        try:
            # https://github.com/jamalex/notion-py/issues/355
            for row in self.block.collection.get_rows(limit=100):
                contents = []
                for idx, slug in enumerate(slugs):
                    item_type = types[idx]
                    item_value = getattr(row, slug)
                    contents.append(
                        str(self.__parse_collection_item(item_type, item_value)).replace("|", "&#124;")
                    )
                block_lines.append("{}".format(" | ".join(contents)))
        except Exception as e:
            from notion_down import logger
            logger.error(str(e))

        return "\n".join(block_lines)

    def __parse_collection_item(self, collection_type, item):
        if item is None:
            return str(item)

        if collection_type == "date":
            if item.end:
                return "{} - {}".format(item.start, item.end)
            return "{}".format(item.start)

        if collection_type == "person":
            users = []
            for user in item:
                if user.email:
                    users.append("{} <{}>".format(user.full_name, user.email))
                else:
                    users.append("{}".format(user.full_name))
            return ", ".join(users)

        if collection_type == "file":
            urls = []
            for url in item:
                file_name = None
                if "/" in url:
                    file_name = url[url.rfind("/") + len("/") :]
                    if "?" in file_name:
                        file_name = file_name[: file_name.find("?")]
                if file_name:
                    urls.append("[{}]({})".format(file_name, url))
                else:
                    urls.append(url)
            return ", ".join(urls)

        return str(item)


class PageTextBlock(PageBaseBlock):
    def __init__(self, _id, _type, _text=""):
        super().__init__(_id, _type)
        self.text = _text

    def write_block(self):
        # Check obfuscated links or images
        pattern = re.compile("\[.*\]\(\[.*\]\(.*\)\)")
        if pattern.search(self.text) is not None:
            # parse obfuscated blocks
            obfuscated_links = []

            try:
                p = pattern
                for m in p.finditer(self.text):
                    obfuscated_link = m.group()
                    prefix = obfuscated_link[: obfuscated_link.find("]([")] + "]"
                    link = obfuscated_link[
                        obfuscated_link.rfind("](") + len("](") : obfuscated_link.rfind("))")
                    ]
                    obfuscated_links.append("{}({})".format(prefix, link))

                intermediate_text = re.sub(pattern, "{}", self.text)
                return intermediate_text.format(*obfuscated_links)
            except Exception as e:
                print("Parse obfuscated links block error: text = {}\t\n".format(self.text))
                raise e

        return self.text


class PageEnterBlock(PageTextBlock):
    def __init__(self):
        super().__init__(_id="undefined", _type="undefined", _text="")

    def write_block(self):
        return self.text


class PageQuoteBlock(PageTextBlock):
    def write_block(self):
        return "> {}".format(self.text)


class PageDividerBlock(PageTextBlock):
    def __init__(self, _id, _type):
        super().__init__(_id=_id, _type=_type)
        self.text = "---"

    def write_block(self):
        return self.text


class PageCalloutBlock(PageTextBlock):
    def write_block(self):
        lines = str(self.text).split("\n")
        return "> " + "> ".join(lines)


class PageHeaderBlock(PageTextBlock):
    """Preserve `#` for title"""

    def write_block(self):
        return "# {}".format(self.text)


class PageSubHeaderBlock(PageTextBlock):
    def write_block(self):
        return "## {}".format(self.text)


class PageSubSubHeaderBlock(PageTextBlock):
    def write_block(self):
        return "### {}".format(self.text)


class PageCodeBlock(PageTextBlock):
    def __init__(self, _id, _type, _text, _lang=""):
        super().__init__(_id, _type, _text)
        self.lang = _lang

    def write_block(self):
        return f"```{self.lang}\n{self.text}```"


class PageImageBlock(PageBaseBlock):
    def __init__(self, _id, _type, _image_kwargs):
        super().__init__(_id=_id, _type=_type)
        self.image_caption = _image_kwargs["image_caption"]
        self.image_url = _image_kwargs["image_url"]
        self.image_file = _image_kwargs["image_file"]

    def write_block(self):
        return self.write_image_block(self.image_url)

    def write_image_block(self, image_source):
        return "![{}]({})".format(self.image_caption, image_source)


class PageNumberedListBlock(PageTextBlock):
    def __init__(self, _id, _type, _text, _level=0):
        super().__init__(_id=_id, _type=_type)
        self.text = _text
        self.level = _level

    def write_block(self):
        return "{}1. {}".format(" " * TAB * self.level, self.text)


class PageBulletedListBlock(PageNumberedListBlock):
    def write_block(self):
        return "{} - {}".format(" " * TAB * self.level, self.text)


class PageToggleBlock(PageTextBlock):
    def __init__(self, _id, _type, _text="", _children=[]):
        super().__init__(_id, _type, _text=_text)
        self.children = _children
        self.status = "details"  # or 'details open'

    def on_write_children(self, handler: Callable[[List[PageBaseBlock]], str]):
        self.on_write_children_handler = handler
        pass

    def write_block(self):
        datas = []
        for child in self.children:
            if hasattr(child, "title"):
                datas.append(child.title)
        return (
            f"<{self.status}>\n"
            + f"\t<summary>{self.text}</summary>\n"
            + "\t<p>{}</p>\n".format("</p>\n<p>".join(datas))
            + "</details>\n"
        )
