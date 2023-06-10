import sys
import asyncio
import aiotieba


async def main():
    async with aiotieba.Client('default') as client:
        if len(sys.argv) == 1:
            credential = input('Enter {id|portrait|user_name}: ')
        else:
            credential = sys.argv[1]
        try:
            credential = int(credential)
        except ValueError:
            pass
        user = await client.get_user_info(credential)
        print_uinfo(user)

def print_uinfo(user):
    print(f'user_id: {user.user_id}')
    print(f'portrait: {user.portrait}')
    print(f'用户名: {user.user_name}')
    print(f'昵称: {user.nick_name}')
    print(f'性别: {("未知", "男", "女")[user.gender]} (gender: {user.gender})')
    print(f'吧龄(年): {user.age}')
    print(f'发贴数(主题贴+回复): {user.post_num}')
    print(f'粉丝数: {user.fan_num}')
    print(f'关注数: {user.follow_num}')
    print(f'ip归属地: {user.ip}')

if __name__ == '__main__':
    asyncio.run(main())
