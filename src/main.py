from fastapi import FastAPI

from auth.router import router as AuthRouter

app = FastAPI()

app.include_router(AuthRouter, prefix="/auth")

