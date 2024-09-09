from fastapi import FastAPI
import fastapi.responses
import uvicorn


app = FastAPI()


@app.get("/")
async def get_default():
    return fastapi.responses.HTMLResponse()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=80)
