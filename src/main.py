from fastapi import FastAPI

from auth.router import router as AuthRouter
from api.router import router as GiryaAPIRouter
import dependencies

app = FastAPI()

dependencies.setup()

app.include_router(AuthRouter, prefix="/auth")
app.include_router(GiryaAPIRouter, prefix="/api")

