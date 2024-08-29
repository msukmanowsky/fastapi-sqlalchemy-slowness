import asyncio
import logging

import sqlalchemy as sa
from fastapi import FastAPI

from .dependencies import AsyncDBSessionDep, SyncDBSessionDep
from .models import Todo

logger = logging.getLogger("fastapi_sqlalchemy_slowness")
logger.setLevel(logging.INFO)
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)
stream_handler.setFormatter(
    logging.Formatter(
        "%(asctime)s [%(processName)s: %(process)d] [%(threadName)s: %(thread)d] [%(levelname)s] %(name)s: %(message)s"
    )
)
logger.addHandler(stream_handler)

app = FastAPI()


class TimingMiddleware:
    def __init__(self, app: FastAPI):
        self.app = app

    async def __call__(self, scope, receive, send):
        import time

        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start = time.time()
        await self.app(scope, receive, send)
        method = scope["method"]
        path = scope["path"]
        logger.info(
            "%(method)r %(path)s took %(time).2fs",
            {
                "method": method,
                "path": path,
                "time": time.time() - start,
            },
        )


# Uncomment to see timing of routes
# app.add_middleware(TimingMiddleware)


@app.get("/ping")
async def ping():
    return {"message": "pong"}


@app.get("/ping-with-async-sleep")
async def ping_with_async_sleep():
    await asyncio.sleep(10)
    return {"message": "pong"}


completed_at_status = sa.case(
    (Todo.completed_at.is_(None), "not_completed"),
    else_="completed",
)
count_todos_query = sa.select(
    completed_at_status.label("completed_at_status"),
    sa.func.count(Todo.id).label("count"),
).group_by(completed_at_status)


@app.get("/count-todos-async")
async def count_todos_async(db_session: AsyncDBSessionDep):
    # Since this route is defined with `async def`, it'll run in an asyncio
    # event loop and, will end up blocking the loop slowing down other requests

    result = (await db_session.execute(count_todos_query)).all()
    response = {"completed": 0, "not_completed": 0}
    for row in result:
        response[row.completed_at_status] = row.count
    return response


@app.get("/count-todos-sync")
def count_todos_sync(db_session: SyncDBSessionDep):
    # Since this route is defined with `def`, it'll run in a threadpool
    # and won't block the asyncio event loop

    result = db_session.execute(count_todos_query).all()
    response = {"completed": 0, "not_completed": 0}
    for row in result:
        response[row.completed_at_status] = row.count

    return response
