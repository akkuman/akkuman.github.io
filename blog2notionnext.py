'''
该文件用来将仓库中的博客填充到 notionnext 中
用法示例
export TOKEN_V2="v02:user_token_or_cookies:xxx"
export POST_DIR=content/posts
export DATABASE_URL=https://www.notion.so/xxx/xxxx?v=xxxx
python blog2notionnext.py
'''

import hashlib
import os
import tempfile
import typing
import re
from notion.client import NotionClient
import notion.collection
from datetime import datetime
from md2notion.upload import upload
import frontmatter
from pathlib import Path
from dataclasses import dataclass
import requests
import urllib.parse
import yaml

TOKEN_V2 = os.environ['TOKEN_V2']
POST_DIR = os.environ['POST_DIR']
DATABASE_URL = os.environ['DATABASE_URL']

client = NotionClient(token_v2=TOKEN_V2)

@dataclass
class MarkdownInfo:
    title: str
    slug: str
    date: datetime
    summary: str
    tags: typing.List[str]
    content: str


def parse_markdown(filepath: str, text: str) -> MarkdownInfo:
    '''解析 markdown
    
    Args:
        filepath: markdown 文件地址
        text: markdown 内容
    Returns:
        返回一个 MarkdownInfo
    '''
    post = frontmatter.loads(text)
    # 处理时间，保证为 datetime 类型
    if isinstance(post.metadata['date'], str):
        post.metadata['date'] = yaml.load(post.metadata['date'], yaml.SafeLoader)
    # 处理标签
    tags = set()
    for i in ['tags', 'categories']:
        if i not in post.metadata:
            continue
        if isinstance(post.metadata[i], list):
            tags.update(post.metadata[i])
        elif isinstance(post.metadata[i], str):
            tags.add(post.metadata[i])
        else:
            print(f'[ERR] {filepath} 错误的信息 {post.metadata[i]}')
    summary = ''
    pattern = re.compile('^\<\!--more--\>$', flags=re.MULTILINE)
    contents = pattern.split(post.content)
    if 'description' in post.metadata:
        summary = post.metadata['description']
    if summary == '' and len(contents) >= 2:
        summary = contents[0]
    content = pattern.sub('\n', post.content, count=1)
    return MarkdownInfo(
        title=post.metadata['title'],
        slug=Path(filepath).stem,
        date=post.metadata['date'],
        summary=summary,
        tags=list(tags),
        content=content,
    )

def calc_md5(content: bytes):
    md5_hash = hashlib.md5()
    md5_hash.update(content)
    return md5_hash.hexdigest()

def get_ext(resp: requests.Response):
    ext = Path(urllib.parse.urlparse(resp.url).path).suffix
    if ext and re.match(r'^\.\w+$', ext):
        return ext
    for i in ['content-type', 'Content-Type']:
        if i not in resp.headers:
            continue
        content_type = resp.headers[i]
        ext = f'.{content_type.split("/")[1]}'
        return ext
    raise ValueError(f'未知的后缀: {resp.url}')


def handle(filepath, row: notion.collection.CollectionRowBlock):
    markdown_text = ''
    with open(filepath, "r", encoding="utf-8") as f:
        markdown_text = f.read()
    # 解析 markdown
    print(f'[INF] 开始解析: {filepath}')
    markdown_info = parse_markdown(filepath, markdown_text)
    print(f'[INF] 解析完成: {filepath}')
    # 将 markdown 
    pattern = re.compile(r'^\!\[.*?\]\(([^)]+)\)', flags=re.MULTILINE)
    with tempfile.TemporaryDirectory() as tmpdirname:
        print(f'[INF] 处理图片: {filepath}')
        tmpdir = Path(tmpdirname)
        img_links: typing.List[str] = pattern.findall(markdown_info.content)
        img_links = list(set(img_links))
        markdown_content = markdown_info.content
        for i in img_links:
            if i.startswith('https://') or i.startswith('http://'):
                url = i
                if url.startswith('https://raw.githubusercontent.com/'):
                    url = f'https://mirror.ghproxy.com/{url}'
                response = requests.get(url)
                if response.status_code != 200:
                    print(f'图片状态码 [{response.status_code}]{i}')
                    continue
                img_content = response.content
                ext = get_ext(response)
            elif i.startswith('/'):
                with open(Path('./static/').joinpath(i[1:]), 'rb') as f:
                    img_content = f.read()
                ext = Path(i).suffix
            else:
                print(f'无效图片 {i}')
                continue
            img_filename = f'{calc_md5(img_content)}{ext}'
            with open(tmpdir.joinpath(img_filename), 'wb') as f:
                f.write(img_content)
            markdown_content = markdown_content.replace(i, img_filename)
        print(f'[INF] 图片处理完成: {filepath}')
        markdown_filepath = tmpdir.joinpath(Path(filepath).name)
        with open(markdown_filepath, 'w', encoding="utf-8") as f:
            f.write(markdown_content)
        # 开始写入 notion
        print(f'[INF] 开始写入 notion: {filepath}')
        row.type = 'Post'
        row.category = '技术分享'
        row.status = 'Draft'
        row.title = markdown_info.title
        row.slug = markdown_info.slug
        row.date = notion.collection.NotionDate(datetime.date(markdown_info.date))
        row.summary = markdown_info.summary
        row.tags = markdown_info.tags
        with open(markdown_filepath, "r", encoding="utf-8") as mdFile:
            upload(mdFile, row)
        print(f'[INF] notion 写入完成: {filepath}')

def main():
    cv = client.get_collection_view(DATABASE_URL)
    for filepath in Path(POST_DIR).rglob("*.md"):
        print(f'[INF] 开始处理: {filepath}')
        row: notion.collection.CollectionRowBlock = cv.collection.add_row()
        handle(filepath, row)
        print(f'[INF] 处理完成: {filepath}')

if __name__ == "__main__":
    main()
