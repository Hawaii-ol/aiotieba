# 添加违规图片
import cv2
import pathlib
import asyncio
import argparse
from aiotieba.reviewer import BaseReviewer

async def add_spam_img(filename: str, fname=''):
    async with BaseReviewer('', fname) as reviewer:
        img = cv2.imread(filename, cv2.IMREAD_COLOR)
        hash = reviewer.compute_imghash(img)
        stem = pathlib.Path(filename).stem
        raw_hash = stem if len(stem) == 40 else ''
        await reviewer.db.add_imghash(hash, raw_hash, permission=-5, note='广告')

async def add_spam_img_url(url: str, fname=''):
    async with BaseReviewer('', fname) as reviewer:
        img = await reviewer.client.get_image(url)
        hash = reviewer.compute_imghash(img)
        raw_hash = ''
        await reviewer.db.add_imghash(hash, raw_hash, permission=-5, note='广告')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--file',
        help="图片本地路径"
    )
    parser.add_argument(
        "--url",
        help="图片在百度贴吧的url",
    )
    args = parser.parse_args()
    if args.file:
        asyncio.run(add_spam_img(args.file, 'C语言'))
    elif args.url:
        asyncio.run(add_spam_img_url(args.url, 'C语言'))
    else:
        print(f'usage: {pathlib.Path(__file__).name} [--url image_URL|--file image_filename]')
