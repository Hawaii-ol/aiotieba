import asyncio
import aiomysql
import aiotieba
from pathlib import Path
from typing import List
from aiotieba._config import CONFIG

async def collect_alt_uinfo():
    portraits = await collect_alt_portraits()
    async with aiotieba.Client() as client:
        users = [await client.get_user_info(p) for p in portraits]
        users.sort(key=lambda u : u.tieba_uid)
        for u in users:
            print(f'用户名：{u.user_name}\t昵称：{u.nick_name}\t贴吧ID：{u.tieba_uid}')

async def collect_alt_portraits() -> List[str]:
    dbcfg = CONFIG['Database']
    conn_params = {param : dbcfg[param] for param in ('host', 'port', 'user', 'password', 'db')}
    if 'unix_socket' in dbcfg:
        conn_params['unix_socket'] = dbcfg['unix_socket']
    conn = await aiomysql.connect(**conn_params)
    cursor = await conn.cursor()
    await cursor.execute("SELECT `portrait` FROM `user_credit` WHERE `user_id` REGEXP '^(1722|1783)[0-9]{6}$'")
    result = await cursor.fetchall()
    return [r[0] for r in result]

if __name__ == '__main__':
    rules_path = Path(__file__).parent / 'antispam' / 'rules'
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
    
    print('\n以下为同一诈骗团伙使用的部分贴吧马甲账号（账号特征均高度一致）：')
    asyncio.run(collect_alt_uinfo())
    print('\n（什么是用户名、昵称和贴吧ID）')
    print('在贴吧客户端点击某位用户的头像，可以跳转到TA的主页。主页显示的名称即为昵称，昵称下方的ID即为客户端贴吧ID。'
          '用户名可点击右侧的“关于Ta”查看。昵称可以被修改，而用户名和贴吧ID不可修改且唯一。')
    print('\n请各位吧友擦亮眼睛，谨防上当受骗。不要相信以上任何账号的狡辩。')
