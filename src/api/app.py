from contextlib import asynccontextmanager
from concurrent.futures import ThreadPoolExecutor
import asyncio
from fastapi import FastAPI
from api.routes.tickets import router as tickets_router
from api.routes.monitoring import router as monitoring_router
from utils.logging.logging_config import setup_logging
setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    executor = ThreadPoolExecutor(max_workers=64)

    loop = asyncio.get_running_loop()
    loop.set_default_executor(executor)

    app.state.executor = executor

    try:
        yield
    finally:
        executor.shutdown(wait=False)


app = FastAPI(lifespan=lifespan)

app.include_router(tickets_router)
app.include_router(monitoring_router)