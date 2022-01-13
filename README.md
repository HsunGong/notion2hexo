# notion2hexo

This repo translate notion pages into hexo pages.

Thanks a lot for [notion-down](https://github.com/kaedea/notion-down), I borrow `write_block` from it, and translate to markdown-style.

This is based on [notion-py](https://github.com/jamalex/notion-py), which requires non-offical `token_v2` that need to get by webpage cache.

## installation

### PreInstallation: Modify the config.yaml

`cp config.example.yaml config.yaml`

```yaml
output : "./build"
url : "#REPLACED:https://bolder-oak-f58.notion.site/Test-Blog-eb8445c955144ea5a4ff0b9d97c488b0"
token : "#TODO:notion-sdk-python API"
match_patterns:
  "Test notion-down": # Blog category
    - ^NotionDown.*
    - ^MarkDown.*
    - ^Hexo.*

token_v2: "#REPLACED:notion-py token_v2 API"
```

### Github Action

fork this repo, merge into `XXX.github.io` and run the `github action`.

### Local Run

```bash
git remote add notion2hexo git@github.com:HsunGong/notion2hexo.git
git fetch
git checkout -b notion2hexo notion2hexo/main

pip -r reqiurements.txt
python main.py

git checkout SOURCE_BRANCH # source branch of hexo
rsync -av build/ SOURCE_DIR # SOURCE_DIR like source, store _posts, assets, _drafts
hexo g -d
```

## TODOs:
- change blog category during writing
- check file date:
  - do not generate again
  - only update newer
  - cache mode
- notion-py
  - add cache
- notion-sdk
