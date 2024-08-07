# 脚本功能：恢复被屏蔽/删除的主题贴和回复贴，并加入到缓存记录，防止再次误删
import __init__
import time
import asyncio
import argparse
import aiotieba as tb

async def recover_tid(fname, tid, unhide=False):
    async with tb.Reviewer('default', fname) as reviewer:
        if unhide:
            await reviewer.client.unhide_thread(fname, tid)
        else:
            await reviewer.client.recover_thread(fname, tid)
        # 无法直接获取指定tid的详细信息，获取当前时间戳作为last_edit
        # 当前时间戳一定晚于帖子的实际发布时间，因此下一次检查时loop_handle_thread将会自动修正last_edit
        now = int(time.time())
        await reviewer.add_id(tid, id_last_edit=now)

async def recover_pid(fname, pid):
    async with tb.Reviewer('default', fname) as reviewer:
        await reviewer.client.recover_post(fname, pid=pid)
        await reviewer.add_id(pid)

if __name__ == '__main__':
    tb.logging.enable_filelog()
    parser = argparse.ArgumentParser(
        description='恢复被删除或屏蔽的主题贴/回复贴/楼中楼，并添加到已审核列表，防止再次误删',
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        '-t', '--tid',
        help='被删除或屏蔽的主题贴的tid',
    )
    group.add_argument(
        '-p', '--pid',
        help='被删除的回复贴或楼中楼的pid',
    )
    parser.add_argument(
        '--unhide',
        default=False,
        action='store_true',
        help='恢复被屏蔽的主题贴'
    )
    fname = 'C语言'
    args = parser.parse_args()
    if args.tid:
        asyncio.run(recover_tid('C语言', args.tid, args.unhide))
    elif args.pid:
        asyncio.run(recover_pid('C语言', args.pid))
