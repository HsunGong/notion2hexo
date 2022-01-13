import argparse
from typing import NamedTuple
import yaml
from pathlib import Path
import os
import re

if "NOTION_TOKEN" in os.environ:
    NOTION_TOKEN = os.environ["NOTION_TOKEN"]
else:
    NOTION_TOKEN = ""


class Config(NamedTuple):
    token: str = ""
    output: Path = Path("./build")
    url: str = ""
    token_v2: str = ""
    match_patterns: dict = {"default": re.compile(".*")} # cat : filter_pattern

global config

def parse() -> Config:
    parser = argparse.ArgumentParser("notion download to markdown in hexo format")
    parser.add_argument("--config", "-c", help="config in yaml", type=str, default="./config.yaml")
    parser.add_argument("--url", "-u", help="blog url", type=str, default="")
    parser.add_argument("--match_patterns", type=dict, default={})
    parser.add_argument(
        "--token",
        "-t",
        help="notion token, NOTION_TOKEN",
        type=str,
        default=NOTION_TOKEN,
    )
    parser.add_argument("--token_v2", "-t2", type=str)
    parser.add_argument("--output", "-o", help="output path", type=str, default="./build")

    args = parser.parse_args()

    # args priority is higher than yaml
    opt = vars(args)
    args = yaml.load(open(args.config), Loader=yaml.FullLoader)
    opt.update(args)
    opt.pop("config")

    _patterns = {}
    for key, match_pattern in opt["match_patterns"].items():
        match_pattern = [ f"({p})" for p in match_pattern]
        match_pattern = r'\b(?:%s)\b' % '|'.join(match_pattern)
        _patterns[key] = re.compile(match_pattern)
    _patterns.update({"default": re.compile(".*")})
    opt["match_patterns"] = _patterns
    opt["output"] = Path(opt["output"])

    global config
    config = Config(**opt)
    print("Loaded config:", config)
    return config
