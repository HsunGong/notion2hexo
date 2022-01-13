import urllib
from typing import List

# blocks
from notion.block import PageBlock
from notion_down.page.block import PageBaseBlock
from notion_down.page.page import NotionPage

# parsers
from notion_down.parser.short_block import (
    _is_short_code_start,
    _parse_short_code_chunks,
)
from notion_down.parser.toc import _is_toc, _parse_toc_block
from notion_down.parser.functions import _parse_blocks, _parse_properties


def parse(page) -> NotionPage:
    """Step 1: main parse part

    Generate a NotionPage Object, which is a list-style of page blocks
    """
    page_cover = page.get("format.page_cover")
    if page_cover:
        if str(page_cover).startswith("http"):
            page_cover = str(page_cover)
        else:
            page_cover = "https://www.notion.so/image/" + urllib.parse.quote(
                "https://www.notion.so{}".format(page_cover).replace("/", "%2F")
            )

    # Step 2: parse page blocks
    blocks, properties = _parse_page_blocks(page.children)
    return NotionPage(id=page.id, title=page.title, cover=page_cover, blocks=blocks, properties=properties)


def _parse_page_blocks(blocks: List[PageBlock]) -> List[PageBaseBlock]:
    """Step 2: parse page.children into blocks
    
    Return a list(sequence) of page blocks
    """
    page_blocks = []
    properties = {}

    # parse page blocks
    idx = 0
    while idx < len(blocks):
        block = blocks[idx]

        # Channel Block START
        if _is_short_code_start(block):
            new_block, idx_end = _parse_short_code_chunks(blocks, idx)
            if idx_end > idx:
                # success
                page_blocks.append(new_block)
                idx = idx_end
                continue
        elif _is_toc(block):
            new_block, idx_end = _parse_toc_block(blocks, idx)
            if idx_end > idx:
                # success
                page_blocks.append(new_block)
                idx = idx_end
                continue

        # Basic Parsing
        new_blocks = _parse_blocks(block, properties=properties)
        page_blocks.extend(new_blocks)
        idx += 1

    return page_blocks, properties