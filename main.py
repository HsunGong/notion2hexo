from notion_down.config import parse, Config
from notion_down.read import NotionReader
from notion_down import logger
from notion_down.page.write import NotionPageWriter, write_page

if __name__ == '__main__':
    args = parse()
    
    # from notion_client import Client
    # client = Client(auth=args.token)
    # notion_reader = NotionSDKReader(client)
    from notion.client import NotionClient
    client = NotionClient(token_v2=args.token_v2, enable_caching=True)

    reader = NotionReader(client, args.url, args.match_patterns)

    rendered_catories = reader.handle()
    for cat, pages in rendered_catories.items():
        cat = cat
        logger.info(f"Write data to {args.output}/{cat}")

        writer = NotionPageWriter(args.output, cat)
        for page in pages:
            write_page(page, writer)