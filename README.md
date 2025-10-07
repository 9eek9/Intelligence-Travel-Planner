# SmartTravelSystem_Backend
Capstone Project

# SmartTravelSystem (Backend Only)

FastAPI backend that generates smart itineraries using Google Places API + Gemini.

## Stack
- FastAPI, Uvicorn
- Google Generative AI (Gemini)
- Google Places API

## Run locally
```bash
python -m venv .venv
.\.venv\Scripts\activate          
pip install -r requirements.txt
cp .env.example .env              
uvicorn app:app --reload
