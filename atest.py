import asyncio


# coroutine function
async def main():
    print("hello world")
     
		await asyncio.sleep(0)
		print("")

# Run
asyncio.run(main())
