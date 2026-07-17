import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .fastgpt_client import fastgpt_client
from .middleware import request_id_middleware
from .routers import datasets, collections, data, search

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up")
    yield
    logger.info("Shutting down")
    await fastgpt_client.close()


app = FastAPI(
    title="FastGPT RAG API",
    version="1.0.0",
    lifespan=lifespan,
)

app.middleware("http")(request_id_middleware)

app.include_router(datasets.router)
app.include_router(collections.router)
app.include_router(data.router)
app.include_router(search.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
