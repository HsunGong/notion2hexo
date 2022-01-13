from typing import List, Tuple

from notion.block import PageBlock

from notion_down.page.block import PageBaseBlock, PageChannelBlock, PageGroupBlock, PageShortCodeBlock
from notion_down.parser.functions import _parse_blocks


def _is_short_code_start(block):
    """Start with SHORT_CODE_"""
    if block.type == "text":
        if str(block.title).startswith("<!-- SHORT_CODE_"):
            return True
    return False


def _is_short_code_end(block):
    """END with SHORT_CODE_END"""
    if block.type == "text":
        if str(block.title).startswith("SHORT_CODE_END -->"):
            return True
    return False


def _parse_short_code_chunks(blocks: List[PageBlock], idx_start) -> Tuple[PageGroupBlock, int]:
    """parse `SHORT_CODE`, cross blocks

    Return
      - Case 1) None, -1, if not satisified.
      - Case 2) block, idx_end

    """
    if idx_start < 0 or idx_start >= len(blocks) - 1:
        return None, -1
    if not _is_short_code_start(blocks[idx_start]):
        return None, -1

    start_line = str(blocks[idx_start].title)
    block_id = blocks[idx_start].id

    group_block: PageGroupBlock = PageGroupBlock(block_id)

    symbol = "SHORT_CODE_"
    if symbol in start_line:
        group_block = PageShortCodeBlock(block_id, _type="short_code_block")

        name = start_line[start_line.rfind(symbol) + len(symbol) :].strip()
        symbol_end = "="
        if symbol_end in name:
            name = name[: name.find(symbol_end)]
        group_block.name = name

    symbol = "SHORT_CODE_CHANNEL="
    if symbol in start_line:
        group_block = PageChannelBlock(block_id)

        group_block.name = "CHANNEL"
        channel = start_line[start_line.rfind(symbol) + len(symbol) :].strip()
        group_block.channel = channel

    # Update group_block.children
    channel_blocks: List[PageBaseBlock] = []

    end_found = False
    idx = idx_start + 1
    for idx in range(idx_start + 1, len(blocks)):
        block = blocks[idx]

        # Channel Block END
        if _is_short_code_end(block):
            end_found = True
            break

        # Mapping for parse
        channel_blocks.extend(_parse_blocks(block))
        
    if end_found:
        group_block.children = channel_blocks
        return group_block, idx + 1
    else:
        return None, -1
