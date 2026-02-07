import asyncio

async def myfun(name, delay):
    print(f"Task {name} started")
    await asyncio.sleep(delay)
    print(f"Task {name} finished")

async def main():
    await asyncio.gather(
        myfun("A", 2),
        myfun("B", 1),
        myfun("C", 3),
    )

asyncio.run(main())
