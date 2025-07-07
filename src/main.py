from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from auth.router import router as AuthRouter
from api.router import router as GiryaAPIRouter
import dependencies

import config


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

dependencies.setup()

app.include_router(AuthRouter, prefix="/auth")
app.include_router(GiryaAPIRouter, prefix="/api")

