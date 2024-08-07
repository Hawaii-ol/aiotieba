import pytest

import aiotieba as tb


@pytest.mark.flaky(reruns=3, reruns_delay=2.0)
@pytest.mark.asyncio
async def test_Recovers(client: tb.Client):
    recovers = await client.get_recovers(21841105)

    ##### Recover #####
    recover = recovers[0]
    assert recover.tid > 0
    assert recover.op_user_name != ''
