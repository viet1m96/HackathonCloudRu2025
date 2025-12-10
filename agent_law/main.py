from fastapi import FastAPI
from api import controller

app = FastAPI(title="Agent 1 API")

app.include_router(controller.router, prefix="/api")

@app.get("/")
def root():
    return {"message": "Agent 1 is running. Use /api/user to send questions."}
