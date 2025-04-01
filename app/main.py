import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.public import router as public_router
from api.private import router as private_router

app = FastAPI(title="Customer Support API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(public_router, prefix="/api/public", tags=["public"])
app.include_router(private_router, prefix="/api/private", tags=["private"])


@app.get("/")
async def root():
    return {"message": "Customer Support API is running"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
