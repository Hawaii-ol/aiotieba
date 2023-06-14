import __init__
import sys
import asyncio
import argparse
import aiotieba as tb
from cyuyan_reviewer import FraudTypes, punish_note

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
    async with tb.Reviewer('default', fname) as reviewer:
        if cred_type == 'tieba_uid':
            user = await reviewer.client.tieba_uid2user_info(credential)
        else:
            user = await reviewer.client.get_user_info(credential)
        print('请选择封禁原因：')
        print('[1] 广告')
        print('[2] 疑似诈骗')
        print('[3] 举报核实诈骗')
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
