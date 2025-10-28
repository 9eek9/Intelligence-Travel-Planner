from typing import List, Dict, Any, Optional
from datetime import datetime

def calculate_activity_meal_costs(checkin: str, checkout: str, daily_activities: float = 50.0, daily_meals: float = 75.0) -> Dict[str, float]:
    """
    Calculate activity and meal costs based on trip duration
    
    Args:
        checkin: Check-in date (YYYY-MM-DD)
        checkout: Check-out date (YYYY-MM-DD)
        daily_activities: Cost per day for activities (default: 50 CAD)
        daily_meals: Cost per day for meals (default: 75 CAD)
    
    Returns:
        Dictionary with activities and meals total costs
    """
    checkin_date = datetime.strptime(checkin, "%Y-%m-%d")
    checkout_date = datetime.strptime(checkout, "%Y-%m-%d")
    nights = (checkout_date - checkin_date).days
    
    return {
        "activities": round(nights * daily_activities, 2),
        "meals": round(nights * daily_meals, 2)
    }

def _compose_candidates(
    flights: List[Dict[str, Any]], 
    hotels: List[Dict[str, Any]], 
    transit: Dict[str, Any],
    activity_meal: Optional[Dict[str, Any]], 
    currency: str,
    max_flights: int = 2,
    max_hotels: int = 2
) -> List[Dict[str, Any]]:
    """
    Compose candidate travel packages from flights and hotels
    
    Args:
        flights: List of flight offers
        hotels: List of hotel offers (Amadeus format)
        transit: Transit cost dictionary
        activity_meal: Activity and meal cost dictionary (optional, defaults to 0)
        currency: Currency code
        max_flights: Maximum number of flights to consider (default: 2)
        max_hotels: Maximum number of hotels to consider (default: 2)
    
    Returns:
        List of candidate packages with total costs
    """
    if not flights:
        raise ValueError("No flights provided")
    if not hotels:
        raise ValueError("No hotels provided")
    
    # Default activity_meal to 0 if not provided
    if activity_meal is None:
        activity_meal = {"activities": 0, "meals": 0}
    
    combos = []
    top_flights = flights[:max_flights]
    top_hotels = hotels[:max_hotels]

    print(f"\n🔄 Processing {len(top_flights)} flights × {len(top_hotels)} hotels...")

    for f in top_flights:
        try:
            flight_price = float(f["price"]["total"])
            flight_currency = f["price"].get("currency", currency)
            
            for h in top_hotels:
                try:
                    # Amadeus hotel format: h["offers"][0]["price"]["total"]
                    if "offers" not in h or len(h["offers"]) == 0:
                        print(f"⚠️  Skipping hotel - no offers available")
                        continue
                    
                    # Get first offer
                    offer = h["offers"][0]
                    hotel_price = float(offer["price"]["total"])
                    hotel_currency = offer["price"].get("currency", currency)
                    hotel_name = h.get("hotel", {}).get("name", "Unknown Hotel")
                    hotel_id = h.get("hotel", {}).get("hotelId", "unknown")
                    
                    transit_cost = float(transit.get("total", 0))
                    activities_cost = float(activity_meal.get("activities", 0))
                    meals_cost = float(activity_meal.get("meals", 0))
                    
                    total = flight_price + hotel_price + transit_cost + activities_cost + meals_cost
                    
                    combos.append({
                        "flight": {
                            "id": f.get("id", "unknown"),
                            "price": flight_price,
                            "currency": flight_currency
                        },
                        "hotel": {
                            "id": hotel_id,
                            "name": hotel_name,
                            "total": hotel_price,
                            "currency": hotel_currency,
                            "offer_id": offer.get("id", "unknown")
                        },
                        "transit": transit,
                        "activities": activities_cost,
                        "meals": meals_cost,
                        "currency": currency,
                        "total": round(total, 2)
                    })
                    
                    print(f"✅ Combo: Flight ${flight_price:.2f} {flight_currency} + Hotel ${hotel_price:.2f} {hotel_currency} = ${total:.2f}")
                    
                except (KeyError, ValueError, TypeError) as e:
                    print(f"⚠️  Skipping hotel combination - {str(e)}")
                    continue
                    
        except (KeyError, ValueError, TypeError) as e:
            print(f"⚠️  Skipping flight - {str(e)}")
            continue
    
    if not combos:
        raise ValueError("No valid combinations could be created")
    
    print(f"\n✅ Created {len(combos)} valid package combinations")
    return combos

def compose_and_optimize(
    flights: List[Dict[str, Any]], 
    hotels: List[Dict[str, Any]], 
    transit: Dict[str, Any],
    activity_meal: Optional[Dict[str, Any]], 
    fx_snapshot: Dict[str, Any],
    budget: float, 
    currency: str,
    max_results: int = 3
) -> List[Dict[str, Any]]:
    """
    Compose and optimize travel packages within budget
    
    Args:
        flights: List of flight offers
        hotels: List of hotel offers
        transit: Transit cost dictionary (e.g., {"total": 50})
        activity_meal: Activity and meal cost dictionary (optional)
        fx_snapshot: Exchange rate snapshot
        budget: Maximum budget
        currency: Currency code
        max_results: Maximum number of results to return (default: 3)
    
    Returns:
        List of optimized travel packages sorted by total cost
    """
    if budget <= 0:
        raise ValueError("Budget must be positive")
    
    # Compose candidates
    candidates = _compose_candidates(flights, hotels, transit, activity_meal, currency)
    
    # Greedy: choose those within budget, sort by total ascending
    within = [c for c in candidates if c["total"] <= budget]
    within.sort(key=lambda x: x["total"])
    
    print(f"\n📊 {len(within)} packages within budget of ${budget:.2f} {currency}")
    
    # Get top results
    if within:
        top = within[:max_results]
    else:
        # If nothing within budget, return cheapest options
        print(f"⚠️  No packages within budget, returning {max_results} cheapest options")
        top = sorted(candidates, key=lambda x: x["total"])[:max_results]

    # Annotate with FX snapshot and status
    for q in top:
        q["fxSnapshot"] = {"base": fx_snapshot["base"], "ts": fx_snapshot["ts"]}
        q["status"] = "within-budget" if q["total"] <= budget else "over-budget"
        q["budgetRemaining"] = round(budget - q["total"], 2) if q["total"] <= budget else 0
    
    return top