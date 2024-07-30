# 脚本功能：导出诈骗用户名单
import __init__
import asyncio
import logging
import pathlib
import re
from aiotieba.logging import get_logger as LOG
from cyuyan_reviewer import MyReviewer, FraudTypes

async def print_frauds(fname):
    frauds = []
    frauds_feat = [] # 特征检测账号
    async with MyReviewer('default', fname) as reviewer:
        feat_id_pattern = re.compile(r'^(1722|1783)\d{6}$')
        for uc in await reviewer.db.list_user_credits():
            if uc.fraud_type == FraudTypes.CONFIRMED_FRAUD:
                if uinfo := await reviewer.client.get_user_info(uc.user.portrait):
                    if feat_id_pattern.match(str(uinfo.user_id)):
                        frauds_feat.append(uinfo)
                    else:
                        frauds.append(uinfo)
    
    frauds.sort(key=lambda u : u.tieba_uid)
    frauds_feat.sort(key=lambda u : u.tieba_uid)

    print('\n以下为已知的诈骗贴吧账号：\n')
    pprint_uinfos(frauds)
    
    print('\n以下为同一诈骗团伙使用的部分贴吧马甲账号（账号特征均高度一致）：')
    pprint_uinfos(frauds_feat)

def pprint_uinfos(users):
    user_name_max = max(len(u.user_name) for u in users)
    nick_name_max = max(len(u.nick_name) for u in users)
    for u in users:
        print(f'用户名：{u.user_name:<{user_name_max}}\t'
              f'昵称：{u.nick_name:<{nick_name_max}}\t'
              f'贴吧ID：{u.tieba_uid}\t'
              f'IP归属地：{u.ip}')

if __name__ == '__main__':
    rules_path = pathlib.Path(__file__).parent.parent / 'antispam' / 'rules'
    print('以下为已知的诈骗号码名单：')
    with open(rules_path / 'fraud.txt', encoding='utf-8') as file:
        l = []
        for line in file:
            line = line.strip()
            if not line:
                continue
            if line.startswith('#'):
                l.sort()
                for line in l:
                    print(line)
                l.clear()
                print(line[1:].strip())
            else:
                l.append(line)
        l.sort()
        for line in l:
            print(line)
    
    LOG().setLevel(logging.CRITICAL)
    asyncio.run(print_frauds('C语言'))
    
    print('\n（什么是用户名、昵称和贴吧ID）')
    print('在贴吧客户端点击某位用户的头像，可以跳转到TA的主页。主页显示的名称即为昵称，昵称下方的ID即为贴吧ID。'
          '用户名可点击右侧的“关于Ta”查看。昵称可以被修改，而用户名和贴吧ID不可修改且唯一。某些账号可能没有用户名。')
    print('\n请各位吧友擦亮眼睛，谨防上当受骗。不要与以上任何账号交流，更不要与它们交易。')
