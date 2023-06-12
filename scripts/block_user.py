import __init__
import sys
import asyncio
import aiotieba as tb
from cyuyan_reviewer import FraudTypes, punish_note

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
        print('请选择封禁原因：')
        print('1.广告')
        print('2.疑似诈骗')
        print('3.举报核实诈骗')
        reason = int(input())
        if reason in [1, 2, 3]:
            if credit := await reviewer.db.get_user_credit(user):
                violations = credit[0] + 1
            else:
                violations = 1
            if reason == 1:
                fraud_type = FraudTypes.NOT_FRAUD
            elif reason == 2:
                fraud_type = FraudTypes.SUSPECTED_FRAUD
            else:
                fraud_type = FraudTypes.CONFIRMED_FRAUD
            note = punish_note(violations, fraud_type)
            print(note)
            await reviewer.db.add_user_credit(user, fraud_type == FraudTypes.CONFIRMED_FRAUD)
            await reviewer.block(user.portrait, day=1, reason=note)
        else:
            print('无效选项')

if __name__ == '__main__':
    asyncio.run(main('C语言'))
