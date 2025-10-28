from fastapi import FastAPI
from routers import itinerary, sentiment, budget
from database.database import create_tables

app = FastAPI(title="SmartTravelSystem API", version="1.0.0")

# Create database tables on startup
@app.on_event("startup")
async def startup_event():
    """Create database tables on startup"""
    create_tables()
    print(" Database tables created")

app.include_router(itinerary.router, prefix="/itinerary", tags=["Itinerary"])
app.include_router(sentiment.router, prefix="/sentiment", tags=["Sentiment"])
app.include_router(budget.router, prefix="/budget", tags=["budget"])

@app.get("/")
def root():
    return {"message": "SmartTravelSystem API is running"}
