from typing import Union

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

app = FastAPI()


@app.get("/api/ping")
def ping():
    return {"pong": True}


app.mount("/", StaticFiles(directory="dist", html=True), name="static")
