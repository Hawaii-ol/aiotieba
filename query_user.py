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
        print(f'user_id: {user.user_id}')
        print(f'portrait: {user.portrait}')
        print(f'user_name: {user.user_name}')
        print(f'nick_name: {user.nick_name}')

asyncio.run(main())
