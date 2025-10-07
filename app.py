from fastapi import FastAPI
from routers import itinerary

app = FastAPI(title="SmartTravelSystem API", version="1.0.0")
app.include_router(itinerary.router, prefix="/itinerary", tags=["Itinerary"])

@app.get("/")
def root():
    return {"message": "SmartTravelSystem API is running"}