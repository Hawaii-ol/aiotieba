import sys
import asyncio
import pathlib
import aiotieba as tb

async def main(fname, tid):
    reviewer = tb.Reviewer('', fname)
    if await reviewer.is_tid_hide(tid):
        await reviewer.client.unhide_thread(fname, tid)
    await reviewer.add_id(tid)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(f'usage: {pathlib.Path(sys.argv[0]).name} thread_id')
        print('将指定帖子添加到已审核列表，防止被误删')
        exit(0)
    asyncio.run(main('C语言', sys.argv[1]))
