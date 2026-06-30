from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router

app = FastAPI(title="GeoIntel OSINT", version="3.0", docs_url="/api/docs", redoc_url="/api/redoc")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/docs", include_in_schema=False)
@app.get("/status", include_in_schema=False)
@app.get("/terms", include_in_schema=False)
def frontend_page():
    return FileResponse("frontend/dist/index.html")


app.mount("/", StaticFiles(directory="frontend/dist", html=True))
