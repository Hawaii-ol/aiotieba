import argparse
import asyncio
import httpx
import re
import pathlib
from typing import Optional, Union, List

import aiotieba as tb
from aiotieba._config import CONFIG
from aiotieba._logging import get_logger as LOG
from aiotieba.database import FraudTypes

antispammer_url = 'http://127.0.0.1:14930/predict/spam'
antifraud_url = 'http://127.0.0.1:14930/predict/fraud'

class MyReviewer(tb.Reviewer):
    def __init__(self, BDUSS_key: str, fname: str):
        super().__init__(BDUSS_key, fname)
        bawu_config = CONFIG['Bawu']
        self.is_bazhu = bawu_config.get('is_bazhu', False)
        self.blacklist_violations = bawu_config.get('blacklist_violations', 6)

        self.thread_checkers = [self.check_blacklist, self.check_thread, self.check_img]
        self.post_checkers = [self.check_blacklist, self.check_fraud, self.check_post, self.check_img]
        self.comment_checkers = [self.check_blacklist, self.check_fraud, self.check_comment]

        rules_path = pathlib.Path(__file__).parent / 'antispam' / 'rules'
        # 加载回贴违禁词
        self.post_ad_patterns = self._parse_rule(rules_path / 'post_ad.txt')
        # 加载诈骗号码黑名单
        self.fraud_patterns = self._parse_rule(rules_path / 'fraud.txt')
        # 加载二维码链接黑名单
        self.qrcode_patterns = self._parse_rule(rules_path / 'qrcode.txt')
        # 部分例外贴的tid（置顶贴、吧务公告、诈骗举报贴和申诉贴等）
        self.exclude_tids = [int(tid) for tid in self._parse_rule(rules_path / 'exclude_tids.txt', False)]
    
    def _parse_rule(self, filename, regex=True) -> List[re.Pattern]:
        patterns = []
        with open(filename, encoding='utf-8') as file:
            for line in file:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if regex:
                    patterns.append(re.compile(line))
                else:
                    patterns.append(line)
        return patterns

    def time_interval(self):
        """
        每2分钟执行一次检查
        """
        return lambda : 120.0
    
    def punish_note(self, violations: int, fraud_type: FraudTypes):
        """
        根据违规记录，返回对应的封禁理由
        Args:
            violations (int): 违规次数
            fruad_type (FraudTypes): 涉嫌诈骗情况
                FraudTypes.NOT_FRAUD: 不涉嫌诈骗
                FraudTypes.SUSPECTED_FRAUD: 疑似诈骗
                FraudTypes.CONFIRMED_FRAUD: 已核实诈骗
        """
        if fraud_type == FraudTypes.SUSPECTED_FRAUD:
            return '风控检测疑似诈骗账号，为避免风险删封处理。'
        elif fraud_type == FraudTypes.CONFIRMED_FRAUD:
            return '经举报核实，此账号或相关账号存在诈骗行为，予以发言永久删封处罚。'
        if violations <= 3:
            return '发布违法违规内容或垃圾广告。'
        elif violations < self.blacklist_violations:
            return f'发布违法违规内容或垃圾广告。你已有{violations}次违规记录，请阅读并遵守吧规。继续违规可能导致永久删封处罚。'
        else:
            return '多次发布违法违规内容或垃圾广告，屡教不改，藐视吧规，予以发言永久删封处罚。'

    def make_punish(self, op: tb.Ops, violations: int, fraud_type: FraudTypes) -> tb.Punish:
        """
        生成处罚 (punish对象)
        Args:
            op (tb.Ops): 处罚类型(删贴、隐藏)
            violations (int): 违规次数
            fruad_type (FraudTypes): 涉嫌诈骗情况
        """
        note = self.punish_note(violations, fraud_type)
        max_days = 10 if self.is_bazhu else 1
        if fraud_type == FraudTypes.CONFIRMED_FRAUD:
            days = min(10, max_days)
        elif violations == 1: # 初次豁免
            days = 0
        elif violations <= 3:
            days = 1
        elif violations < self.blacklist_violations - 1: # 拉黑前最后一次封禁为10天
            days = min(3, max_days)
        else:
            days = min(10, max_days)
        return tb.Punish(op, block_days=days, note=note)

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
            uc = await self.db.get_user_credit(thread.user)
            violations = uc.violations + 1 if uc else 1
            await self.db.add_user_credit(thread.user, FraudTypes.NOT_FRAUD)
            return self.make_punish(tb.Ops.DELETE, violations, FraudTypes.NOT_FRAUD)

    async def check_post(self, post: tb.Post) -> Optional[tb.Punish]:
        """检查回复中的违禁词"""
        # 防止误删
        if post.user.is_bawu or post.tid in self.exclude_tids:
            return
        punish = False
        for pattern in self.post_ad_patterns:
            if pattern.search(post.text):
                punish = True
                break
        if punish:
            uc = await self.db.get_user_credit(post.user)
            violations = uc.violations + 1 if uc else 1
            await self.db.add_user_credit(post.user, FraudTypes.NOT_FRAUD)
            return self.make_punish(tb.Ops.DELETE, violations, FraudTypes.NOT_FRAUD)

    async def check_comment(self, comment: tb.Comment) -> Optional[tb.Punish]:
        return

    async def check_fraud(self, obj: Union[tb.Post, tb.Comment]) -> Optional[tb.Punish]:
        """检查回复是否涉嫌诈骗"""
        # 防止误删
        if obj.user.is_bawu or obj.tid in self.exclude_tids or obj.is_thread_author:
            return
        punish = False
        fraud_type = FraudTypes.NOT_FRAUD
        for _ in range(1):
            # 检查黑名单
            for pattern in self.fraud_patterns:
                if pattern.search(obj.text):
                    punish = True
                    fraud_type = FraudTypes.CONFIRMED_FRAUD
                    break
            if punish:
                break
            # 特征检测一批马甲账号
            # 1.贴吧等级<4
            # 2.1722或1783开头的10位user_id
            # 3.用户名为4-6个汉字（这条不一定）
            # 4.性别为女（有时客户端会返回未知）
            # 5.ip属地为内蒙古或上海
            if (obj.user.level < 4 and
                re.match(r'^(1722\d{6})|(1783\d{6})$', str(obj.user.user_id)) and
                # re.match(r'^[\u4e00-\u9fa5]{4,6}$', obj.user.user_name) and
                obj.user.gender != 1 and
                obj.user.ip in ('内蒙古', '上海')
            ):
                LOG().info(f'特征检测: {repr(obj.user)}')
                punish = True
                fraud_type = FraudTypes.CONFIRMED_FRAUD
                break
            # 检查发言是否为加q私聊等接单性质
            async with httpx.AsyncClient() as client:
                r = await client.post(antifraud_url, data={'text': obj.text})
                if r.text == 'spam':
                    # 7级以下的账号一律按疑似诈骗处理
                    if obj.user.level < 7:
                        punish = True
                        fraud_type = FraudTypes.SUSPECTED_FRAUD
                        break
                    # 已标记疑似诈骗的账号
                    uc = await self.db.get_user_credit(obj.user)
                    if uc and uc.fraud_type == FraudTypes.SUSPECTED_FRAUD:
                        punish = True
                        fraud_type = FraudTypes.SUSPECTED_FRAUD
                        break
        if punish:
            uc = await self.db.get_user_credit(obj.user)
            violations = uc.violations + 1 if uc else 1
            await self.db.add_user_credit(obj.user, fraud_type)
            return self.make_punish(tb.Ops.DELETE, violations, fraud_type)

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
                        LOG().info(f'Possible spam QR code: src={img_content.origin_src}, content={qrcode}')
                        break
                if punish:
                    break
            # 比对违规图片库
            permission = await self.get_imghash(img, hamming_dist=5)
            if permission <= -5:
                punish = True
                phash = self.compute_imghash(img)
                LOG().info(f'Possible spam image: src={img_content.origin_src}, img_hash={img_content.hash}, phash={phash}')
                break
        if punish:
            uc = await self.db.get_user_credit(obj.user)
            violations = uc.violations + 1 if uc else 1
            await self.db.add_user_credit(obj.user, FraudTypes.NOT_FRAUD)
            return self.make_punish(tb.Ops.DELETE, violations, FraudTypes.NOT_FRAUD)
    
    async def check_blacklist(self, obj: Union[tb.Thread, tb.Post, tb.Comment]) -> Optional[tb.Punish]:
        """
        以下用户发言一律删封：
        1.违规次数达到或超过blacklist_violations
        2.经举报核实诈骗
        """
        # 给黑名单用户在指定贴下申诉的机会
        if obj.tid in self.exclude_tids:
            return
        if uc := await self.db.get_user_credit(obj.user):
            if uc.violations >= self.blacklist_violations or uc.fraud_type == FraudTypes.CONFIRMED_FRAUD:
                await self.db.add_user_credit(obj.user, uc.fraud_type)
                return self.make_punish(tb.Ops.DELETE, uc.violations, uc.fraud_type)

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