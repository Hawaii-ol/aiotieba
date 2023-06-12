import __init__
import asyncio
from aiotieba.database import MySQLDB

async def db_init(fname=''):
    db = MySQLDB(fname)
    await db.create_database()

if __name__ == '__main__':
    asyncio.run(db_init('C语言'))
