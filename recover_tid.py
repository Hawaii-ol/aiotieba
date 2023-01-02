import sys
import time
import asyncio
import pathlib
import aiotieba as tb

async def main(fname, tid):
    async with tb.Reviewer('default', fname) as reviewer:
        await reviewer.client.unhide_thread(fname, tid)
        # 无法直接获取指定tid的详细信息，获取当前时间戳作为last_edit
        # 当前时间戳一定晚于帖子的实际发布时间，因此下一次检查时loop_handle_thread将会自动修正last_edit
        now = int(time.time())
        await reviewer.add_id(tid, id_last_edit=now)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(f'usage: {pathlib.Path(sys.argv[0]).name} thread_id')
        print('恢复指定帖子的屏蔽状态，并添加到已审核列表，防止再次误删')
        exit(0)
    asyncio.run(main('C语言', sys.argv[1]))
