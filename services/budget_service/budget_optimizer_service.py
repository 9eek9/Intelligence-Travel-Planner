import os
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
from datetime import datetime

from flights_client import get_flight_offers
from hotels_client import get_hotel_offers
from activities_client import fetch_activities_by_city_name
# from fx_client import convert_currency
from optimizer import compose_and_optimize

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
        travel_style: str = "moderate",

    ) -> List[Dict[str, Any]]:
        """
        Get optimized travel packages within budget
        """
        print("\n" + "="*60)
        print("BUDGET OPTIMIZER SERVICE")
        print("="*60)
        
        # 1. Get flight offers
        print(f"\nFetching flights from {origin} to {destination}...")
        flight_data = get_flight_offers(
            origin, 
            destination, 
            depart_date, 
            return_date, 
            self.amadeus_key, 
            self.amadeus_secret
        )
        flights = flight_data.get("data", [])
        print(f"Found {len(flights)} flight options")

        # 2. Get hotel offers
        print(f"\nFetching hotels in {destination}...")
        hotel_data = get_hotel_offers(
            destination, 
            depart_date, 
            return_date, 
            self.amadeus_key, 
            self.amadeus_secret,
            currency="EUR"  # Always fetch in EUR
        )
        hotels = hotel_data.get("data", [])
        print(f"Found {len(hotels)} hotel options")


        # 3. Fetch activities
        print(f"\nFetching activities in {destination}...")
        activity_data = fetch_activities_by_city_name(
            destination, 
            depart_date, 
            return_date, 
            self.amadeus_key, 
            self.amadeus_secret
        )

        
        # 5. Get FX snapshot
        fx_snapshot = {
            "base": currency,
            "ts": datetime.now().isoformat(),
            "rates": {}
        }
        
        # 6. Optimize
        print(f"\nOptimizing packages for budget: ${budget:.2f} {currency}...")
        optimized = compose_and_optimize(
            flights,
            hotels,
            activity_data,
            fx_snapshot,
            budget,
            currency,
            destination,
            depart_date=depart_date,
            return_date=return_date,
            travel_style=travel_style,

        )
        
        return optimized


def main():
    """Example usage"""
    try:
        service = BudgetOptimizerService()
        
        results = service.optimize_trip(
            origin="Toronto",
            destination="Bangkok",
            depart_date="2026-03-25",
            return_date="2026-03-30",
            budget=6000,
            currency="CAD",
            travel_style="moderate" #"moderate/budget/luxury"
        )
        
        print("\n" + "="*60)
        print("OPTIMIZED TRAVEL PACKAGES")
        print("="*60)
        
        for i, package in enumerate(results, 1):
            print(f"\nPackage #{i}")
            print(f"   Flight: {package['flight']['id']}")
            print(f"      Price: ${package['flight']['price']:.2f} {package['flight']['currency']}")
            print(f"   Hotel: {package['hotel']['name']}")
            print(f"      Price: ${package['hotel']['total']:.2f} {package['hotel']['currency']}")
            print(f"   Transit: ${package['transit']['total']:.2f}")
            print(f"   Activities: ${package['activities']:.2f}")
            print(f"   Meals: ${package['meals']:.2f}")
            print(f"   " + "-"*40)
            print(f"   TOTAL: ${package['total']:.2f} {package['currency']}")
            print(f"   Status: {package['status']}")
            if package['budgetRemaining'] > 0:
                print(f" Budget Remaining: ${package['budgetRemaining']:.2f}")
        
        print("\n" + "="*60)
        
    except Exception as e:
        print(f"\nError: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()