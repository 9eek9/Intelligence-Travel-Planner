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

# Add budget_service to path
budget_service_path = os.path.join(os.path.dirname(__file__), '..', 'services', 'budget_service')
sys.path.insert(0, budget_service_path)

# Import services
from budget_optimizer_service import BudgetOptimizerService
from flights_client import get_flight_offers
from hotels_client import get_hotel_offers
from fx_client import convert_currency
from optimizer import compose_and_optimize, calculate_activity_meal_costs

router = APIRouter()

# Initialize services
budget_service = BudgetOptimizerService()

# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class TripOptimizationRequest(BaseModel):
    origin: str
    destination: str
    city_code: str
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
                "origin": "YYZ",
                "destination": "BKK",
                "city_code": "BKK",
                "depart_date": "2025-12-01",
                "return_date": "2025-12-05",
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

@router.post("/optimize-trip", response_model=TripOptimizationResponse, summary="Get Multiple Packages")
async def optimize_trip(request: TripOptimizationRequest):
    """
    Optimize travel packages within budget
    
    Returns up to 3 optimized travel packages sorted by price.
    Includes flights, hotels, transit, activities, and meals.
    """
    try:
        results = budget_service.optimize_trip(
            origin=request.origin,
            destination=request.destination,
            city_code=request.city_code,
            depart_date=request.depart_date,
            return_date=request.return_date,
            budget=request.budget,
            currency=request.currency,
            transit_cost=request.transit_cost,
            activities_cost=request.activities_cost,
            meals_cost=request.meals_cost,
            daily_activities=request.daily_activities,
            daily_meals=request.daily_meals
        )
        
        return TripOptimizationResponse(
            success=True,
            packages=results,
            total_packages=len(results),
            message=f"Found {len(results)} optimized packages"
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/optimize-trip/best", response_model=SinglePackageResponse, summary="Get Best Package Only")
async def get_best_trip_package(request: TripOptimizationRequest):
    """
    Get the single best optimized travel package within budget
    
    Returns only the cheapest package that fits within your budget.
    If no packages are within budget, returns the cheapest available option.
    """
    try:
        results = budget_service.optimize_trip(
            origin=request.origin,
            destination=request.destination,
            city_code=request.city_code,
            depart_date=request.depart_date,
            return_date=request.return_date,
            budget=request.budget,
            currency=request.currency,
            transit_cost=request.transit_cost,
            activities_cost=request.activities_cost,
            meals_cost=request.meals_cost,
            daily_activities=request.daily_activities,
            daily_meals=request.daily_meals
        )
        
        if not results:
            raise HTTPException(status_code=404, detail="No packages found")
        
        # Return only the first (best) package
        best_package = results[0]
        
        status_msg = "within budget" if best_package["status"] == "within-budget" else "over budget (cheapest available)"
        
        return SinglePackageResponse(
            success=True,
            package=best_package,
            message=f"Found best package ({status_msg})"
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/optimize-trip/stream", summary="Stream Optimization Progress")
async def optimize_trip_stream(request: TripOptimizationRequest):
    """
    Optimize travel packages with real-time progress streaming
    
    Streams progress updates as Server-Sent Events (SSE).
    Frontend can display live progress to users.
    """
    
    async def event_generator():
        """Generate Server-Sent Events with progress updates"""
        try:
            # Send initial message
            yield f"data: {json.dumps({'type': 'info', 'message': '🚀 Starting optimization...'})}\n\n"
            await asyncio.sleep(0.1)
            
            # Fetch flights
            yield f"data: {json.dumps({'type': 'progress', 'step': 'flights', 'message': f'✈️  Fetching flights from {request.origin} to {request.destination}...'})}\n\n"
            await asyncio.sleep(0.1)
            
            flight_data = get_flight_offers(
                request.origin, 
                request.destination, 
                request.depart_date, 
                request.return_date, 
                budget_service.amadeus_key, 
                budget_service.amadeus_secret
            )
            flights = flight_data.get("data", [])
            
            yield f"data: {json.dumps({'type': 'success', 'message': f'✅ Found {len(flights)} flight options'})}\n\n"
            await asyncio.sleep(0.1)
            
            if not flights:
                yield f"data: {json.dumps({'type': 'error', 'message': '❌ No flights found'})}\n\n"
                return
            
            # Fetch hotels
            yield f"data: {json.dumps({'type': 'progress', 'step': 'hotels', 'message': f'🏨 Fetching hotels in {request.city_code}...'})}\n\n"
            await asyncio.sleep(0.1)
            
            hotel_data = get_hotel_offers(
                request.city_code, 
                request.depart_date, 
                request.return_date, 
                budget_service.amadeus_key, 
                budget_service.amadeus_secret,
                currency=request.currency
            )
            hotels = hotel_data.get("data", [])
            
            yield f"data: {json.dumps({'type': 'success', 'message': f'✅ Found {len(hotels)} hotel options'})}\n\n"
            await asyncio.sleep(0.1)
            
            if not hotels:
                yield f"data: {json.dumps({'type': 'error', 'message': '❌ No hotels found'})}\n\n"
                return
            
            # Convert currency
            yield f"data: {json.dumps({'type': 'progress', 'step': 'currency', 'message': f'💱 Converting prices to {request.currency}...'})}\n\n"
            await asyncio.sleep(0.1)
            
            converted_count = 0
            for hotel in hotels:
                if "offers" in hotel and len(hotel["offers"]) > 0:
                    offer = hotel["offers"][0]
                    price_currency = offer["price"].get("currency", request.currency)
                    
                    if price_currency != request.currency:
                        original_price = float(offer["price"]["total"])
                        converted_price = convert_currency(original_price, price_currency, request.currency)
                        offer["price"]["total"] = str(converted_price)
                        offer["price"]["currency"] = request.currency
                        offer["price"]["original_amount"] = original_price
                        offer["price"]["original_currency"] = price_currency
                        converted_count += 1
            
            if converted_count == 0:
                yield f"data: {json.dumps({'type': 'success', 'message': f'✅ All prices already in {request.currency}'})}\n\n"
            else:
                yield f"data: {json.dumps({'type': 'success', 'message': f'✅ Converted {converted_count} hotel prices'})}\n\n"
            await asyncio.sleep(0.1)
            
            # Calculate costs
            yield f"data: {json.dumps({'type': 'progress', 'step': 'costs', 'message': '🧮 Calculating additional costs...'})}\n\n"
            await asyncio.sleep(0.1)
            
            if request.activities_cost is None or request.meals_cost is None:
                calculated_costs = calculate_activity_meal_costs(
                    request.depart_date, 
                    request.return_date, 
                    request.daily_activities, 
                    request.daily_meals
                )
                activities_cost = request.activities_cost or calculated_costs["activities"]
                meals_cost = request.meals_cost or calculated_costs["meals"]
            else:
                activities_cost = request.activities_cost
                meals_cost = request.meals_cost
            
            transit = {"total": request.transit_cost or 50.0}
            activity_meal = {"activities": activities_cost, "meals": meals_cost}
            
            transit_total = transit["total"]
            message = f'✅ Activities: ${activities_cost:.2f}, Meals: ${meals_cost:.2f}, Transit: ${transit_total:.2f}'
            yield f"data: {json.dumps({'type': 'success', 'message': message})}\n\n"
            await asyncio.sleep(0.1)
            
            # Optimize
            yield f"data: {json.dumps({'type': 'progress', 'step': 'optimize', 'message': f'🎯 Optimizing packages (Budget: ${request.budget:.2f} {request.currency})...'})}\n\n"
            await asyncio.sleep(0.1)
            
            fx_snapshot = {
                "base": request.currency,
                "ts": datetime.now().isoformat(),
                "rates": {}
            }
            
            optimized = compose_and_optimize(
                flights,
                hotels,
                transit,
                activity_meal,
                fx_snapshot,
                request.budget,
                request.currency
            )
            
            yield f"data: {json.dumps({'type': 'success', 'message': f'✅ Generated {len(optimized)} package(s)'})}\n\n"
            await asyncio.sleep(0.1)
            
            # Send final result
            result_data = {
                'type': 'complete',
                'packages': optimized,
                'total_packages': len(optimized),
                'message': f'🎉 Optimization complete! Found {len(optimized)} packages'
            }
            yield f"data: {json.dumps(result_data)}\n\n"
            
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            print(f"Stream error: {error_detail}")
            yield f"data: {json.dumps({'type': 'error', 'message': f'❌ Error: {str(e)}'})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

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

# ============================================================================
# ML BUDGET PREDICTION ENDPOINT
# ============================================================================

class MLBudgetRequest(BaseModel):
    destination: str = Field(..., description="Destination city code (e.g., 'BKK' for Bangkok)")
    duration: int = Field(..., ge=1, description="Trip duration in days")
    total_budget: float = Field(..., gt=0, description="Total trip budget")
    travelers: int = Field(default=1, ge=1, description="Number of travelers")
    region: Optional[str] = Field(None, description="Region (e.g., 'Asia', 'Europe')")
    season: Optional[str] = Field("off_peak", description="Season: peak, off_peak, shoulder")
    purpose: Optional[str] = Field("leisure", description="Purpose: leisure, business, family, adventure, romantic")
    accommodation_type: Optional[str] = Field("hotel", description="Type: hotel, hostel, airbnb, resort, apartment")

    class Config:
        json_schema_extra = {
            "example": {
                "destination": "BKK",
                "duration": 5,
                "total_budget": 3000,
                "travelers": 2,
                "region": "Asia",
                "season": "off_peak",
                "purpose": "leisure",
                "accommodation_type": "hotel"
            }
        }

class MLBudgetResponse(BaseModel):
    success: bool
    breakdown: Dict[str, float]
    total_budget: float
    confidence: float
    message: Optional[str] = None

@router.post("/predict-budget", response_model=MLBudgetResponse, summary="ML Budget Prediction")
async def predict_budget_allocation(request: MLBudgetRequest):
    """
    Use ML model to predict budget allocation across categories
    
    Returns recommended $ amounts for:
    - Accommodation
    - Transportation
    - Food
    - Activities
    - Miscellaneous
    
    Based on destination, duration, travelers, and travel style.
    
    Note: Uses rule-based allocation if ML model fails (graceful degradation)
    """
    try:
        # Import ML predictor (lazy load to avoid startup errors)
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ml_models'))
        from budget_predictor import BudgetPredictor
        import pandas as pd
        
        # City code to name mapping (if model trained on names)
        city_code_to_name = {
            'BKK': 'Bangkok',
            'NYC': 'New York',
            'LAX': 'Los Angeles',
            'MIA': 'Miami',
            'LAS': 'Las Vegas',
            'LON': 'London',
            'PAR': 'Paris',
            'TYO': 'Tokyo',
            'SYD': 'Sydney',
            'DXB': 'Dubai',
            'YYZ': 'Toronto',
            'YVR': 'Vancouver',
            'YUL': 'Montreal'
        }
        
        predictor = BudgetPredictor()
        
        # Use city name if model was trained on names, otherwise use code
        destination = city_code_to_name.get(request.destination, request.destination)
        
        # Create DataFrame with single row (ML model expects DataFrame)
        input_df = pd.DataFrame([{
            'destination': destination,  # Use mapped name
            'duration': request.duration,
            'total_budget': request.total_budget,
            'travelers': request.travelers,
            'region': request.region or 'Unknown',
            'season': request.season,
            'purpose': request.purpose,
            'accommodation_type': request.accommodation_type
        }])
        
        print(f"🔍 ML Prediction Input:\n{input_df}")
        
        # Call predict with DataFrame
        result = predictor.predict(input_df)
        
        print(f"✅ ML Prediction Result: {result}")
        
        return MLBudgetResponse(
            success=True,
            breakdown=result['breakdown'],
            total_budget=result['total_budget'],
            confidence=result['confidence'],
            message=f"ML budget prediction for {request.destination} ({request.duration} days)"
        )
        
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"⚠️  ML Prediction Failed, using rule-based allocation:\n{error_detail}")
        
        # Fallback: Rule-based budget allocation
        # Use percentages based on typical travel patterns
        total = request.total_budget
        
        # Allocation percentages (typical travel budget split)
        allocations = {
            'accommodation': 0.35,      # 35%
            'transportation': 0.25,     # 25%
            'food': 0.20,              # 20%
            'activities': 0.15,        # 15%
            'miscellaneous': 0.05      # 5%
        }
        
        # Adjust based on accommodation type
        if request.accommodation_type == 'hostel':
            allocations['accommodation'] = 0.25
            allocations['activities'] = 0.20
        elif request.accommodation_type == 'resort':
            allocations['accommodation'] = 0.45
            allocations['activities'] = 0.10
        
        # Adjust based on season
        if request.season == 'peak':
            allocations['accommodation'] *= 1.2
            allocations['transportation'] *= 1.1
            # Normalize
            total_pct = sum(allocations.values())
            allocations = {k: v/total_pct for k, v in allocations.items()}
        
        # Calculate amounts
        breakdown = {
            category: round(total * percentage, 2)
            for category, percentage in allocations.items()
        }
        
        print(f"✅ Rule-based allocation: {breakdown}")
        
        return MLBudgetResponse(
            success=True,
            breakdown=breakdown,
            total_budget=total,
            confidence=0.65,  # Lower confidence for rule-based
            message=f"Rule-based budget allocation for {request.destination} ({request.duration} days) - ML model unavailable"
        )
