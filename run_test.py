import argparse
import asyncio
import time
from typing import Dict, List, TypedDict

import httpx


class ResponseTimes(TypedDict):
    min: float
    mean: float
    max: float


async def get(client: httpx.AsyncClient, path: str):
    start = time.time()
    response = await client.get(f"http://localhost:8001{path}", timeout=30.0)
    return response, time.time() - start


async def run_concurrent_requests(
    num_requests: int, paths: List[str]
) -> Dict[str, ResponseTimes]:
    results: Dict[str, ResponseTimes] = {}
    async with httpx.AsyncClient() as client:
        responses = []
        for path in paths:
            responses.extend([get(client, path) for _ in range(num_requests)])
        for response, response_time in await asyncio.gather(*responses):
            path = response.url.path
            if path not in results:
                results[path] = {
                    "min": response_time,
                    "mean": response_time,
                    "max": response_time,
                }
            else:
                results[path]["min"] = min(results[path]["min"], response_time)
                results[path]["mean"] += response_time
                results[path]["max"] = max(results[path]["max"], response_time)
        for path in results:
            results[path]["mean"] /= num_requests
    return results


async def run_test(num_requests: int, paths: List[str]):
    print("------ START ------")
    print(f"Running test with {num_requests} requests each to paths: {paths!r}")
    responses = await run_concurrent_requests(num_requests, paths)
    for path, response_times in responses.items():
        print(f"{path}:")
        print(f"Min: {response_times['min']:.2f}")
        print(f"Mean: {response_times['mean']:.2f}")
        print(f"Max: {response_times['max']:.2f}")
    print("------ END ------\n")


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--num-requests", type=int, default=100)
    args = parser.parse_args()

    await run_test(args.num_requests, ["/ping"])
    await run_test(args.num_requests, ["/ping", "/ping-with-async-sleep"])
    await run_test(args.num_requests, ["/count-todos-async", "/ping"])
    await run_test(args.num_requests, ["/count-todos-sync", "/ping"])


if __name__ == "__main__":
    asyncio.run(main())
