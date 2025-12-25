import os
from datetime import datetime, timedelta

from fastapi import FastAPI, BackgroundTasks
from sqlalchemy import select, and_, desc
from sqlalchemy.orm import joinedload
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.responses import FileResponse
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from database.database import async_session_factory
from settings import settings


app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}
