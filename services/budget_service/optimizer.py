from typing import List, Dict, Any, Optional
from datetime import datetime
from fx_client import convert_currency
from llm_cost_calculator import calculate_costs_with_llm

def _compose_candidates(
    flights: List[Dict[str, Any]], 
    hotels: List[Dict[str, Any]], 
    transit: Dict[str, Any],
    activities: List[Dict[str, Any]],
    meal: Optional[Dict[str, Any]], 
    currency: str,
    budget: float,
    transit_reasoning: Optional[str] = None,  # Add transit reasoning
    meals_reasoning: Optional[str] = None,  # Add meals reasoning
    max_flights: int = 3,
    max_hotels: int = 3
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
    seen_keys = set()  # Track unique flight+hotel combinations
    
    # Sort activities by price (ascending)
    sorted_activities = sorted(activities, key=lambda x: float(x["price"]["amount"]))

    # Case 1: Only hotels available (no flights)
    if not flights and hotels:
        print(f"\nNo flights available - creating hotel-only packages")
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
                    # Create a deep copy to avoid modifying the original
                    activity_copy = {
                        "name": activity.get("name"),
                        "price": {
                            "amount": float(activity["price"]["amount"]),
                            "currencyCode": activity["price"].get("currencyCode", currency)
                        },
                        "minimumDuration": activity.get("minimumDuration"),  # Fixed: Added closing quote
                        "bookingLink": activity.get("bookingLink")
                    }
                    
                    activity_currency = activity_copy["price"]["currencyCode"]
                    print(f"Processing activity: {activity_copy.get('name', 'Unknown')} - Currency: {activity_currency}")

                    # Convert activity price to the target currency if needed
                    if activity_currency != currency:
                        activity_copy["price"]["amount"] = convert_currency(
                            activity_copy["price"]["amount"],
                            activity_currency,
                            currency
                        )
                        activity_copy["price"]["currencyCode"] = currency
                        activity_copy["price"]["amount"] = round(activity_copy["price"]["amount"], 2)

                    # Filter activities within the remaining budget
                    activity_price = activity_copy["price"]["amount"]
                    if activity_price <= remaining_budget:
                        affordable_activities.append(activity_copy)
                        current_activities_total += activity_price
                        remaining_budget -= activity_price
                    else:
                        break

                # Calculate total activity cost
                total_activity_cost = current_activities_total

                total = hotel_price + transit_cost + total_activity_cost + meals_cost

                # Check for duplicates using Set
                unique_key = ("no-flight", hotel_id)
                if unique_key in seen_keys:
                    print(f"  ⏭️ Skipping duplicate: No flight + Hotel {hotel_id}")
                    continue
                
                seen_keys.add(unique_key)
                
                # Now append (only if not duplicate)
                combos.append({
                    "flight": None,
                    "hotel": {
                        "id": hotel_id,
                        "name": hotel_name,
                        "price": hotel_price,  # Changed from "total" to "price"
                        "currency": hotel_currency,
                        "offer_id": offer.get("id", "unknown"),
                        "room_description": room_description
                    },
                    "transit": {
                        **transit,
                        "reasoning": transit_reasoning
                    },
                    "activities": {
                        "total": total_activity_cost,
                        "details": affordable_activities
                    },
                    "meals": {
                        "total": meals_cost,
                        "reasoning": meals_reasoning
                    },
                    "currency": currency,
                    "total": round(total, 2)
                })

                print(f"Hotel-only package: ${total:.2f}")
            except (KeyError, ValueError, TypeError) as e:
                print(f"Skipping hotel - {str(e)}")
                continue

        if combos:
            return combos
        else:
            raise ValueError("No valid hotel packages could be created")
    
    # Case 2: Only flights available (no hotels)
    if flights and not hotels:
        print(f"\nNo hotels available - creating flight-only packages")
        top_flights = flights[:max_flights * 2]  # Get more flights when no hotels
        for f in top_flights:
            try:
                flight_id = f.get("id", "unknown")
                flight_price = float(f["price"]["total"])
                flight_currency = f["price"].get("currency", currency)
                transit_cost = float(transit.get("total", 0))
                meals_cost = float(meal.get("meals", 0))

                # Process activities: convert prices and filter within the remaining budget
                remaining_budget = budget - (flight_price + transit_cost + meals_cost)
                affordable_activities = []
                current_activities_total = 0

                for activity in sorted_activities:
                    # Create a deep copy to avoid modifying the original
                    activity_copy = {
                        "name": activity.get("name"),
                        "price": {
                            "amount": float(activity["price"]["amount"]),
                            "currencyCode": activity["price"].get("currencyCode", currency)
                        },
                        "minimumDuration": activity.get("minimumDuration"),  # Fixed: Added closing quote
                        "bookingLink": activity.get("bookingLink")
                    }
                    
                    activity_currency = activity_copy["price"]["currencyCode"]
                    print(f"Processing activity: {activity_copy.get('name', 'Unknown')} - Currency: {activity_currency}" ) # Log currency code

                    # Convert activity price to the target currency if needed
                    if activity_currency != currency:
                        activity_copy["price"]["amount"] = convert_currency(
                            activity_copy["price"]["amount"],
                            activity_currency,
                            currency
                        )
                        activity_copy["price"]["currencyCode"] = currency
                        activity_copy["price"]["amount"] = round(activity_copy["price"]["amount"], 2)

                    # Filter activities within the remaining budget
                    activity_price = activity_copy["price"]["amount"]  # Ensure price is a float
                    if activity_price <= remaining_budget:
                        affordable_activities.append(activity_copy)
                        current_activities_total += activity_price
                        remaining_budget -= activity_price  # Update remaining budget
                    else:
                        break  # Stop adding activities once the budget is exceeded

                # Calculate total activity cost
                total_activity_cost = current_activities_total

                total = flight_price + transit_cost + total_activity_cost + meals_cost

                # Check for duplicates using Set
                unique_key = (flight_id, "no-hotel")
                if unique_key in seen_keys:
                    print(f"Skipping duplicate: Flight {flight_id} + No hotel")
                    continue
                
                seen_keys.add(unique_key)
                
                # Now append (only if not duplicate)
                combos.append({
                    "flight": {
                        "id": flight_id,
                        "price": flight_price,
                        "currency": flight_currency
                    },
                    "hotel": None,
                    "transit": {
                        **transit,
                        "reasoning": transit_reasoning
                    },
                    "activities": {
                        "total": total_activity_cost,
                        "details": affordable_activities
                    },
                    "meals": {
                        "total": meals_cost,
                        "reasoning": meals_reasoning
                    },
                    "currency": currency,
                    "total": round(total, 2)
                })

                print(f"Flight-only package: ${total:.2f}")
            except (KeyError, ValueError, TypeError) as e:
                print(f"Skipping flight - {str(e)}")
                continue

        if combos:
            return combos
        else:
            raise ValueError("No valid flight packages could be created")
    
    # Case 3: Both flights and hotels available
    top_flights = flights[:max_flights]
    top_hotels = hotels[:max_hotels]

    print(f"\nProcessing {len(top_flights)} flights × {len(top_hotels)} hotels...")

    for f in top_flights:
        try:
            flight_id = f.get("id", "unknown")
            flight_price = float(f["price"]["total"])
            flight_currency = f["price"].get("currency", currency)
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
                        print(f"Skipping hotel - no offers available")
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
                        # Create a deep copy to avoid modifying the original
                        activity_copy = {
                            "name": activity.get("name"),
                            "price": {
                                "amount": float(activity["price"]["amount"]),
                                "currencyCode": activity["price"].get("currencyCode", currency)
                            },
                            "minimumDuration": activity.get("minimumDuration"),      # Fixed: Added closing quote
                            "bookingLink": activity.get("bookingLink")
                        }
                        
                        activity_currency = activity_copy["price"]["currencyCode"]

                        # Convert activity price to the target currency if needed
                        if activity_currency != currency:
                            activity_copy["price"]["amount"] = convert_currency(
                                activity_copy["price"]["amount"],
                                activity_currency,
                                currency
                            )
                            activity_copy["price"]["currencyCode"] = currency
                            activity_copy["price"]["amount"] = round(activity_copy["price"]["amount"], 2)

                        # Filter activities within the remaining budget
                        activity_price = activity_copy["price"]["amount"]  # Ensure price is a float
                        if activity_price <= remaining_budget:
                            affordable_activities.append(activity_copy)
                            current_activities_total += activity_price
                            remaining_budget -= activity_price  # Update remaining budget
                        else:
                            break  # Stop adding activities once the budget is exceeded

                    # Calculate total activity cost
                    total_activity_cost = current_activities_total

                    # Calculate the total cost for this combination
                    total = flight_price + hotel_price + transit_cost + total_activity_cost + meals_cost
                    if any(combo["total"] == round(total, 2) for combo in combos):
                        print(f"totals exist in combos",round(total, 2))
                        continue


                    combos.append({
                        "flight": flight_details,
                        "hotel": {
                            "id": hotel_id,
                            "name": hotel_name,
                            "price": hotel_price,
                            "currency": hotel_currency,
                            "offer_id": offer.get("id", "unknown"),
                            "room_description": room_description
                        },
                        "transit": {
                            **transit,
                            "reasoning": transit_reasoning
                        },
                        "activities": {
                            "total": total_activity_cost,
                            "details": affordable_activities
                        },
                        "meals": {
                            "total": meals_cost,
                            "reasoning": meals_reasoning
                        },
                        "currency": currency,
                        "total": round(total, 2)
                    })

                    
                except (KeyError, ValueError, TypeError) as e:
                    print(f"Skipping hotel combination - {str(e)}")
                    continue

        except (KeyError, ValueError, TypeError) as e:
            print(f"Skipping flight - {str(e)}")
            continue
    
    if not combos:
        raise ValueError("No valid combinations could be created")
    
    print(f"\nCreated {len(combos)} unique package combinations")
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
    """
    Compose and optimize travel packages based on flight, hotel, and activity options
    
    Args:
        flights: List of flight offers
        hotels: List of hotel offers (Amadeus format)
        activities: List of activities fetched from the API
        fx_snapshot: Foreign exchange snapshot for currency conversion
        budget: Maximum budget for the trip
        currency: Currency code for the budget
        destination: Travel destination
        depart_date: Departure date
        return_date: Return date
        travel_style: Preferred travel style (e.g., luxury, moderate, budget)
        max_results: Maximum number of package results to return
    
    Returns:
        List of optimized travel packages
    """
    if budget <= 0:
        raise ValueError("Budget must be positive")
    
    print(f"\nCalculating meal and transit costs...")
    
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
    
    print(f"   Budget Analysis:")
    print(f"   Total Budget: ${budget:.2f} {currency}")
    print(f"   Min Flight: ${min_flight_cost:.2f} {currency}")
    print(f"   Min Hotel: ${min_hotel_cost:.2f} {currency}")
    print(f"   Activity Reserve: ${activity_budget_reserve:.2f} {currency}")
    print(f"   Estimated for meals/transit: ${max(estimated_remaining, 0):.2f} {currency}")
    
    # Calculate meal and transit costs using LLM
    transit_reasoning = None
    meals_reasoning = None
    
    
    try:
        print("Using AI to estimate meal and transit costs...")
        llm_costs = calculate_costs_with_llm(
            destination=destination,
            depart_date=depart_date,
            return_date=return_date,
            total_budget=budget,
            remaining_budget=max(estimated_remaining, 0),
            currency=currency,
            travel_style=travel_style
        )
        
        # Override with LLM values if successful
        meal = {"meals": llm_costs["total_meals"]}
        transit = {"total": llm_costs["total_transit"]}
        
        # Split reasoning by sentences
        full_reasoning = llm_costs.get("reasoning", "No reasoning provided")
        
        # Split by sentences (ending with .)
        sentences = [s.strip() + '.' for s in full_reasoning.split('.') if s.strip()]
        
        # Separate meals and transit sentences
        meals_sentences = []
        transit_sentences = []
        
        for sentence in sentences:
            sentence_lower = sentence.lower()
            # Check if sentence is about meals/food
            if any(keyword in sentence_lower for keyword in ['meal', 'food', 'eat', 'restaurant', 'street food', 'snack', 'drink', 'dining']):
                meals_sentences.append(sentence)
            # Check if sentence is about transit/transport
            elif any(keyword in sentence_lower for keyword in ['transit', 'transport', 'bts', 'mrt', 'grab', 'taxi', 'tuk-tuk', 'ride', 'public transport']):
                transit_sentences.append(sentence)
            # If neither, add to both (like intro sentences)
            elif 'these estimates' in sentence_lower or 'travel style' in sentence_lower:
                meals_sentences.append(sentence)
                transit_sentences.append(sentence)
        
        # Join sentences back together
        meals_reasoning = ' '.join(meals_sentences) if meals_sentences else full_reasoning
        transit_reasoning = ' '.join(transit_sentences) if transit_sentences else full_reasoning
        
        print(f"AI calculated meals: ${meal['meals']:.2f}")
        print(f"AI calculated transit: ${transit['total']:.2f}")
        print(f"\nMeals Reasoning:\n{meals_reasoning}")
        print(f"\nTransit Reasoning:\n{transit_reasoning}")
        
    except Exception as e:
        print(f"LLM calculation failed: {str(e)}, using fallback values")
        # Use fallback reasoning
        transit_reasoning = f"Using default transit estimate due to API limits. Estimated ${transit['total']:.2f} {currency} for local transportation."
        meals_reasoning = f"Using default meal estimate due to API limits. Estimated ${meal['meals']:.2f} {currency} for meals during the trip."
        
        print(f"Fallback meals: ${meal['meals']:.2f}")
        print(f"Fallback transit: ${transit['total']:.2f}")
    
    # Compose candidates (pass separate reasoning)
    candidates = _compose_candidates(
        flights, hotels, transit, activities, meal, currency, budget, 
        transit_reasoning=transit_reasoning,
        meals_reasoning=meals_reasoning
    )
    
    # Greedy: choose those within budget, sort by total ascending
    within = [c for c in candidates if c["total"] <= budget]
    within.sort(key=lambda x: x["total"])
    
    print(f"{len(within)} packages within budget of ${budget:.2f} {currency}")
    
    # Get top results
    if within:
        top = within[:max_results]
    else:
        print(f"No packages within budget, returning {max_results} cheapest options")
        top = sorted(candidates, key=lambda x: x["total"])[:max_results]

    # Annotate with FX snapshot and status
    for q in top:
        q["fxSnapshot"] = {"base": fx_snapshot["base"], "ts": fx_snapshot["ts"]}
        q["status"] = "within-budget" if q["total"] <= budget else "over-budget"
        q["budgetRemaining"] = round(budget - q["total"], 2) if q["total"] <= budget else 0
        
        # Verify reasoning is present in transit and meals
        if "transit" in q and isinstance(q["transit"], dict):
            if "reasoning" not in q["transit"]:
                q["transit"]["reasoning"] = transit_reasoning
        
        if "meals" in q and isinstance(q["meals"], dict):
            if "reasoning" not in q["meals"]:
                q["meals"]["reasoning"] = meals_reasoning
    
    return top  # Return only the packages list