import os
import re
import urllib
from typing import List, Union
from notion.block import PageBlock

from notion.utils import slugify

from notion_down import logger
from notion_down.page.block import (
    PageBaseBlock,
    PageBulletedListBlock,
    PageCalloutBlock,
    PageChannelBlock,
    PageCodeBlock,
    PageColumnBlock,
    PageColumnListBlock,
    PageDividerBlock,
    PageGroupBlock,
    PageHeaderBlock,
    PageImageBlock,
    PageNumberedListBlock,
    PageQuoteBlock,
    PageShortCodeBlock,
    PageEnterBlock,
    PageSubHeaderBlock,
    PageSubSubHeaderBlock,
    PageSyncedCopyBlock,
    PageSyncedSourceBlock,
    PageTableBlock,
    PageTextBlock,
    PageTocBlock,
    PageToggleBlock,
)
from notion_down.page.page import _parse_properties


def _parse_blocks(block: PageBlock, *args, **kwargs) -> List[PageBaseBlock]:
    """Parse single line PageBlock

    Return a list, but with one or more blocks
    """
    new_block = []
    if hasattr(block, "title") and len(str(block.title).strip()) == 0:
        new_block = [PageEnterBlock()]
    elif block.type == "text":
        new_block = [PageTextBlock(block.id, block.type, block.title)]
    elif block.type == "divider":
        new_block = [PageDividerBlock(block.id, block.type)]
    elif block.type == "quote":
        new_block = [PageQuoteBlock(block.id, block.type, block.title)]
    elif block.type == "callout":
        new_block = [PageCalloutBlock(block.id, block.type, block.title)]
    elif block.type == "header":
        new_block = [PageHeaderBlock(block.id, block.type, block.title)]
    elif block.type == "sub_header":
        new_block = [PageSubHeaderBlock(block.id, block.type, block.title)]
    elif block.type == "sub_sub_header":
        new_block = [PageSubSubHeaderBlock(block.id, block.type, block.title)]
    elif block.type == "code":
        symbol = "[notion-down-properties]"
        if symbol in block.title:
            kwargs["properties"] = _parse_properties(symbol, block)
        new_block = [PageCodeBlock(block.id, block.type, block.title, block.language)]
    elif block.type == "collection_view" or block.type == "collection_view_page" or block.type == "view_ids":
        new_block = [PageTableBlock(block.id, block.type, block)]
    elif block.type == "toggle":
        new_block = [PageToggleBlock(block.id, block.type, block.title, block.children)]
    elif block.type == "image":
        from notion_down.config import config

        new_block = [
            PageImageBlock(
                block.id,
                block.type,
                _image_kwargs={
                    "image_caption": block.caption,
                    "image_url": block.source,
                    "image_file": config.output.joinpath(f"assets/image/{block.id}_{block.caption}.jpg"),
                },
            )
        ]
    elif block.type == "page":
        logger.warning(f"Transpose subpage block into link within page {block.id}: `{block.title}`")
        new_block = [PageTextBlock(block.id, block.type, f"Ignored: {block.title}")]
    elif block.type in ["numbered_list", "bulleted_list"]:
        new_block = _parse_list(block)
    elif block.type in ["column_list", "column", "transclusion_container", "transclusion_reference"]:
        new_block = [_parse_group(block)]
    else:
        #TODO: raise ValueError(f"{block.type} is invalid in notion_down.parser.functions")
        logger.error(f"{block.type} is invalid in notion_down.parser.functions")
        new_block = [PageBaseBlock(block.id, block.type)]

    return new_block


def _parse_list(block: PageBlock) -> List[PageNumberedListBlock]:
    _type = block.type
    if _type == "numbered_list":
        _class = PageNumberedListBlock
    elif _type == "bulleted_list":
        _class = PageBulletedListBlock

    new_blocks = []

    def _recursive_parse(cur_blocks, level):
        for _block in cur_blocks:
            _new_block = _class(_block.id, _block.type, _block.title, level)
            new_blocks.append(_new_block)
            if children:
                _recursive_parse(_block.children, level + 1)

    level = 0
    new_block = _class(block.id, block.type, block.title, level)
    new_blocks.append(new_block)
    children = block.children
    if children:
        _recursive_parse(children, level + 1)

    return new_blocks


def _parse_group(block: PageBlock) -> PageGroupBlock:
    _type = block.type
    if _type == "column_list":
        _class = PageColumnListBlock
    elif _type == "column":
        _class = PageColumnBlock
    elif _type == "transclusion_container":
        _class = PageSyncedSourceBlock
    elif _type == "transclusion_reference":
        _class = PageSyncedCopyBlock

    new_block = _class(block.id, block.type)

    column_blocks = []
    children = block.children
    if children:
        for child in children:
            if _type == "column":
                column_blocks.extend(_parse_blocks(child))
            elif _type == "column_list":
                column_blocks.append(_parse_group(child))

    new_block.children = column_blocks
    return new_block
