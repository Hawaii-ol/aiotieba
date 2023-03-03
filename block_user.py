import sys
import asyncio
import aiotieba as tb

def punish_note(violations: int):
    """
    根据违规次数，返回对应的封禁理由
    """
    if violations < 8:
        return '散布代写/接单/辅导类主题帖，或推广网站/产品/群聊等广告行为'
    elif 8 <= violations <= 10:
        return f'散布代写/接单/辅导类主题帖，或推广网站/产品/群聊等广告行为；请注意，你已有{violations}次违规记录，请阅读并遵守吧规。继续违规可能导致永久删封处罚。'
    else:
        return '无视吧规多次散布广告，屡教不改，情节恶劣，予以发言永久删封处罚。'

async def main(fname):
    async with tb.Reviewer('default', fname) as reviewer:
        if len(sys.argv) == 1:
            credential = input('Enter {id|portrait|user_name}: ')
        else:
            credential = sys.argv[1]
        try:
            credential = int(credential)
        except ValueError:
            pass
        user = await reviewer.client.get_user_info(credential)
        violations = await reviewer.db.get_user_violations(user) + 1
        note = punish_note(violations)
        await reviewer.db.add_user_credit(user)
        await reviewer.block(user.portrait, day=1, reason=note)

if __name__ == '__main__':
    asyncio.run(main('C语言'))
