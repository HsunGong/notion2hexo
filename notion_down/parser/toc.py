from typing import List, Tuple

from notion.block import PageBlock

from notion_down.page.block import PageBaseBlock, PageChannelBlock, PageGroupBlock, PageShortCodeBlock, PageTocBlock
from notion_down.parser.functions import _parse_blocks
from notion_down import logger

def _is_toc(block):
    if block.type == "table_of_contents":
        return True
    return False

def _parse_toc_block(blocks: List[PageBlock], idx_start) -> Tuple[PageGroupBlock, int]:
    block = blocks[idx_start]
    new_block = PageTocBlock(block.id, block.type, [])

    sub_blocks = []

    for idx in range(idx_start + 1, len(blocks)):
        block = blocks[idx]
        if not _is_toc(block):
            idx_end = idx
            break

        # Mapping for parse
        sub_blocks.extend(_parse_blocks(block))
    else:
        idx_end = len(blocks) # 0-based larger than idx-final
        logger.info("Only toc")

    new_block.page_blocks = sub_blocks
    return new_block, idx_end
