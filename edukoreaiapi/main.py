from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config.config import CORS_ORIGINS
from routers import auth, ebooks


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Pre-load the OCR engine (e.g. EasyOCR's models) so the first real
    # scan request doesn't pay that cost and risk a client-side timeout.
    from ocr.factory import get_ocr_engine

    try:
        get_ocr_engine()
    except Exception:
        pass
    yield


app = FastAPI(title="EduKoreAI API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(ebooks.router)


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    from config.config import API_HOST, API_PORT

    uvicorn.run("main:app", host=API_HOST, port=API_PORT, reload=False)
