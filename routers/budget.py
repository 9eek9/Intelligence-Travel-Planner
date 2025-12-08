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
import time
import concurrent.futures

# Add budget_service to path
budget_service_path = os.path.join(os.path.dirname(__file__), '..', 'services', 'budget_service')
sys.path.insert(0, budget_service_path)

# Import services
from services.budget_service.budget_optimizer_service import BudgetOptimizerService
from services.budget_service.flights_client import get_flight_offers
from services.budget_service.hotels_client import get_hotel_offers
from services.budget_service.fx_client import convert_currency
from services.budget_service.optimizer import compose_and_optimize
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
                "budget": 6000,
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
    Complete AI/ML Pipeline with optimized parallel processing
    """
    start_time = time.time()
    
    try:
        progress_logs = []
        suggested_allocation = None
        
        # ========================================================================
        # STEP 1: FETCH TRAVEL DATA FROM AMADEUS API
        # ========================================================================
        
        progress_logs.append(f"Resolving city code for origin: {request.origin}...")
        origin_city_code = get_city_code_from_amadeus(
            city_name=request.origin,
            amadeus_key=budget_service.amadeus_key,
            amadeus_secret=budget_service.amadeus_secret
        )
        progress_logs.append(f"Resolved origin code: {origin_city_code}")
        
        progress_logs.append(f"Resolving city code for destination: {request.destination}...")
        destination_city_code = get_city_code_from_amadeus(
            city_name=request.destination,
            amadeus_key=budget_service.amadeus_key,
            amadeus_secret=budget_service.amadeus_secret
        )
        progress_logs.append(f"Resolved destination code: {destination_city_code}")
        
        # ========================================================================
        # STEP 1: FETCH TRAVEL DATA IN PARALLEL (OPTIMIZED - NO TIMEOUT)
        # ========================================================================
        
        progress_logs.append("Fetching flights, hotels, and activities in parallel...")
        
        def fetch_flights():
            return get_flight_offers(
                origin_city_code, destination_city_code,
                request.depart_date, request.return_date,
                budget_service.amadeus_key, budget_service.amadeus_secret
            )
        
        def fetch_hotels():
            return get_hotel_offers(
                city_code=destination_city_code,
                check_in_date=request.depart_date,
                check_out_date=request.return_date,
                amadeus_key=budget_service.amadeus_key,
                amadeus_secret=budget_service.amadeus_secret,
                currency=request.currency
            )
        
        def fetch_activities():
            return fetch_activities_by_city_name(
                city_name=request.destination,
                start_date=request.depart_date,
                end_date=request.return_date,
                amadeus_key=budget_service.amadeus_key,
                amadeus_secret=budget_service.amadeus_secret,
                target_currency=request.currency
            )
        
        # Execute all API calls in parallel (NO TIMEOUT - more reliable)
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            future_flights = executor.submit(fetch_flights)
            future_hotels = executor.submit(fetch_hotels)
            future_activities = executor.submit(fetch_activities)
            
            # Wait for all results without timeout
            flight_data = future_flights.result()
            hotel_data = future_hotels.result()
            activities = future_activities.result()
        
        flights = flight_data.get("data", [])
        hotels = hotel_data.get("data", [])
        
        elapsed = time.time() - start_time
        progress_logs.append(f"✅ Data fetched in {elapsed:.1f}s: {len(flights)} flights, {len(hotels)} hotels, {len(activities)} activities")
        
        # Extract dictionaries
        dictionaries = flight_data.get("dictionaries", {})
        carriers_dict = dictionaries.get("carriers", {})
        aircraft_dict = dictionaries.get("aircraft", {})
        
        # ========================================================================
        # STEP 2: CALCULATE MEAL & TRANSIT USING LLM (GEMINI)
        # ========================================================================
        # This happens inside compose_and_optimize()
        
        # ========================================================================
        # STEP 3: COMPOSE & OPTIMIZE PACKAGES
        # ========================================================================
        
        fx_snapshot = {
            "base": request.currency,
            "ts": datetime.now().isoformat(),
            "rates": {}
        }

        progress_logs.append("Optimizing packages...")
        opt_start = time.time()
        
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
        
        opt_elapsed = time.time() - opt_start
        progress_logs.append(f"✅ Optimization complete in {opt_elapsed:.1f}s")
        
        # ========================================================================
        # STEP 4: SCORE PACKAGES USING ML (XGBOOST) - KEEP FUNCTIONALITY
        # ========================================================================
        
        progress_logs.append("Scoring packages with ML...")
        score_start = time.time()
        
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
            
        except Exception as e:
            print(f"Scoring error: {str(e)}")
            import traceback
            traceback.print_exc()
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
        
        score_elapsed = time.time() - score_start
        progress_logs.append(f"✅ Quality scoring complete in {score_elapsed:.1f}s")
        
        # ========================================================================
        # STEP 5: SUGGEST BUDGET ALLOCATION USING ML (XGBOOST) - KEEP FUNCTIONALITY
        # ========================================================================
        
        progress_logs.append("Generating budget allocation suggestions...")
        alloc_start = time.time()
        
        try:
            days = (datetime.strptime(request.return_date, "%Y-%m-%d") - 
                    datetime.strptime(request.depart_date, "%Y-%m-%d")).days
            
            suggested_allocation = suggest_budget_allocation(
                total_budget=request.budget,
                destination=request.destination,
                days=days,
                travel_style=request.travel_style
            )
            
        except Exception as e:
            print(f"Budget allocation error: {str(e)}")
            suggested_allocation = {
                "flights_percent": 40.0,
                "hotels_percent": 30.0,
                "activities_percent": 15.0,
                "meals_percent": 10.0,
                "transit_percent": 5.0,
                "reasoning": "Default allocation used due to error",
                "model_used": "Fallback"
            }
        
        alloc_elapsed = time.time() - alloc_start
        progress_logs.append(f"✅ Budget allocation complete in {alloc_elapsed:.1f}s")

        # ========================================================================
        # STEP 6: FORMAT RESPONSE
        # ========================================================================

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
            
            # Ensure activities has proper structure
            if "activities" not in package or not isinstance(package["activities"], dict):
                package["activities"] = {
                    "total": 0,
                    "details": []
                }
            
            # Get the activities from the package (already converted in optimizer)
            package_activities = package.get("activities", {}).get("details", [])
            
            # Format activity details with the package currency
            if package_activities:
                package["activities"]["details"] = [
                    {
                        "name": activity.get("name", "Unknown Activity"),
                        "price": float(activity["price"]["amount"]),
                        "currencyCode": package["currency"],  # Use package currency instead of original
                        "duration": activity.get("minimumDuration"),
                        "bookinglink": activity.get("bookingLink")
                    }
                    for activity in package_activities
                    if "price" in activity and "amount" in activity["price"]
                ]

        total_elapsed = time.time() - start_time
        progress_logs.append(f"🎉 Total processing time: {total_elapsed:.1f}s")

        return {
            "success": True,
            "packages": optimized,
            "total_packages": len(optimized),
            "message": f"Found {len(optimized)} AI-optimized packages in {total_elapsed:.1f}s",
            "progress": progress_logs,
            "processing_time_seconds": round(total_elapsed, 2),
            "ai_ml_pipeline": {
                "step1_data_source": "Amadeus API (Parallel)",
                "step2_meal_transit": "LLM (Gemini)",
                "step3_optimization": "Greedy Algorithm",
                "step4_scoring": suggested_allocation.get("model_used", "XGBoost") if suggested_allocation else "XGBoost",
                "step5_allocation": suggested_allocation.get("model_used", "XGBoost") if suggested_allocation else "XGBoost"
            },
            "budget_suggestion": {
                "flights_percent": suggested_allocation.get("flights_percent", 0) if suggested_allocation else 0,
                "hotels_percent": suggested_allocation.get("hotels_percent", 0) if suggested_allocation else 0,
                "activities_percent": suggested_allocation.get("activities_percent", 0) if suggested_allocation else 0,
                "meals_percent": suggested_allocation.get("meals_percent", 0) if suggested_allocation else 0,
                "transit_percent": suggested_allocation.get("transit_percent", 0) if suggested_allocation else 0,
                "reasoning": suggested_allocation.get("reasoning", "No reasoning available") if suggested_allocation else "No reasoning available"
            },
            "stats": {
                "flights_found": len(flights),
                "hotels_found": len(hotels),
                "activities_found": len(activities),
                "packages_within_budget": sum(1 for p in optimized if p["status"] == "within-budget"),
                "best_quality_score": optimized[0].get("quality_score", 0) if optimized else 0
            }
        }

    except ValueError as e:
        print(f"ValueError: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
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

