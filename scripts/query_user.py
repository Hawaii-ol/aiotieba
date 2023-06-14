import __init__
import asyncio
import aiotieba
import argparse


async def main(credential, cred_type=None):
    if not cred_type:
        try:
            credential = int(credential)
            print('Credential type not specified and what you enter seems to be an integer. '
                  'Please select the credential type you would like to query by:')
            print('[1] user_id')
            print('[2] user_name')
            print('[3] tieba_uid')
            choice = int(input())
            if choice in [1, 2, 3]:
                if choice == 2:
                    credential = str(credential)
                elif choice == 3:
                    cred_type = 'tieba_uid'
            else:
                print('Invalid choice.')
                exit(1)
        except ValueError:
            pass
    elif cred_type in ['user_id', 'tieba_uid']:
        try:
            credential = int(credential)
        except ValueError:
            print(f"{cred_type} must be an integer, not '{credential}'.")
            exit(1)
    async with aiotieba.Client('default') as client:
        if cred_type == 'tieba_uid':
            user = await client.tieba_uid2user_info(credential)
            user = await client.get_user_info(user.portrait)
        else:
            user = await client.get_user_info(credential)
        print_uinfo(user)

def print_uinfo(user):
    print(f'user_id: {user.user_id}')
    print(f'portrait: {user.portrait}')
    print(f'贴吧ID: {user.tieba_uid}')
    print(f'用户名: {user.user_name}')
    print(f'昵称: {user.nick_name}')
    print(f'性别: {("未知", "男", "女")[user.gender]} (gender: {user.gender})')
    print(f'吧龄(年): {user.age}')
    print(f'发贴数(主题贴+回复): {user.post_num}')
    print(f'粉丝数: {user.fan_num}')
    print(f'关注数: {user.follow_num}')
    print(f'ip归属地: {user.ip}')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='query user info by several credential types')
    parser.add_argument(
        '-t','--cred_type',
        help='credential type',
        choices=['user_id', 'user_name', 'portrait', 'tieba_uid'],
    )
    parser.add_argument('credential')
    args = parser.parse_args()
    asyncio.run(main(args.credential, args.cred_type))
