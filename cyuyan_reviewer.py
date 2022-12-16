import argparse
import asyncio
import aiohttp
import re
from typing import Optional, Union

import aiotieba as tb

antispammer_url = 'http://127.0.0.1:14930/predict'

class MyReviewer(tb.Reviewer):
    def __init__(self, BDUSS_key: str, fname: str):
        super().__init__(BDUSS_key, fname)

        self.thread_checkers = [self.check_thread]
        self.post_checkers = [self.check_post, self.check_text]
        self.comment_checkers = [self.check_comment, self.check_text]
        self.post_ad_patterns = [
            re.compile('http://8.136.190.216:8080/ca'),
        ]

    def time_interval(self):
        return lambda : 300.0

    async def check_thread(self, thread: tb.Thread) -> Optional[tb.Punish]:
        if not (user := thread.user):
            return
        punish = False

        # 机器学习判断广告内容
        if not thread.is_top and not thread.is_good:
            async with aiohttp.ClientSession() as session:
                async with session.post(url=antispammer_url, data={'text': thread.text}) as resp:
                    result = await resp.text()
                    if result == 'spam':
                        punish = True
        if punish:
            violations = await self.db.get_user_violations(thread.user)
            block_days = 1 if violations + 1 >= 3 else 0
            await self.db.add_user_credit(thread.user)
            return tb.Punish(tb.Ops.HIDE, block_days=block_days, note='散布广告')

    async def check_post(self, post: tb.Post) -> Optional[tb.Punish]:
        punish = False
        for pattern in self.post_ad_patterns:
            if pattern.search(post.text):
                punish = True
        if punish:
            violations = await self.db.get_user_violations(post.user)
            block_days = 1 if violations + 1 >= 3 else 0
            await self.db.add_user_credit(post.user)
            return tb.Punish(tb.Ops.DELETE, block_days=block_days, note='散布广告')

    async def check_comment(self, comment: tb.Comment) -> Optional[tb.Punish]:
        return

    async def check_text(self, obj: Union[tb.Thread, tb.Post, tb.Comment]) -> Optional[tb.Punish]:
        return

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--no_dbg",
        help="调试模式默认开启以避免误操作 生产环境下使用该选项将其关闭",
        action="store_true",
    )
    args = parser.parse_args()

    async def main():
        async with MyReviewer('default', 'C语言') as reviewer:
            if args.no_dbg:
                await reviewer.review_loop()
            else:
                await reviewer.review_debug()

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass