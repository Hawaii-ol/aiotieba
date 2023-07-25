# 脚本功能：封禁用户
import __init__
import asyncio
import argparse
import aiotieba as tb
from cyuyan_reviewer import FraudTypes, MyReviewer

async def main(fname, credential, cred_type=None):
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
    
    async with MyReviewer('default', fname) as reviewer:
        if cred_type == 'tieba_uid':
            user = await reviewer.client.tieba_uid2user_info(credential)
        else:
            user = await reviewer.client.get_user_info(credential)
        print('请选择封禁原因：')
        print('[1] 违法违规内容或垃圾广告')
        print('[2] 疑似诈骗')
        print('[3] 举报核实诈骗')
        try:
            reason = int(input())
            if reason not in [1, 2, 3]:
                raise ValueError
            uc = await reviewer.db.get_user_credit(user)
            violations = uc.violations + 1 if uc else 1
            fraud_type = FraudTypes(reason - 1)
            punish = reviewer.make_punish(tb.Ops.NORMAL, violations, fraud_type)
            note = punish.note
            print(note)
            await reviewer.db.add_user_credit(user, fraud_type)
            await reviewer.block(user.portrait, day=punish.block_days, reason=note)
        except ValueError:
            print('Invalid choice.')
            exit(1)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-t','--cred_type',
        help='credential type',
        choices=['user_id', 'user_name', 'portrait', 'tieba_uid'],
    )
    parser.add_argument('credential')
    args = parser.parse_args()
    asyncio.run(main('C语言', args.credential, args.cred_type))
