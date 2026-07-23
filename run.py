import uvicorn

if __name__ == "__main__":
    print("Starting YouTube Subscription Tracker Dashboard...")
    print("Open http://localhost:8000 in your browser.")
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
