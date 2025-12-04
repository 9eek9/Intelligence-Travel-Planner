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
from services.budget_service.llm_cost_calculator import calculate_costs_with_llm  # LLM for meals/transit
from services.budget_service.package_scorer import score_package  # XGBoost scorer
from services.budget_service.budget_allocator import suggest_budget_allocation  # XGBoost allocator

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
    activities_cost: Optional[float] = None
    travel_style: str = "moderate"  # Add: 'budget', 'moderate', or 'luxury'
    user_id: Optional[str] = None  # NEW: Add user_id for personalized recommendations

    class Config:
        json_schema_extra = {
            "example": {
                "origin": "Toronto",
                "destination": "Bangkok",  # Pass city name instead of city code
                "depart_date": "2026-03-25",
                "return_date": "2026-03-30",
                "budget": 3000,
                "currency": "CAD",
                "travel_style": "moderate", #"moderate/budget/luxury"
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
        raise RuntimeError(f"Failed to retrieve the city code: {e}")

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

@router.post("/optimize-trip", summary="Get Multiple Packages with AI/ML")
async def optimize_trip(request: TripOptimizationRequest):
    """
    Complete AI/ML Pipeline:
    1. Fetch data from Amadeus
    2. Use LLM (Gemini) for meal/transit estimation
    3. Compose packages
    4. Score packages with XGBoost
    5. Suggest budget allocation with XGBoost
    """
    try:
        progress_logs = []

        # ========================================================================
        # STEP 1: FETCH TRAVEL DATA FROM AMADEUS API
        # ========================================================================
        progress_logs.append("📍 STEP 1: Fetching travel data from Amadeus...")
        
        # Resolve city codes
        origin_city_code = get_city_code_from_amadeus(
            city_name=request.origin,
            amadeus_key=budget_service.amadeus_key,
            amadeus_secret=budget_service.amadeus_secret
        )
        destination_city_code = get_city_code_from_amadeus(
            city_name=request.destination,
            amadeus_key=budget_service.amadeus_key,
            amadeus_secret=budget_service.amadeus_secret
        )
        
        # Fetch flights
        progress_logs.append(f"  ✈️  Fetching flights...")
        flight_data = get_flight_offers(
            origin_city_code, destination_city_code,
            request.depart_date, request.return_date,
            budget_service.amadeus_key, budget_service.amadeus_secret
        )
        flights = flight_data.get("data", [])
        
        # Extract dictionaries for airline and aircraft names
        dictionaries = flight_data.get("dictionaries", {})
        carriers_dict = dictionaries.get("carriers", {})
        aircraft_dict = dictionaries.get("aircraft", {})
        
        progress_logs.append(f"  ✅ Found {len(flights)} flights")

        # Fetch hotels
        progress_logs.append(f"  🏨 Fetching hotels...")
        hotel_data = get_hotel_offers(
            city_code=destination_city_code,
            check_in_date=request.depart_date,
            check_out_date=request.return_date,
            amadeus_key=budget_service.amadeus_key,
            amadeus_secret=budget_service.amadeus_secret,
            currency=request.currency
        )
        hotels = hotel_data.get("data", [])
        progress_logs.append(f"  ✅ Found {len(hotels)} hotels")
        
        # Fetch activities
        progress_logs.append(f"  🎭 Fetching activities...")
        activities = fetch_activities_by_city_name(
            city_name=request.destination,
            start_date=request.depart_date,
            end_date=request.return_date,
            amadeus_key=budget_service.amadeus_key,
            amadeus_secret=budget_service.amadeus_secret,
            target_currency=request.currency
        )
        progress_logs.append(f"  ✅ Found {len(activities)} activities")

        # ========================================================================
        # STEP 2: CALCULATE MEAL & TRANSIT USING LLM (GEMINI)
        # ========================================================================
        progress_logs.append("🤖 STEP 2: Using LLM (Gemini) to calculate meal & transit costs...")
        # This happens inside compose_and_optimize()
        
        # ========================================================================
        # STEP 3: COMPOSE & OPTIMIZE PACKAGES
        # ========================================================================
        progress_logs.append("🎯 STEP 3: Composing travel packages...")
        
        fx_snapshot = {
            "base": request.currency,
            "ts": datetime.now().isoformat(),
            "rates": {}
        }

        optimized = compose_and_optimize(
            flights=flights,
            hotels=hotels,
            activities=activities,
            fx_snapshot=fx_snapshot,
            budget=request.budget,
            currency=request.currency,
            destination=request.destination,
            depart_date=request.depart_date,
            return_date=request.return_date,
            travel_style=request.travel_style
        )
        
        # ========================================================================
        # STEP 4: SCORE PACKAGES USING ML (XGBOOST)
        # ========================================================================
        progress_logs.append("📊 STEP 4: Scoring packages with XGBoost ML model...")
        
        try:
            for i, package in enumerate(optimized):
                print(f"Scoring package {i+1}/{len(optimized)}...")
                quality_score = score_package(
                    package=package,
                    user_preferences={
                        "travel_style": request.travel_style,
                        "budget": request.budget
                    },
                    destination=request.destination
                )
                
                package["quality_score"] = quality_score["overall_score"]
                package["quality_breakdown"] = {
                    "value": quality_score["value_score"],
                    "convenience": quality_score["convenience_score"],
                    "experience": quality_score["experience_score"],
                    "insights": quality_score["insights"],
                    "model": quality_score.get("model_used", "Rule-Based")
                }
            
            progress_logs.append(f"  ✅ All packages scored successfully")
            
        except Exception as e:
            print(f"❌ Scoring error: {str(e)}")
            import traceback
            traceback.print_exc()
            progress_logs.append(f"  ⚠️  Scoring failed: {str(e)}")
            # Add default scores so API doesn't crash
            for package in optimized:
                if "quality_score" not in package:
                    package["quality_score"] = 50.0
                    package["quality_breakdown"] = {
                        "value": 50.0,
                        "convenience": 50.0,
                        "experience": 50.0,
                        "insights": "Scoring unavailable",
                        "model": "Error"
                    }
        
        # Sort packages by quality score (best first)
        optimized = sorted(optimized, key=lambda x: x.get("quality_score", 0), reverse=True)

        # ========================================================================
        # STEP 5: SUGGEST BUDGET ALLOCATION USING ML (XGBOOST)
        # ========================================================================
        progress_logs.append("💰 STEP 5: Generating budget allocation suggestion...")
        
        try:
            days = (datetime.strptime(request.return_date, "%Y-%m-%d") - 
                    datetime.strptime(request.depart_date, "%Y-%m-%d")).days
            
            suggested_allocation = suggest_budget_allocation(
                total_budget=request.budget,
                destination=request.destination,
                days=days,
                travel_style=request.travel_style
            )
            progress_logs.append(f"  ✅ Allocation: Hotels {suggested_allocation['hotels_percent']:.1f}%")
            
        except Exception as e:
            print(f"❌ Budget allocation error: {str(e)}")
            import traceback
            traceback.print_exc()
            # Provide default allocation
            suggested_allocation = {
                "flights_percent": 25.0,
                "hotels_percent": 40.0,
                "activities_percent": 12.0,
                "meals_percent": 18.0,
                "transit_percent": 5.0,
                "reasoning": "Default allocation (error occurred)",
                "model_used": "Error"
            }
            progress_logs.append(f"  ⚠️  Using default allocation")

        # ========================================================================
        # STEP 6: FORMAT RESPONSE
        # ========================================================================
        progress_logs.append("✅ COMPLETE! All processing done.")

        # Fill in airline/aircraft names from Amadeus dictionaries
        for package in optimized:
            if package.get("flight"):
                # Add airline name
                airline_code = package["flight"].get("airline_code")
                if airline_code in carriers_dict:
                    package["flight"]["airline_name"] = carriers_dict[airline_code]
                else:
                    package["flight"]["airline_name"] = airline_code
                
                # Fill in carrier and aircraft names for each segment
                for itinerary in package["flight"].get("itineraries", []):
                    for segment in itinerary.get("segments", []):
                        carrier_code = segment.get("carrier_code")
                        aircraft_code = segment.get("aircraft_code")
                        
                        # Add carrier name
                        if carrier_code in carriers_dict:
                            segment["carrier_name"] = carriers_dict[carrier_code]
                        else:
                            segment["carrier_name"] = carrier_code
                        
                        # Add aircraft name
                        if aircraft_code in aircraft_dict:
                            segment["aircraft_name"] = aircraft_dict[aircraft_code]
                        else:
                            segment["aircraft_name"] = f"Aircraft {aircraft_code}"
            
            # Add activity details
            package["activities"] = {
                "total": package.get("activities", {}).get("total", 0),
                "details": [
                    {
                        "name": activity["name"],
                        "price": float(activity["price"]["amount"]),
                        "currencyCode": activity["price"]["currencyCode"],
                        "duration": activity.get("minimumDuration"),
                        "bookinglink": activity.get("bookingLink")
                    }
                    for activity in activities
                    if "price" in activity and "amount" in activity["price"]
                ]
            }

        return {
            "success": True,
            "packages": optimized,
            "total_packages": len(optimized),
            "message": f"Found {len(optimized)} AI-optimized packages",
            "ai_ml_pipeline": {
                "step1_data_source": "Amadeus API",
                "step2_meal_transit": "LLM (Gemini)",
                "step3_optimization": "Greedy Algorithm",
                "step4_scoring": suggested_allocation.get("model_used", "XGBoost"),
                "step5_allocation": suggested_allocation.get("model_used", "XGBoost")
            },
            "budget_suggestion": {
                "flights_percent": suggested_allocation["flights_percent"],
                "hotels_percent": suggested_allocation["hotels_percent"],
                "activities_percent": suggested_allocation["activities_percent"],
                "meals_percent": suggested_allocation["meals_percent"],
                "transit_percent": suggested_allocation["transit_percent"],
                "reasoning": suggested_allocation["reasoning"]
            },
            "progress": progress_logs,
            "stats": {
                "flights_found": len(flights),
                "hotels_found": len(hotels),
                "activities_found": len(activities),
                "packages_within_budget": sum(1 for p in optimized if p["status"] == "within-budget"),
                "best_quality_score": optimized[0].get("quality_score", 0) if optimized else 0
            }
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# ...existing convert_currency_endpoint...

@router.get("/convert-currency", summary="Convert Currency")
async def convert_currency_endpoint(
    to_currency: str,
    from_currency: str,
    amount: float
):
    """
    Example: /convert-currency?amount=100&from_currency=USD&to_currency=CAD
        Convert currency using real-time exchange rates
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

