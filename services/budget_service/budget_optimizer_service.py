import os
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
from datetime import datetime

from flights_client import get_flight_offers
from hotels_client import get_hotel_offers
from fx_client import convert_currency
from optimizer import compose_and_optimize, calculate_activity_meal_costs

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
        daily_activities: float = 50.0,
        daily_meals: float = 75.0
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
        
        if not flights:
            raise ValueError("No flights found")
        
        # 2. Get hotel offers
        print(f"\n🔍 Fetching hotels in {city_code}...")
        hotel_data = get_hotel_offers(
            city_code, 
            depart_date, 
            return_date, 
            self.amadeus_key, 
            self.amadeus_secret,
            currency=currency
        )
        
        hotels = hotel_data.get("data", [])
        print(f"✅ Found {len(hotels)} hotel options")
        
        if not hotels:
            raise ValueError("No hotels found")
        
        # 3. Convert hotel prices if needed
        print(f"\n💱 Converting hotel prices to {currency}...")
        for hotel in hotels:
            if "offers" in hotel and len(hotel["offers"]) > 0:
                offer = hotel["offers"][0]
                price_currency = offer["price"].get("currency", currency)
                
                if price_currency != currency:
                    original_price = float(offer["price"]["total"])
                    converted_price = convert_currency(original_price, price_currency, currency)
                    print(f"   {hotel['hotel']['name']}: {original_price:.2f} {price_currency} → {converted_price:.2f} {currency}")
                    offer["price"]["total"] = str(converted_price)
                    offer["price"]["currency"] = currency
                    offer["price"]["original_amount"] = original_price
                    offer["price"]["original_currency"] = price_currency
        
        # 4. Calculate costs
        if activities_cost is None or meals_cost is None:
            calculated_costs = calculate_activity_meal_costs(
                depart_date, 
                return_date, 
                daily_activities, 
                daily_meals
            )
            activities_cost = activities_cost or calculated_costs["activities"]
            meals_cost = meals_cost or calculated_costs["meals"]
            print(f"\n💰 Calculated costs - Activities: ${activities_cost:.2f}, Meals: ${meals_cost:.2f}")
        
        transit = {"total": transit_cost or 50.0}
        activity_meal = {
            "activities": activities_cost,
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
            activity_meal,
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
            origin="YYZ",
            destination="BKK",
            city_code="BKK",
            depart_date="2025-12-01",
            return_date="2025-12-05",
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