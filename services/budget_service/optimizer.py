from typing import List, Dict, Any, Optional
from datetime import datetime
from fx_client import convert_currency
from llm_cost_calculator import calculate_costs_with_llm

def calculate_meal_costs(checkin: str, checkout: str,daily_meals: float = 75.0) -> Dict[str, float]:
    """
    Calculate  meal costs based on trip duration
    
    Args:
        checkin: Check-in date (YYYY-MM-DD)
        checkout: Check-out date (YYYY-MM-DD)
        daily_meals: Cost per day for meals (default: 75 CAD)
    
    Returns:
        Dictionary with meals total costs
    """
    checkin_date = datetime.strptime(checkin, "%Y-%m-%d")
    checkout_date = datetime.strptime(checkout, "%Y-%m-%d")
    nights = (checkout_date - checkin_date).days
    
    return {
        "meals": round(nights * daily_meals, 2)
    }

def _compose_candidates(
    flights: List[Dict[str, Any]], 
    hotels: List[Dict[str, Any]], 
    transit: Dict[str, Any],
    activities: List[Dict[str, Any]],
    meal: Optional[Dict[str, Any]], 
    currency: str,
    budget: float,
    max_flights: int = 2,
    max_hotels: int = 2
) -> List[Dict[str, Any]]:
    """
    Compose candidate travel packages from flights, hotels, and activities
    
    Args:
        flights: List of flight offers
        hotels: List of hotel offers (Amadeus format)
        transit: Transit cost dictionary
        activities: List of activities fetched from the API
        meal: Meal cost dictionary (optional, defaults to 0)
        currency: Currency code
        budget: Maximum budget
        max_flights: Maximum number of flights to consider (default: 2)
        max_hotels: Maximum number of hotels to consider (default: 2)
    
    Returns:
        List of candidate packages with total costs
    """
    # Validate we have at least flights or hotels
    if not flights and not hotels:
        raise ValueError("No flights or hotels available - cannot create packages")
    
    # Default meal to 0 if not provided
    if meal is None:
        meal = {"meals": 0}
    
    combos = []
    
    # Sort activities by price (ascending)
    sorted_activities = sorted(activities, key=lambda x: float(x["price"]["amount"]))

    # Case 1: Only hotels available (no flights)
    if not flights and hotels:
        print(f"\n⚠️  No flights available - creating hotel-only packages")
        top_hotels = hotels[:max_hotels]
        for h in top_hotels:
            try:
                if "offers" not in h or len(h["offers"]) == 0:
                    continue

                offer = h["offers"][0]
                hotel_price = float(offer["price"]["total"])  # Ensure hotel_price is a float
                hotel_currency = offer["price"].get("currency", currency)  # Use default currency if missing
                hotel_name = h.get("hotel", {}).get("name", "Unknown Hotel")
                hotel_id = h.get("hotel", {}).get("hotelId", "unknown")
                room_description = offer.get("room", {}).get("description", {}).get("text", "No description available")

                # Convert hotel price to the target currency if needed
                if hotel_currency != currency:
                    hotel_price = convert_currency(hotel_price, hotel_currency, currency)
                    hotel_currency = currency  # Update the currency to the target currency

                transit_cost = float(transit.get("total", 0))  # Ensure transit_cost is a float
                meals_cost = float(meal.get("meals", 0))  # Ensure meals_cost is a float

                # Process activities: convert prices and filter within the remaining budget
                remaining_budget = budget - (hotel_price + transit_cost + meals_cost)
                affordable_activities = []
                current_activities_total = 0

                for activity in sorted_activities:
                    activity_currency = activity["price"].get("currencyCode", currency)  # Use default currency if missing
                    print(f"🔍 Processing activity: {activity.get('name', 'Unknown')} - Currency: {activity_currency}")  # Log currency code

                    # Convert activity price to the target currency if needed
                    if activity_currency != currency:
                        activity["price"]["amount"] = convert_currency(
                            float(activity["price"]["amount"]),
                            activity_currency,
                            currency
                        )
                        activity["price"]["currencyCode"] = currency
                        activity["price"]["amount"] = round(activity["price"]["amount"], 2)

                    # Filter activities within the remaining budget
                    activity_price = float(activity["price"]["amount"])  # Ensure price is a float
                    if activity_price <= remaining_budget:
                        affordable_activities.append(activity)
                        current_activities_total += activity_price
                        remaining_budget -= activity_price  # Update remaining budget
                    else:
                        break  # Stop adding activities once the budget is exceeded

                # Calculate total activity cost
                total_activity_cost = current_activities_total

                total = hotel_price + transit_cost + total_activity_cost + meals_cost

                combos.append({
                    "flight": None,
                    "hotel": {
                        "id": hotel_id,
                        "name": hotel_name,
                        "total": hotel_price,
                        "currency": hotel_currency,
                        "offer_id": offer.get("id", "unknown"),
                        "room_description": room_description  # Add room description here
                    },
                    "transit": transit,
                    "activities": {
                        "total": total_activity_cost,
                        "details": affordable_activities  # Include filtered activity data
                    },
                    "meals": meals_cost,
                    "currency": currency,
                    "total": round(total, 2)
                })

                print(f"✅ Hotel-only package: ${total:.2f}")
            except (KeyError, ValueError, TypeError) as e:
                print(f"⚠️  Skipping hotel - {str(e)}")
                continue

        if combos:
            return combos
        else:
            raise ValueError("No valid hotel packages could be created")
    
    # Case 2: Only flights available (no hotels)
    if flights and not hotels:
        print(f"\n⚠️  No hotels available - creating flight-only packages")
        top_flights = flights[:max_flights * 2]  # Get more flights when no hotels
        for f in top_flights:
            try:
                flight_price = float(f["price"]["total"])
                flight_currency = f["price"].get("currency", currency)
                transit_cost = float(transit.get("total", 0))
                meals_cost = float(meal.get("meals", 0))

                # Process activities: convert prices and filter within the remaining budget
                remaining_budget = budget - (flight_price + transit_cost + meals_cost)
                affordable_activities = []
                current_activities_total = 0

                for activity in sorted_activities:
                    activity_currency = activity["price"].get("currencyCode", currency)  # Use default currency if missing
                    print(f"🔍 Processing activity: {activity.get('name', 'Unknown')} - Currency: {activity_currency}" ) # Log currency code

                    # Convert activity price to the target currency if needed
                    if activity_currency != currency:
                        activity["price"]["amount"] = convert_currency(
                            float(activity["price"]["amount"]),
                            activity_currency,
                            currency
                        )
                        activity["price"]["currencyCode"] = currency
                        activity["price"]["amount"] = round(activity["price"]["amount"], 2)

                    # Filter activities within the remaining budget
                    activity_price = float(activity["price"]["amount"])  # Ensure price is a float
                    if activity_price <= remaining_budget:
                        affordable_activities.append(activity)
                        current_activities_total += activity_price
                        remaining_budget -= activity_price  # Update remaining budget
                    else:
                        break  # Stop adding activities once the budget is exceeded

                # Calculate total activity cost
                total_activity_cost = current_activities_total

                total = flight_price + transit_cost + total_activity_cost + meals_cost

                combos.append({
                    "flight": {
                        "id": f.get("id", "unknown"),
                        "price": flight_price,
                        "currency": flight_currency
                    },
                    "hotel": None,
                    "transit": transit,
                    "activities": {
                        "total": total_activity_cost,
                        "details": affordable_activities  # Include filtered activity data
                    },
                    "meals": meals_cost,
                    "currency": currency,
                    "total": round(total, 2)
                })

                print(f"✅ Flight-only package: ${total:.2f}")
            except (KeyError, ValueError, TypeError) as e:
                print(f"⚠️  Skipping flight - {str(e)}")
                continue

        if combos:
            return combos
        else:
            raise ValueError("No valid flight packages could be created")
    
    # Case 3: Both flights and hotels available
    top_flights = flights[:max_flights]
    top_hotels = hotels[:max_hotels]

    print(f"\n🔄 Processing {len(top_flights)} flights × {len(top_hotels)} hotels...")

    for f in top_flights:
        try:
            flight_price = float(f["price"]["total"])
            flight_currency = f["price"].get("currency", currency)
            
            # Extract detailed flight information
            carrier_code = f.get("validatingAirlineCodes", ["Unknown"])[0]
            
            flight_details = {
                "id": f.get("id", "unknown"),
                "price": flight_price,
                "currency": flight_currency,
                "airline_code": carrier_code,
                "itineraries": []
            }
            
            # Parse itineraries (outbound and return)
            for itinerary in f.get("itineraries", []):
                itinerary_info = {
                    "duration": itinerary.get("duration", "N/A"),
                    "segments": []
                }
                
                for segment in itinerary.get("segments", []):
                    aircraft_code = segment.get("aircraft", {}).get("code", "N/A")
                    carrier = segment.get("carrierCode", "N/A")
                    
                    segment_info = {
                        "departure": {
                            "airport": segment["departure"].get("iataCode", "N/A"),
                            "terminal": segment["departure"].get("terminal", ""),
                            "time": segment["departure"].get("at", "N/A")
                        },
                        "arrival": {
                            "airport": segment["arrival"].get("iataCode", "N/A"),
                            "terminal": segment["arrival"].get("terminal", ""),
                            "time": segment["arrival"].get("at", "N/A")
                        },
                        "carrier_code": carrier,
                        "flight_number": f"{carrier}{segment.get('number', '')}",
                        "aircraft_code": aircraft_code,
                        "duration": segment.get("duration", "N/A"),
                        "stops": segment.get("numberOfStops", 0)
                    }
                    itinerary_info["segments"].append(segment_info)
                
                flight_details["itineraries"].append(itinerary_info)

            for h in top_hotels:
                try:
                    # Amadeus hotel format: h["offers"][0]["price"]["total"]
                    if "offers" not in h or len(h["offers"]) == 0:
                        print(f"⚠️  Skipping hotel - no offers available")
                        continue

                    # Get first offer
                    offer = h["offers"][0]
                    hotel_price = float(offer["price"]["total"])  # Ensure hotel_price is a float
                    hotel_currency = offer["price"].get("currency", currency)  # Use default currency if missing
                    hotel_name = h.get("hotel", {}).get("name", "Unknown Hotel")
                    hotel_id = h.get("hotel", {}).get("hotelId", "unknown")
                    room_description = offer.get("room", {}).get("description", {}).get("text", "No description available")

                    # Convert hotel price to the target currency if needed
                    if hotel_currency != currency:
                        hotel_price = convert_currency(hotel_price, hotel_currency, currency)
                        hotel_currency = currency  # Update the currency to the target currency

                    transit_cost = float(transit.get("total", 0))
                    meals_cost = float(meal.get("meals", 0))

                    # Process activities: convert prices and filter within the remaining budget
                    remaining_budget = budget - (flight_price + hotel_price + transit_cost + meals_cost)
                    affordable_activities = []
                    current_activities_total = 0

                    for activity in sorted_activities:
                        activity_currency = activity["price"].get("currencyCode", currency)  # Use default currency if missing

                        # Convert activity price to the target currency if needed
                        if activity_currency != currency:
                            activity["price"]["amount"] = convert_currency(
                                float(activity["price"]["amount"]),
                                activity_currency,
                                currency
                            )
                            activity["price"]["currencyCode"] = currency
                            activity["price"]["amount"] = round(activity["price"]["amount"], 2)

                        # Filter activities within the remaining budget
                        activity_price = float(activity["price"]["amount"])  # Ensure price is a float
                        if activity_price <= remaining_budget:
                            affordable_activities.append(activity)
                            current_activities_total += activity_price
                            remaining_budget -= activity_price  # Update remaining budget
                        else:
                            break  # Stop adding activities once the budget is exceeded

                    # Calculate total activity cost
                    total_activity_cost = current_activities_total

                    # Calculate the total cost for this combination
                    total = flight_price + hotel_price + transit_cost + total_activity_cost + meals_cost

                    combos.append({
                        "flight": flight_details,  # Enhanced flight details
                        "hotel": {
                            "id": hotel_id,
                            "name": hotel_name,
                            "total": hotel_price,
                            "currency": hotel_currency,
                            "offer_id": offer.get("id", "unknown"),
                            "room_description": room_description  # Add room description here
                        },
                        "transit": transit,
                        "activities": {
                            "total": total_activity_cost,
                            "details": affordable_activities  # Include filtered activity data
                        },
                        "meals": meals_cost,
                        "currency": currency,
                        "total": round(total, 2)
                    })

                    # Add debug log for total calculation
                    print(f"✅ Combo: Flight ${flight_price:.2f} {flight_currency} + Hotel ${hotel_price:.2f} {hotel_currency} + Transit ${transit_cost:.2f} + Activities ${total_activity_cost:.2f} + Meals ${meals_cost:.2f} = ${total:.2f}")

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
    activities: List[Dict[str, Any]],
    fx_snapshot: Dict[str, Any],
    budget: float, 
    currency: str,
    destination: str,
    depart_date: str,
    return_date: str,
    travel_style: str = "moderate",
    max_results: int = 3
) -> List[Dict[str, Any]]:

    if budget <= 0:
        raise ValueError("Budget must be positive")
    
    print(f"\n🧮 Calculating meal and transit costs...")
    
    # Calculate minimum REQUIRED costs (flights + hotels only)
    # Activities are optional and will be added later based on remaining budget
    
    # Get minimum flight cost (no conversion needed - already in target currency)
    min_flight_cost = min((float(f["price"]["total"]) for f in flights), default=0) if flights else 0
    
    # Get minimum hotel cost and convert to target currency
    min_hotel_cost = 0
    if hotels:
        hotel_prices = []
        for h in hotels:
            if h.get("offers") and len(h["offers"]) > 0:
                price = float(h["offers"][0]["price"]["total"])
                hotel_currency = h["offers"][0]["price"].get("currency", currency)
                if hotel_currency != currency:
                    price = convert_currency(price, hotel_currency, currency)
                hotel_prices.append(price)
        min_hotel_cost = min(hotel_prices, default=0)
    
    # Reserve some budget for activities (e.g., 20% of total budget or a fixed amount)
    activity_budget_reserve = min(budget * 0.2, 500)  # Reserve 20% or $500, whichever is smaller
    
    estimated_remaining = budget - min_flight_cost - min_hotel_cost - activity_budget_reserve
    
    print(f"💰 Budget Analysis:")
    print(f"   Total Budget: ${budget:.2f} {currency}")
    print(f"   Min Flight: ${min_flight_cost:.2f} {currency}")
    print(f"   Min Hotel: ${min_hotel_cost:.2f} {currency}")
    print(f"   Activity Reserve: ${activity_budget_reserve:.2f} {currency}")
    print(f"   Estimated for meals/transit: ${max(estimated_remaining, 0):.2f} {currency}")
    
    # Calculate meal and transit costs using LLM
    try:
        print("🤖 Using AI to estimate meal and transit costs...")
        llm_costs = calculate_costs_with_llm(
            destination=destination,
            depart_date=depart_date,
            return_date=return_date,
            total_budget=budget,
            remaining_budget=max(estimated_remaining, 0),
            currency=currency,
            travel_style=travel_style
        )
        
        meal = {"meals": llm_costs["total_meals"]}
        transit = {"total": llm_costs["total_transit"]}
        
        print(f"AI calculated meals: ${meal['meals']:.2f}")
        print(f"AI calculated transit: ${transit['total']:.2f}")
        print(f"AI Reasoning: {llm_costs['reasoning']}")
    except Exception as e:
        print(f"LLM calculation failed: {str(e)}, using fallback values")
        # Use manual calculation as fallback
        meal = calculate_meal_costs(depart_date, return_date)
        transit = {"total": 50.0}
        print(f"Fallback meal calculation: ${meal['meals']:.2f}")
        print(f"Fallback transit cost: ${transit['total']:.2f}")
    
    # Compose candidates (handles empty flights or hotels gracefully)
    candidates = _compose_candidates(flights, hotels, transit, activities, meal, currency, budget)
    
    # Greedy: choose those within budget, sort by total ascending
    within = [c for c in candidates if c["total"] <= budget]
    within.sort(key=lambda x: x["total"])
    
    print(f"\n{len(within)} packages within budget of ${budget:.2f} {currency}")
    
    # Get top results
    if within:
        top = within[:max_results]
    else:
        # If nothing within budget, return cheapest options
        print(f"No packages within budget, returning {max_results} cheapest options")
        top = sorted(candidates, key=lambda x: x["total"])[:max_results]

    # Annotate with FX snapshot and status
    for q in top:
        q["fxSnapshot"] = {"base": fx_snapshot["base"], "ts": fx_snapshot["ts"]}
        q["status"] = "within-budget" if q["total"] <= budget else "over-budget"
        q["budgetRemaining"] = round(budget - q["total"], 2) if q["total"] <= budget else 0
    
    return top