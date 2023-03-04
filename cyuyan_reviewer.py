import argparse
import asyncio
import httpx
import re
from typing import Optional, Union

import aiotieba as tb
from aiotieba._logger import LOG

antispammer_url = 'http://127.0.0.1:14930/predict'

class MyReviewer(tb.Reviewer):
    def __init__(self, BDUSS_key: str, fname: str):
        super().__init__(BDUSS_key, fname)

        self.thread_checkers = [self.check_blacklist, self.check_thread, self.check_img]
        self.post_checkers = [self.check_blacklist, self.check_post, self.check_img]
        self.comment_checkers = [self.check_comment]
        self.post_ad_patterns = [
            re.compile('http://8.136.190.216:8080/ca'),
            re.compile('867056058'),
            re.compile('1259845250'),
            re.compile('graves2022'),
            re.compile('❻❼❾❸❹❾❻'),
            re.compile('昆鹏发卡'),
        ]

    def time_interval(self):
        """
        每3分钟执行一次检查
        """
        return lambda : 180.0
    
    def punish_note(self, violations: int):
        """
        根据违规次数，返回对应的封禁理由
        """
        if violations < 8:
            return '散布代写/接单/辅导类主题帖，或推广网站/产品/群聊等广告行为'
        elif 8 <= violations <= 10:
            return f'散布代写/接单/辅导类主题帖，或推广网站/产品/群聊等广告行为；请注意，你已有{violations}次违规记录，请阅读并遵守吧规。继续违规可能导致永久删封处罚。'
        else:
            return '无视吧规多次散布广告，屡教不改，情节恶劣，予以发言永久删封处罚。'

    async def check_thread(self, thread: tb.Thread) -> Optional[tb.Punish]:
        punish = False
        # 机器学习判断广告内容
        if not thread.is_top and not thread.is_good:
            async with httpx.AsyncClient() as client:
                r = await client.post(antispammer_url, data={'text': thread.text})
                if r.text == 'spam':
                    punish = True
        if punish:
            violations = await self.db.get_user_violations(thread.user) + 1
            block_days = 1 if violations >= 3 else 0
            await self.db.add_user_credit(thread.user)
            return tb.Punish(tb.Ops.HIDE, block_days=block_days, note=self.punish_note(violations))

    async def check_post(self, post: tb.Post) -> Optional[tb.Punish]:
        punish = False
        for pattern in self.post_ad_patterns:
            if pattern.search(post.text):
                punish = True
        if punish:
            violations = await self.db.get_user_violations(post.user) + 1
            block_days = 1 if violations >= 3 else 0
            await self.db.add_user_credit(post.user)
            return tb.Punish(tb.Ops.DELETE, block_days=block_days, note=self.punish_note(violations))

    async def check_comment(self, comment: tb.Comment) -> Optional[tb.Punish]:
        return

    async def check_img(self, obj: Union[tb.Thread, tb.Post, tb.Comment]) -> Optional[tb.Punish]:
        # 判断违规图片
        punish = False
        for img_content in obj.contents.imgs:
            img = await self.client.get_image(img_content.origin_src)
            if img.size == 0:
                continue
            permission = await self.get_imghash(img, hamming_dist=5)
            if permission <= -5:
                punish = True
                phash = self.compute_imghash(img)
                LOG.info(f'Possible spam image: src={img_content.origin_src}, img_hash={img_content.hash}, phash={phash}')
                break
        if punish:
            violations = await self.db.get_user_violations(obj.user) + 1
            block_days = 1 if violations >= 3 else 0
            op = tb.Ops.HIDE if isinstance(obj, tb.Thread) else tb.Ops.DELETE
            await self.db.add_user_credit(obj.user)
            return tb.Punish(op, block_days=block_days, note=self.punish_note(violations))
    
    async def check_blacklist(self, obj: Union[tb.Thread, tb.Post, tb.Comment]) -> Optional[tb.Punish]:
        # 违规超过10次的惯犯发言一律删封
        violations = await self.db.get_user_violations(obj.user)
        if violations > 10:
            op = tb.Ops.HIDE if isinstance(obj, tb.Thread) else tb.Ops.DELETE
            await self.db.add_user_credit(obj.user)
            return tb.Punish(op, block_days=1, note=self.punish_note(violations))

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