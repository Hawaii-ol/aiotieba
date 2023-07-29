# 脚本功能：将严重违规的用户同步到贴吧黑名单（需要吧主权限）
# 包括违规次数超过阈值，以及举报核实诈骗的账号
import __init__
import asyncio
import aiotieba as tb
from cyuyan_reviewer import FraudTypes, MyReviewer

async def main(fname):
    tb.logging.enable_filelog()
    async with MyReviewer('default', fname) as reviewer:
        if not reviewer.is_bazhu:
            print('贴吧黑名单功能需要吧主权限。')
            exit(0)
        uc_list = await reviewer.db.list_user_credits()
        for uc in uc_list:
            if uc.violations >= reviewer.blacklist_violations or uc.fraud_type == FraudTypes.CONFIRMED_FRAUD:
                await reviewer.client.add_bawu_blacklist(fname, uc.user.user_id)

if __name__ == '__main__':
    asyncio.run(main('C语言'))
