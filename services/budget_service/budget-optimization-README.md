# Budget Optimization Service

## Architecture:
```
routers/budget.py            ← REST API endpoints
└─ services/budget_service/
   ├─ budget_optimizer_service.py  ← Main orchestrator
   ├─ flights_client.py         ← Fetches flights from Amadeus API
   ├─ hotels_client.py          ← Fetches hotels from Amadeus API
   ├─ fx_client.py              ← Currency conversion
   └─ optimizer.py              ← Combines & optimizes packages
```

## Features:
✅ Flight Search - Real-time flight offers from Amadeus API
✅ Hotel Search - Real-time hotel offers with currency conversion
✅ Currency Conversion - Exchange rates for accurate pricing
✅ Package Optimization - Combines flights + hotels + extras within budget
✅ Smart Filtering - Returns best options sorted by price
✅ REST API - FastAPI endpoints for frontend integration

## API Endpoints:

### 1. Optimize Trip
**POST** `/api/budget/optimize-trip`

**Request Body:**
```json
{
  "origin": "YYZ",
  "destination": "BKK",
  "city_code": "BKK",
  "depart_date": "2025-12-01",
  "return_date": "2025-12-05",
  "budget": 3000,
  "currency": "CAD"
}
```

**Response:**
```json
{
  "success": true,
  "packages": [
    {
      "flight": {"id": "...", "price": 1200, "currency": "CAD"},
      "hotel": {"id": "...", "name": "Holiday Inn Bangkok", "total": 900, "currency": "CAD"},
      "transit": {"total": 50},
      "activities": 200,
      "meals": 300,
      "total": 2650,
      "status": "within-budget",
      "budgetRemaining": 350
    }
  ],
  "total_packages": 3,
  "message": "Found 3 optimized packages within budget"
}
```

### 2. Convert Currency
**GET** `/api/budget/convert-currency?amount=100&from_currency=USD&to_currency=CAD`

**Response:**
```json
{
  "success": true,
  "amount": 100,
  "from_currency": "USD",
  "to_currency": "CAD",
  "converted_amount": 137.50
}
```

### 3. Health Check
**GET** `/api/budget/health`

## Run API Server:
```bash
pip install google-generativeai

cd /path/to/SmartTravelSystem_Backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
uvicorn app:app --reload
```

Server runs at: **http://localhost:8000**

API Documentation: **http://localhost:8000/docs**

## Test API:
```bash
# Using curl
curl -X POST "http://localhost:8000/api/budget/optimize-trip" \
  -H "Content-Type: application/json" \
  -d '{"origin":"YYZ","destination":"BKK","city_code":"BKK","depart_date":"2025-12-01","return_date":"2025-12-05","budget":3000,"currency":"CAD"}'


curl -N -X POST "http://localhost:8000/budget/optimize-trip/stream" \
  -H "Content-Type: application/json" \
  -d '{"origin":"YYZ","destination":"BKK","city_code":"BKK","depart_date":"2025-12-01","return_date":"2025-12-05","budget":3000,"currency":"CAD"}'


# Using browser
http://localhost:8000/docs
```

## Test Coverage:
✅ Unit tests for all clients (mocked, fast)
✅ Integration tests for all clients (real API calls)
✅ Full end-to-end service test

## Run Tests:
```bash
cd services/budget_service

# Unit tests
python3 test_flight_client.py -v
python3 test_hotels_client.py -v
python3 test_fx_client.py -v
python3 test_optimizer.py -v

# Integration tests
python3 test_flight_client_integration_test.py -v
python3 test_hotel_client_integration.py -v
python3 test_fx_client_integration.py -v
```

## Test Inputs

### Test Input 1: Bangkok (BKK)
```json
{
  "origin": "YYZ",
  "destination": "BKK",
  "city_code": "BKK",
  "depart_date": "2025-12-01",
  "return_date": "2025-12-05",
  "budget": 3000,
  "currency": "CAD"
}
```

### Test Input 2: Las Vegas (LAS)
```json
{
  "origin": "YYZ",
  "destination": "LAS",
  "city_code": "LAS",
  "depart_date": "2025-12-01",
  "return_date": "2025-12-05",
  "budget": 2500,
  "currency": "CAD"
}
```

### Test Input 3: New York City (NYC)
```json
{
  "origin": "YYZ",
  "destination": "JFK",
  "city_code": "NYC",
  "depart_date": "2025-12-01",
  "return_date": "2025-12-05",
  "budget": 2000,
  "currency": "CAD"
}
```

### Test Input 4: Miami (MIA)
```json
{
  "origin": "YYZ",
  "destination": "MIA",
  "city_code": "MIA",
  "depart_date": "2025-12-01",
  "return_date": "2025-12-05",
  "budget": 2800,
  "currency": "CAD"
}
```

### Test Input 5: Los Angeles (LAX)
```json
{
  "origin": "YYZ",
  "destination": "LAX",
  "city_code": "LAX",
  "depart_date": "2025-12-01",
  "return_date": "2025-12-05",
  "budget": 3500,
  "currency": "CAD"
}
```

### Test Input 6: Vancouver (YVR) - Domestic Canada
```json
{
  "origin": "YYZ",
  "destination": "YVR",
  "city_code": "YVR",
  "depart_date": "2025-12-01",
  "return_date": "2025-12-05",
  "budget": 1800,
  "currency": "CAD"
}
```

### Test Input 7: Montreal (YUL) - Domestic Canada
```json
{
  "origin": "YYZ",
  "destination": "YUL",
  "city_code": "YUL",
  "depart_date": "2025-12-01",
  "return_date": "2025-12-05",
  "budget": 1200,
  "currency": "CAD"
}
```

### Test Input 8: London (LON)
```json
{
  "origin": "YYZ",
  "destination": "LHR",
  "city_code": "LON",
  "depart_date": "2025-12-01",
  "return_date": "2025-12-05",
  "budget": 4000,
  "currency": "CAD"
}
```

### Test Input 9: Tokyo (TYO)
```json
{
  "origin": "YYZ",
  "destination": "NRT",
  "city_code": "TYO",
  "depart_date": "2025-12-01",
  "return_date": "2025-12-05",
  "budget": 5000,
  "currency": "CAD"
}
```