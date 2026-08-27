from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def home():
    return {
        "message": "RouteX Backend is running!"
    }