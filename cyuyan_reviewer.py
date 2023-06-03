import argparse
import asyncio
import httpx
import re
from typing import Optional, Union
from enum import Enum

import aiotieba as tb
from aiotieba._logger import LOG

antispammer_url = 'http://127.0.0.1:14930/predict/spam'
antifraud_url = 'http://127.0.0.1:14930/predict/fraud'

class FraudTypes(Enum):
    # 不涉嫌诈骗
    NOT_FRAUD = 0
    # 疑似诈骗
    SUSPECTED_FRAUD = 1
    # 已核实诈骗
    CONFIRMED_FRAUD = 2

def punish_note(violations: int, fruad_type: FraudTypes):
    """
    根据违规记录，返回对应的封禁理由
    Args:
        violations (int): 违规次数
        fruad_type (FraudTypes): 涉嫌诈骗程度
            FraudTypes.NOT_FRAUD: 不涉嫌诈骗
            FraudTypes.SUSPECTED_FRAUD: 疑似诈骗
            FraudTypes.CONFIRMED_FRAUD: 已核实诈骗
    """
    if fruad_type == FraudTypes.SUSPECTED_FRAUD:
        return '疑似诈骗行为，为规避风险删封处理。即日起只允许4级及以上的账号回复接单，4级以下账号接单一律视为涉嫌诈骗，删封处理。'
    elif fruad_type == FraudTypes.CONFIRMED_FRAUD:
        return '经举报核实，此账号存在诈骗行为，予以发言永久删封处罚。如有异议，可向吧务组申诉，并提交相关证据澄清。'
    if violations < 8:
        return '散布代写/接单/辅导类主题帖，或推广网站/课程/群聊等广告行为'
    elif 8 <= violations <= 10:
        return f'散布代写/接单/辅导类主题帖，或推广网站/课程/群聊等广告行为；请注意，你已有{violations}次违规记录，请阅读并遵守吧规。继续违规可能导致永久删封处罚。'
    else:
        return '无视吧规多次散布广告，屡教不改，情节恶劣，予以发言永久删封处罚。'

class MyReviewer(tb.Reviewer):
    def __init__(self, BDUSS_key: str, fname: str):
        super().__init__(BDUSS_key, fname)

        self.thread_checkers = [self.check_blacklist, self.check_thread, self.check_img]
        self.post_checkers = [self.check_blacklist, self.check_fraud, self.check_post, self.check_img]
        self.comment_checkers = [self.check_blacklist, self.check_fraud, self.check_comment]
        # 回贴广告违禁词
        self.post_ad_patterns = [
            re.compile('http://8.136.190.216:8080/ca'),
            re.compile('graves2022'),
            re.compile('昆鹏发卡'),
        ]
        # 诈骗号码黑名单
        self.fraud_patterns = [
            re.compile('1290783771'),
            re.compile('3075922592'),
        ]
        # 二维码链接黑名单
        self.qrcode_patterns = [
            re.compile('weixin.qq.com'),
            re.compile('qm.qq.com'),
        ]
        # 部分例外贴的tid（置顶贴、吧务公告、诈骗举报贴和申诉贴等）
        self.exclude_tids = [
            5550750195, # c语言吧新人引导，入门必看！
            8442248933, # 关于打击诈骗活动的征集意见
        ]

    def time_interval(self):
        """
        每2分钟执行一次检查
        """
        return lambda : 120.0

    async def check_thread(self, thread: tb.Thread) -> Optional[tb.Punish]:
        """检查主题贴是否为广告性质"""
        # 防止误删吧务、置顶贴、加精贴等
        if thread.user.is_bawu or thread.is_top or thread.is_good or thread.tid in self.exclude_tids:
            return
        punish = False
        # 机器学习判断广告内容
        async with httpx.AsyncClient() as client:
            r = await client.post(antispammer_url, data={'text': thread.text})
            if r.text == 'spam':
                punish = True
        if punish:
            if credit := await self.db.get_user_credit(thread.user):
                violations = credit[0] + 1
            else:
                violations = 1
            block_days = 1 if violations >= 3 else 0
            await self.db.add_user_credit(thread.user)
            return tb.Punish(tb.Ops.HIDE, block_days=block_days, note=punish_note(violations, FraudTypes.NOT_FRAUD))

    async def check_post(self, post: tb.Post) -> Optional[tb.Punish]:
        """检查回复中的广告等"""
        # 防止误删
        if post.user.is_bawu or post.tid in self.exclude_tids:
            return
        punish = False
        for pattern in self.post_ad_patterns:
            if pattern.search(post.text):
                punish = True
                break
        if punish:
            if credit := await self.db.get_user_credit(post.user):
                violations = credit[0] + 1
            else:
                violations = 1
            block_days = 1 if violations >= 3 else 0
            await self.db.add_user_credit(post.user)
            return tb.Punish(tb.Ops.DELETE, block_days=block_days, note=punish_note(violations, FraudTypes.NOT_FRAUD))

    async def check_comment(self, comment: tb.Comment) -> Optional[tb.Punish]:
        return
    
    async def check_fraud(self, obj: Union[tb.Post, tb.Comment]) -> Optional[tb.Punish]:
        """检查回复是否涉嫌诈骗"""
        # 防止误删
        if obj.user.is_bawu or obj.tid in self.exclude_tids:
            return
        if isinstance(obj, tb.Post) and obj.is_thread_author:
            return
        for pattern in self.fraud_patterns:
            # 命中诈骗号码黑名单，则确定为诈骗
            if pattern.search(obj.text):
                op = tb.Ops.HIDE if isinstance(obj, tb.Thread) else tb.Ops.DELETE
                await self.db.add_user_credit(obj.user, True)
                return tb.Punish(op, block_days=1, note=punish_note(0, FraudTypes.CONFIRMED_FRAUD))
        # 4级以下的账号接单一律按疑似诈骗处理
        if obj.user.level < 4:
            async with httpx.AsyncClient() as client:
                r = await client.post(antifraud_url, data={'text': obj.text})
                if r.text == 'spam':
                    op = tb.Ops.HIDE if isinstance(obj, tb.Thread) else tb.Ops.DELETE
                    # 疑似诈骗不标记is_fraud=True
                    await self.db.add_user_credit(obj.user)
                    return tb.Punish(op, block_days=1, note=punish_note(0, FraudTypes.SUSPECTED_FRAUD))

    async def check_img(self, obj: Union[tb.Thread, tb.Post, tb.Comment]) -> Optional[tb.Punish]:
        """检查违规图片"""
        punish = False
        for img_content in obj.contents.imgs:
            img = await self.client.get_image(img_content.origin_src)
            if img.size == 0:
                continue
            # 检测二维码
            if self.has_QRcode(img):
                qrcode = self.decode_QRcode(img)
                for p in self.qrcode_patterns:
                    if p.search(qrcode):
                        punish = True
                        LOG.info(f'Possible spam QR code: src={img_content.origin_src}, content={qrcode}')
                        break
                if punish:
                    break
            # 比对违规图片库
            permission = await self.get_imghash(img, hamming_dist=5)
            if permission <= -5:
                punish = True
                phash = self.compute_imghash(img)
                LOG.info(f'Possible spam image: src={img_content.origin_src}, img_hash={img_content.hash}, phash={phash}')
                break
        if punish:
            if credit := await self.db.get_user_credit(obj.user):
                violations = credit[0] + 1
            else:
                violations = 1
            block_days = 1 if violations >= 3 else 0
            op = tb.Ops.HIDE if isinstance(obj, tb.Thread) else tb.Ops.DELETE
            await self.db.add_user_credit(obj.user)
            return tb.Punish(op, block_days=block_days, note=punish_note(violations, FraudTypes.NOT_FRAUD))
    
    async def check_blacklist(self, obj: Union[tb.Thread, tb.Post, tb.Comment]) -> Optional[tb.Punish]:
        """
            以下用户发言一律删封：
            1.违规超过10次
            2.涉嫌诈骗
        """
        # 给黑名单用户在指定贴下申诉的机会
        if obj.tid in self.exclude_tids:
            return
        if credit := await self.db.get_user_credit(obj.user):
            violations, is_fraud = credit
            if violations > 10 or is_fraud:
                op = tb.Ops.HIDE if isinstance(obj, tb.Thread) else tb.Ops.DELETE
                await self.db.add_user_credit(obj.user, is_fraud)
                return tb.Punish(op, block_days=1, note=punish_note(violations, FraudTypes.CONFIRMED_FRAUD if is_fraud else FraudTypes.NOT_FRAUD))

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