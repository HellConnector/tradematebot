import os
from contextlib import asynccontextmanager

import sentry_sdk
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

from mini_app_api.data_loader import (
    get_existing_search_items,
    ALL_SEARCH_ITEMS,
)
from mini_app_api.routes import profile, search, portfolio, stats

load_dotenv()

SSL_KEY_PATH = os.getenv("SSL_KEY_PATH")
SSL_CERT_PATH = os.getenv("SSL_CERT_PATH")
ENVIRONMENT = os.getenv("ENVIRONMENT")

sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"), enable_tracing=True, environment=ENVIRONMENT
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    items = await get_existing_search_items()
    ALL_SEARCH_ITEMS.update(items)
    yield
    pass


app = FastAPI(docs_url=None, openapi_url=None, lifespan=lifespan)
app.add_middleware(HTTPSRedirectMiddleware)

origins = [
    os.getenv("MINI_APP_URL"),
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(profile.router)
app.include_router(search.router)
app.include_router(portfolio.router)
app.include_router(stats.router)


def run():
    uvicorn.run(
        "mini_app_api.main:app",
        port=8080,
        reload=True,
        ssl_keyfile=SSL_KEY_PATH,
        ssl_certfile=SSL_CERT_PATH,
    )


if __name__ == "__main__":
    run()
