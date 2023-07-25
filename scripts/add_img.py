# 脚本功能：添加图片到违规图片数据库
import __init__
import re
import cv2
import pathlib
import asyncio
import argparse
from aiotieba.reviewer import BaseReviewer

async def add_spam_img(filename: str, fname='', note=None):
    async with BaseReviewer('', fname) as reviewer:
        img = cv2.imread(filename, cv2.IMREAD_COLOR)
        if img is None:
            print('获取图片失败')
            exit(1)
        hash = reviewer.compute_imghash(img)
        stem = pathlib.Path(filename).stem
        raw_hash = stem if len(stem) == 40 else None
        if raw_hash is None:
            print('未能获取到40位图床hash，请勿更改文件名')
            exit(1)
        await reviewer.db.add_imghash(hash, raw_hash, permission=-5, note=note or '广告')

async def add_spam_img_url(url: str, fname='', note=None):
    async with BaseReviewer('', fname) as reviewer:
        img = await reviewer.client.get_image(url)
        if img is None:
            print('获取图片失败')
            exit(1)
        hash = reviewer.compute_imghash(img)
        raw_hash = None
        match = re.search(r'(?:pic/item|sign=[0-9a-f]*)/([0-9a-f]{40})\.(?:jpg|png)', url)
        if match:
            raw_hash = match.group(1)
        if raw_hash is None:
            print('未能获取到40位图床hash')
            exit(1)
        await reviewer.db.add_imghash(hash, raw_hash, permission=-5, note=note or '广告')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--file',
        help='图片本地路径，文件名需要为40位hash值'
    )
    parser.add_argument(
        '--url',
        help='图片在百度贴吧的url',
    )
    parser.add_argument(
        '--note',
        help='图片类型备注',
    )
    args = parser.parse_args()
    if args.file:
        asyncio.run(add_spam_img(args.file, 'C语言', args.note))
    elif args.url:
        asyncio.run(add_spam_img_url(args.url, 'C语言', args.note))
    else:
        print(f'usage: {pathlib.Path(__file__).name} [--url image_URL|--file image_filename]')
