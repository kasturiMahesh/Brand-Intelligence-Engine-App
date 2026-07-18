import asyncio
from config.database import init_postgres, init_mongo

async def main():
    await init_postgres()
    await init_mongo()
    print('database initialization complete')

if __name__ == '__main__':
    asyncio.run(main())
