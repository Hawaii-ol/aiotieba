# 实用工具

## 签到

```python
import asyncio
from typing import List

import aiotieba as tb


class NeedRetry(RuntimeError):
    pass


def handle_exce(err: tb.exception.TiebaServerError) -> None:
    if isinstance(err, tb.exception.TiebaServerError):
        if err.code in [160002, 340006]:
            # 已经签过或吧被屏蔽
            return

    raise NeedRetry()


async def sign(BDUSS_key: str, *, retry_times: int = 0) -> None:
    """
    各种签到

    Args:
        BDUSS_key (str): 用于创建客户端
        retry_times (int, optional): 重试次数. Defaults to 0.
    """

    async with tb.Client(BDUSS_key) as client:
        tb.exception.exc_handlers[client.sign_forum] = handle_exce

        # 成长等级签到
        for _ in range(retry_times):
            await asyncio.sleep(1.0)
            if await client.sign_growth():
                break
        # 分享任务
        for _ in range(retry_times):
            await asyncio.sleep(1.0)
            if await client.sign_growth_share():
                break
        # 虚拟形象点赞
        for _ in range(retry_times):
            await asyncio.sleep(1.0)
            if await client.agree_vimage(6050811555):
                break
        # 互关任务
        for _ in range(retry_times):
            await asyncio.sleep(1.0)
            success = False
            success = await client.unfollow_user('tb.1.2fc1394a.ukuFqA26BTuAeXqYr1Nmwg')
            if not success:
                continue
            success = await client.follow_user('tb.1.2fc1394a.ukuFqA26BTuAeXqYr1Nmwg')
            if not success:
                continue
            if success:
                break
        # 签到
        retry_list: List[str] = []
        for pn in range(1, 9999):
            forums = await client.get_self_follow_forums(pn)
            retry_list += [forum.fname for forum in forums]
            if not forums.has_more:
                break
        for _ in range(retry_times + 1):
            new_retry_list: List[str] = []
            for fname in retry_list:
                try:
                    await client.sign_forum(fname)
                except NeedRetry:
                    new_retry_list.append(fname)
                await asyncio.sleep(1.0)
            if not new_retry_list:
                break
            retry_list = new_retry_list


async def main() -> None:
    await sign("default", retry_times=3)
    await sign("backup", retry_times=3)


asyncio.run(main())
```

## 将个人主页的帖子全部设为隐藏

```python
import asyncio

import aiotieba as tb


async def main() -> None:
    async with tb.Client("default") as client:
        # 海象运算符(:=)会在创建threads变量并赋值的同时返回该值，方便while语句检查其是否为空
        # 更多信息请搜索“Python海象运算符”
        while threads := await client.get_self_public_threads():
            await asyncio.gather(*[client.set_thread_private(thread.fid, thread.tid, thread.pid) for thread in threads])


asyncio.run(main())
```

## 屏蔽贴吧，使它们不再出现在你的首页推荐里

```python
import asyncio

import aiotieba as tb


async def main() -> None:
    async with tb.Client("default") as client:
        await asyncio.gather(
            *[
                client.dislike_forum(fname)
                for fname in [
                    "贴吧名A",
                    "贴吧名B",
                    "贴吧名C",
                ]  # 把你要屏蔽的贴吧名填在这个列表里
            ]
        )


asyncio.run(main())
```

## 解除多个贴吧的屏蔽状态

```python
import asyncio

import aiotieba as tb


async def main() -> None:
    async with tb.Client("default") as client:
        # 此列表用于设置例外
        # 将你希望依然保持屏蔽的贴吧名填在这个列表里
        preserve_fnames = [
            "保持屏蔽的贴吧名A",
            "保持屏蔽的贴吧名B",
            "保持屏蔽的贴吧名C",
        ]
        while 1:
            forums = await client.get_dislike_forums()
            await asyncio.gather(
                *[client.undislike_forum(forum.fid) for forum in forums if forum.fname not in preserve_fnames]
            )
            if not forums.has_more:
                break


asyncio.run(main())
```

## 拒绝所有解封申诉

```python
import asyncio

import aiotieba as tb


async def main() -> None:
    async with tb.Client("default") as client:
        fname = "待拒绝申诉的贴吧名"
        while appeals := await client.get_unblock_appeals(fname, rn=30):
            await client.handle_unblock_appeals(fname, [a.appeal_id for a in appeals])


asyncio.run(main())
```

## 清空default账号的粉丝列表（无法复原的危险操作，请谨慎使用！）

```python
import asyncio

import aiotieba as tb


async def main() -> None:
    async with tb.Client("default") as client:
        while fans := await client.get_fans():
            await asyncio.gather(*[client.remove_fan(fan.user_id) for fan in fans])


asyncio.run(main())
```

## 清除default账号的所有历史回复（无法复原的危险操作，请谨慎使用！）

```python
import asyncio

import aiotieba as tb


async def main() -> None:
    async with tb.Client('default') as client:
        while posts_list := await client.get_self_posts():
            await asyncio.gather(*[client.del_post(post.fid, post.tid, post.pid) for posts in posts_list for post in posts])


asyncio.run(main())
```
