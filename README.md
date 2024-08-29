This repo demonstrates that using SQLAlchemy's asyncio support with a FastAPI webserver actually ends up blocking the ASGI event loop and delaying all requests.

## Setup

1. Clone this repo.
2. Install [`uv`](https://github.com/astral-sh/uv?tab=readme-ov-file#installation).
2. Run `uv sync` to install the dependencies (this will create a local `.venv` directory).
3. Run `source .venv/bin/activate` to activate the virtual environment.
4. Run `alembic upgrade head` to create the SQLite database and load 1,000,000 rows of todos.
5. Run `fastapi run --port 8001 src/fastapi_sqlalchemy_slowness/main.py` to start the FastAPI server (you can also run in dev mode with `fastapi dev --port 8001 src/fastapi_sqlalchemy_slowness/main.py`)
6. In another terminal, run `python run_test.py`


## Results

On my 2022 MacBook Air (M2, 24GB RAM, Sonoma 14.6.1), `run_test.py` outputs the following results:

### ✅ Single Request

```txt
------ START ------
Running test with 100 requests each to paths: ['/ping']
/ping:
Min: 0.02
Mean: 0.04
Max: 0.05
------ END ------
```

This a control test making 100 requests to just `/ping` which doesn't do much. FastAPI is fast and returns <0.1s.


### ✅ Concurrent requests to a non-blocking endpoint

```txt
------ START ------
Running test with 100 requests each to paths: ['/ping', '/ping-with-async-sleep']
/ping:
Min: 0.11
Mean: 0.21
Max: 0.25
/ping-with-async-sleep:
Min: 10.18
Mean: 10.23
Max: 10.25
------ END ------
```

In this test, we make 100 separate concurrent requests to `/ping` and `/ping-with-async-sleep`. The only insight here is that `/ping` is clearly not slowed down by `/ping-with-async-sleep` as it uses `asyncio.sleep` to simulate a non-blocking operation. There is however a slight performance penalty on `/ping` due to the overhead of managing the concurrent requests.


### ⚠️ PROBLEM: Concurrent requests to a SQLAlchemy AsyncSession endpoint ⚠️

```txt
------ START ------
Running test with 100 requests each to paths: ['/count-todos-async', '/ping']
/count-todos-async:
Min: 9.70
Mean: 12.18
Max: 12.69
/ping:
Min: 9.70
Mean: 12.40
Max: 12.61
------ END ------
```

In this test, we send 100 concurrent requests to `/count-todos-async` and `/ping`. The `/count-todos-async` endpoint uses SQLAlchemy's `asyncio` support to query the database and run a slightly slow running query. The results show that the `/ping` endpoint is slowed down by the `/count-todos-async` endpoint.  I assume this is because the ASGI event loop is blocked by the SQLAlchemy query (despite using `AsyncSession` and an async DB driver `aiosqlite`).


### ✅ Concurrent requests to a SQLAlchemy Session endpoint

```txt
------ START ------
Running test with 100 requests each to paths: ['/count-todos-sync', '/ping']
/count-todos-sync:
Min: 1.93
Mean: 7.78
Max: 13.39
/ping:
Min: 1.93
Mean: 2.41
Max: 2.65
------ END ------
```

In this test, we send 100 concurrent requests to `/count-todos-sync` and `/ping`. Here `/count-todos-sync` is not an `async def` endpoint and so FastAPI will run this in a threadpool to avoid blocking the event loop. Annoyingly, we actually see a performance increase here despite the fact that we are not using the `asyncio` support in SQLAlchemy.