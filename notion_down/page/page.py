from pathlib import Path
from typing import List, NamedTuple, Union
from notion.utils import slugify
from notion_down import logger

"""
NotionDown page properties to hexo front matter mapping

`key =` is forbidden, once defined, must set value

```
[notion-down-properties]
title = NotionDown Custom Page Properties Support
date = 2021-05-20
Published = false
Categories = NotionDown, hexo
Tag = Notion, NotionDown
```

Changed to

---
xxxx
xxxx
---
"""

def _parse_properties(symbol, block):
    """parse PageBlock properties, that may used in NotionPage"""
    properties = {}

    content = block.title
    if symbol in content:
        content_properties = content[content.rfind(symbol) + len(symbol):]
        for line in str(content_properties).split("\n"):
            if '=' in line:
                _split = "="
            elif ":" in line:
                _split = ":"
            else:
                continue

            ### parse property
            try:
                key, value = line.split(_split)
                if key == "category":
                    key = "categories"
                if key == "tag":
                    key = "tags"
            except:
                logger.error(f"Parse properties error: {line}")
            finally:
                key = key.strip().lower()
                value = value.strip()
            
            ### add to dict
            if ',' in value:
                properties[key] = [it.strip() for it in value.split(',')]
            else:
                properties[key] = value
    return properties

# noinspection PyBroadException,PyMethodMayBeStatic
class NotionPage(NamedTuple):
    """
    parse notion.collection.pageBlock into NotionPage
    """

    id: str
    title: str  # this is the notion title, which is perfer not used
    # date = None
    cover: str
    blocks: list
    properties: dict

    def is_markdown_able(self):
        return self.get_title() is not None  # and self.get_date() is not None

    def is_output_able(self):
        return self.get_file_name() is not None

    def get_identify(self):
        return "[{}] {}".format(self._id, self.get_title())

    def get_title(self):
        data = self.properties.get("title")
        if data is None or len(data) == 0:
            return self.title
        else:
            return data

    def get_date(self):
        data = self.properties.get("date")
        if self.properties.get("data") is None:
            return "undefined"
        else:
            return self.properties.get("date")

    def get_categories(self) -> Union[List[str], str]:
        data = self.properties.get("categories")
        if data is None:
            return "default"
        else:
            return data

    def get_tags(self) -> Union[List[str], str]:
        data = self.properties.get("tags")
        if data is None:
            return "undefined"
        else:
            return data

    def is_published(self):
        pub = self.properties.get("published")
        if pub is None:
            return True
        elif type(pub) != str:
            return False
        elif pub.lower() in ["true", "1", "t", "y", "yes", "yeah", "yup", "certainly", "uh-huh"]:
            return True
        else:
            return False

    def get_file_name(self) -> Path:
        filename = self.properties.get("filename")
        if filename is not None and type(filename) == str:
            if not filename.endswith(".md"):
                filename = filename + ".md"
        elif len(self.get_title()) > 0:
            filename = slugify(self.get_title()) + ".md"
        elif len(self._id) > 0:
            filename = self._id + ".md"
        return Path(filename)
