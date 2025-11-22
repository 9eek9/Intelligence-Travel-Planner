"""
Budget Router - Travel Package Optimization
Handles travel package optimization with flights, hotels, and budget management
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import sys
import os
import asyncio
import json
from datetime import datetime
import requests

# Add budget_service to path
budget_service_path = os.path.join(os.path.dirname(__file__), '..', 'services', 'budget_service')
sys.path.insert(0, budget_service_path)

# Import services
from services.budget_service.budget_optimizer_service import BudgetOptimizerService
from services.budget_service.flights_client import get_flight_offers
from services.budget_service.hotels_client import get_hotel_offers
from services.budget_service.fx_client import convert_currency
from services.budget_service.optimizer import compose_and_optimize, calculate_meal_costs
from services.budget_service.activities_client import fetch_activities_by_city_name

router = APIRouter()

# Initialize services
budget_service = BudgetOptimizerService()

# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class TripOptimizationRequest(BaseModel):
    origin: str
    destination: str  # Change this to accept the city name
    depart_date: str
    return_date: str
    budget: float
    currency: str = "CAD"
    transit_cost: Optional[float] = None
    activities_cost: Optional[float] = None
    meals_cost: Optional[float] = None
    daily_activities: float = 50.0
    daily_meals: float = 75.0

    class Config:
        json_schema_extra = {
            "example": {
                "origin": "Toronto",
                "destination": "Bangkok",  # Pass city name instead of city code
                "depart_date": "2025-12-25",
                "return_date": "2025-12-30",
                "budget": 3000,
                "currency": "CAD"
            }
        }

class TripOptimizationResponse(BaseModel):
    success: bool
    packages: List[Dict[str, Any]]
    total_packages: int
    message: Optional[str] = None

class SinglePackageResponse(BaseModel):
    success: bool
    package: Dict[str, Any]
    message: Optional[str] = None

# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get("/health", summary="Health Check")
async def health_check():
    """Check if budget optimization service is running"""
    return {
        "service": "Budget Optimization",
        "status": "running",
        "version": "1.0.0"
    }

def get_city_code_from_amadeus(city_name: str, amadeus_key: str, amadeus_secret: str) -> str:
    """
    Fetch city name from Amadeus API using the city code (IATA code).
    """
    try:
        # Amadeus API endpoint for Airport & City Search
        url = "https://api.amadeus.com/v1/reference-data/locations/cities"
        headers = {
            "Authorization": f"Bearer {get_amadeus_access_token(amadeus_key, amadeus_secret)}"
        }
        params = {
            "include": "AIRPORTS",
            "keyword": city_name,
            "max": 1
        }
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()

        # Extract city code from the response
        if data and "data" in data and len(data["data"]) > 0:
            return data["data"][0]["iataCode"]
    except Exception as e:
        raise RuntimeError(f"Failed to retreive the city code   : {e}")

def get_amadeus_access_token(amadeus_key: str, amadeus_secret: str) -> str:
    """
    Fetch an access token from Amadeus API.
    """
    try:
        url = "https://api.amadeus.com/v1/security/oauth2/token"
        payload = {
            "grant_type": "client_credentials",
            "client_id": amadeus_key,
            "client_secret": amadeus_secret
        }
        response = requests.post(url, data=payload)
        response.raise_for_status()
        return response.json().get("access_token")
    except Exception as e:
        raise RuntimeError(f"Failed to fetch Amadeus access token: {e}")

@router.post("/optimize-trip", summary="Get Multiple Packages")
async def optimize_trip(request: TripOptimizationRequest):
    """
    Optimize travel packages within budget.
    """
    try:
        progress_logs = []

        # Resolve city code dynamically using Amadeus API
        progress_logs.append(f"🌍 Resolving city code for origin: {request.origin}...")
        origin_city_code = get_city_code_from_amadeus(
            city_name=request.origin,
            amadeus_key=budget_service.amadeus_key,
            amadeus_secret=budget_service.amadeus_secret
        )
        progress_logs.append(f"✅ Resolved city code: {origin_city_code}")

        progress_logs.append(f"🌍 Resolving city code for destination: {request.destination}...")
        destination_city_code = get_city_code_from_amadeus(
            city_name=request.destination,
            amadeus_key=budget_service.amadeus_key,
            amadeus_secret=budget_service.amadeus_secret
        )
        progress_logs.append(f"✅ Resolved city code: {destination_city_code}")

        # Fetch flights
        progress_logs.append(f"✈️  Fetching flights from {request.origin} to {destination_city_code}...")
        flight_data = get_flight_offers(
            origin_city_code,
            destination_city_code,
            request.depart_date,
            request.return_date,
            budget_service.amadeus_key,
            budget_service.amadeus_secret
        )
        flights = flight_data.get("data", [])
        progress_logs.append(f"✅ Found {len(flights)} flight options")

        # Fetch hotel offers
        progress_logs.append(f"🏨 Fetching offers for hotels in {destination_city_code}...")
        hotel_data = get_hotel_offers(
            city_code=destination_city_code,
            check_in_date=request.depart_date,
            check_out_date=request.return_date,
            amadeus_key=budget_service.amadeus_key,
            amadeus_secret=budget_service.amadeus_secret,
            currency=request.currency
        )
        hotels = hotel_data.get("data", [])
        progress_logs.append(f"✅ Found {len(hotels)} hotel offers")

        # Fetch activities
        progress_logs.append(f"🎭 Fetching activities in {request.destination}...")
        activities = fetch_activities_by_city_name(
            city_name=request.destination,
            start_date=request.depart_date,
            end_date=request.return_date,
            amadeus_key=budget_service.amadeus_key,
            amadeus_secret=budget_service.amadeus_secret,
            target_currency=request.currency
        )
        # Ensure total_activity_cost is initialized even if activities are empty or malformed
        total_activity_cost = sum(
            float(
                convert_currency(
                    float(activity["price"]["amount"]),  # Ensure amount is a float
                    activity["price"]["currencyCode"],
                    request.currency
                )
            ) if activity["price"]["currencyCode"] != request.currency else float(activity["price"]["amount"])
            for activity in activities
            if "price" in activity and "amount" in activity["price"] and "currencyCode" in activity["price"]
        ) if activities else 0.0

        progress_logs.append(f"✅ Found {len(activities)} activities with total cost: {total_activity_cost:.2f} {request.currency}")

        # Calculate costs
        progress_logs.append("🧮 Calculating additional costs...")
        activities_cost = total_activity_cost  # Ensure activities_cost is always initialized
        if request.meals_cost is None:
            calculated_costs = calculate_meal_costs(
                request.depart_date,
                request.return_date,
                request.daily_meals
            ) # Use real activity cost
            meals_cost = request.meals_cost or calculated_costs["meals"]
        else:
            meals_cost = request.meals_cost

        transit = {"total": request.transit_cost or 50.0}
        meal = {"meals": meals_cost}

        transit_total = transit["total"]
        progress_logs.append(f"✅ Meals: ${meals_cost:.2f}, Transit: ${transit_total:.2f}")

        # Optimize
        progress_logs.append(f"🎯 Optimizing packages (Budget: ${request.budget:.2f} {request.currency})...")
        fx_snapshot = {
            "base": request.currency,
            "ts": datetime.now().isoformat(),
            "rates": {}
        }

        optimized = compose_and_optimize(
            flights,
            hotels,
            transit,
            activities,  # Pass activities to the function
            meal,
            fx_snapshot,
            request.budget,
            request.currency
        )

        progress_logs.append(f"✅ Generated {len(optimized)} package(s)")
        progress_logs.append(f"🎉 Optimization complete!")

        # Include detailed activities in the response
        for package in optimized:
            package["activities"] = {
                "total": activities_cost,
                "details": [
                    {
                        "name": activity["name"],
                        "price": round(
                            convert_currency(
                                float(activity["price"]["amount"]),  # Ensure amount is a float
                                activity["price"]["currencyCode"],
                                request.currency
                            ),
                            2
                        ) if activity["price"]["currencyCode"] != request.currency else float(activity["price"]["amount"]),
                        "currencyCode": request.currency,  # Use the target currency
                        "duration": activity.get("minimumDuration"),
                        "bookinglink": activity.get("bookingLink")
                    }
                    for activity in activities
                    if "price" in activity and "amount" in activity["price"] and "currencyCode" in activity["price"]
                ]
            }

        return {
            "success": True,
            "packages": optimized,
            "total_packages": len(optimized),
            "message": f"Found {len(optimized)} optimized packages",
            "progress": progress_logs,
            "stats": {
                "flights_found": len(flights),
                "hotels_found": len(hotels),
                "packages_within_budget": sum(1 for p in optimized if p["status"] == "within-budget")
            }
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/convert-currency", summary="Convert Currency")
async def convert_currency_endpoint(
    amount: float,
    from_currency: str,
    to_currency: str
):
    """
    Convert currency using real-time exchange rates
    
    Example: /convert-currency?amount=100&from_currency=USD&to_currency=CAD
    """
    try:
        result = convert_currency(amount, from_currency, to_currency)
        return {
            "success": True,
            "amount": amount,
            "from_currency": from_currency,
            "to_currency": to_currency,
            "converted_amount": round(result, 2)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

