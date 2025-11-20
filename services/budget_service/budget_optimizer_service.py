import os
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
from datetime import datetime

from flights_client import get_flight_offers
from hotels_client import get_hotel_offers
from activities_client import fetch_activities_by_city_name
# from fx_client import convert_currency
from optimizer import compose_and_optimize, calculate_meal_costs

load_dotenv()

class BudgetOptimizerService:
    """
    Main service that coordinates flights, hotels, FX, and optimization
    """
    
    def __init__(self):
        self.amadeus_key = os.getenv("AMADEUS_API_KEY")
        self.amadeus_secret = os.getenv("AMADEUS_API_SECRET")
        self.exchange_api_key = os.getenv("EXCHANGERATE_API_KEY")
    
    def optimize_trip(
        self,
        origin: str,
        destination: str,
        city_code: str,
        depart_date: str,
        return_date: str,
        budget: float,
        currency: str = "CAD",
        transit_cost: Optional[float] = None,
        activities_cost: Optional[float] = None,
        meals_cost: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get optimized travel packages within budget
        """
        print("\n" + "="*60)
        print("🚀 BUDGET OPTIMIZER SERVICE")
        print("="*60)
        
        # 1. Get flight offers
        print(f"\n🔍 Fetching flights from {origin} to {destination}...")
        flight_data = get_flight_offers(
            origin, 
            destination, 
            depart_date, 
            return_date, 
            self.amadeus_key, 
            self.amadeus_secret
        )
        flights = flight_data.get("data", [])
        print(f"✅ Found {len(flights)} flight options")

        # # Convert flight prices to the desired currency
        # print(f"\n💱 Converting flight prices to {currency}...")
        # for flight in flights:
        #     price = flight.get("price", {})
        #     if price.get("currency") != currency:
        #         original_price = float(price.get("total", 0))
        #         original_currency = price.get("currency")
        #         converted_price = convert_currency(original_price, original_currency, currency)
        #         flight["price"]["convertedTotal"] = converted_price
        #         flight["price"]["convertedCurrency"] = currency
        #         print(f"   Flight {flight['id']}: {original_price:.2f} {original_currency} → {converted_price:.2f} {currency}")

        # 2. Get hotel offers
        print(f"\n🔍 Fetching hotels in {destination}...")
        hotel_data = get_hotel_offers(
            destination, 
            depart_date, 
            return_date, 
            self.amadeus_key, 
            self.amadeus_secret,
            currency="EUR"  # Always fetch in EUR
        )
        hotels = hotel_data.get("data", [])
        print(f"✅ Found {len(hotels)} hotel options")

        # # # Convert hotel prices to the desired currency
        # # print(f"\n💱 Converting hotel prices to {currency}...")
        # for hotel in hotels:
        #     if "offers" in hotel and len(hotel["offers"]) > 0:
        #         offer = hotel["offers"][0]
        #         price_currency = offer["price"].get("currency", "EUR")
        #         original_price = float(offer["price"]["total"])
        #         if price_currency != currency:
        #             converted_price = convert_currency(original_price, price_currency, currency)
        #             offer["price"]["convertedTotal"] = converted_price
        #             offer["price"]["convertedCurrency"] = currency
        #             print(f"   {hotel['hotel']['name']}: {original_price:.2f} {price_currency} → {converted_price:.2f} {currency}")

        # 3. Fetch activities
        print(f"\n🔍 Fetching activities in {destination}...")
        activity_data = fetch_activities_by_city_name(
            destination, 
            depart_date, 
            return_date, 
            self.amadeus_key, 
            self.amadeus_secret
        )

        # Remove redundant activity price conversion logic
        # The activities_client already handles currency conversion

        # 4. Calculate costs
        if meals_cost is None:
            calculated_costs = calculate_meal_costs(
                depart_date, 
                return_date, 
                daily_meals=75.0
            )
            meals_cost = meals_cost or calculated_costs["meals"]
            print(f"\n💰 Calculated costs - Meals: ${meals_cost:.2f}")
        
        transit = {"total": transit_cost or 50.0}
        meal = {
            "meals": meals_cost
        }
        
        # 5. Get FX snapshot
        fx_snapshot = {
            "base": currency,
            "ts": datetime.now().isoformat(),
            "rates": {}
        }
        
        # 6. Optimize
        print(f"\n🎯 Optimizing packages for budget: ${budget:.2f} {currency}...")
        optimized = compose_and_optimize(
            flights,
            hotels,
            transit,
            activity_data,
            meal,
            fx_snapshot,
            budget,
            currency
        )
        
        return optimized


def main():
    """Example usage"""
    try:
        service = BudgetOptimizerService()
        
        results = service.optimize_trip(
            origin="Toronto",
            destination="Bangkok",
            depart_date="2025-12-25",
            return_date="2025-12-30",
            budget=3000,
            currency="CAD"
        )
        
        print("\n" + "="*60)
        print("🎉 OPTIMIZED TRAVEL PACKAGES")
        print("="*60)
        
        for i, package in enumerate(results, 1):
            print(f"\n📦 Package #{i}")
            print(f"   ✈️  Flight: {package['flight']['id']}")
            print(f"      Price: ${package['flight']['price']:.2f} {package['flight']['currency']}")
            print(f"   🏨 Hotel: {package['hotel']['name']}")
            print(f"      Price: ${package['hotel']['total']:.2f} {package['hotel']['currency']}")
            print(f"   🚌 Transit: ${package['transit']['total']:.2f}")
            print(f"   🎡 Activities: ${package['activities']:.2f}")
            print(f"   🍽️  Meals: ${package['meals']:.2f}")
            print(f"   " + "-"*40)
            print(f"   💰 TOTAL: ${package['total']:.2f} {package['currency']}")
            print(f"   📊 Status: {package['status']}")
            if package['budgetRemaining'] > 0:
                print(f"   💵 Budget Remaining: ${package['budgetRemaining']:.2f}")
        
        print("\n" + "="*60)
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()