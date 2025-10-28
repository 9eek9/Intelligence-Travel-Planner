# Budget Type
- Luxury, 
- Standard, 
- Budget-Friendly

# Summary
- Loads itinerary JSON from existing DB/API

- Calculates activity + meal costs from her Google data

- Calls live APIs (FX, Expedia, etc.)

- Combines & optimizes totals

# API Method
POST /budget/quotes?itinerary_id=Toronto_3_2_true&currency=CAD&budget=1200

# Flights (live prices, bookability & re-pricing)

Amadeus for Developers – flight search + final-price revalidation 
https://developers.amadeus.com/self-service/category/flights/api-doc/flight-offers-search?utm_source=chatgpt.com

Skyscanner Flights Live Pricing - 
https://developers.skyscanner.net/docs/flights-live-prices/overview?utm_source=chatgpt.com


Duffel Flights – modern REST, access to 300+ airline
https://duffel.com/flights?utm_source=chatgpt.com

Travelport (Travelport+) –
https://developer.travelport.com/?utm_source=chatgpt.com

## Stays / Lodging
Expedia Group Rapid – huge lodging inventory, full booking flow; SDKs and schema explorer. 
https://developers.expediagroup.com/docs/rapid?utm_source=chatgpt.com

Booking.com Demand API (affiliate partners) – accommodations (and cars, flights) 
https://api-docs.rentalcars.com/?utm_source=chatgpt.com


# Currency & FX (for consistent totals)

https://docs.openexchangerates.org/reference/api-introduction?utm_source=chatgpt.com
https://exchangerate.host/documentation?utm_source=chatgpt.com

ExchangeRate.host

Summary: Recommended API Stack for Student Project
Category	API	Reason
Flights	Amadeus Self-Service or Duffel Flights	Realistic data, sandbox access, no license fees
Hotels	Expedia Rapid API	Test mode data and rich rate breakdowns
Currency	ExchangeRate.host	Free and stable FX lookups
Optional	Skyscanner Live Pricing	If you need real-time benchmark prices



# Regression only estimates cost — it doesn’t choose the best combination.
Feed those prices into an optimizer (like a knapsack or linear programming model) to find the cheapest feasible combination of flights + hotels + transport.


# Use case

Trip: Toronto (YYZ) → Bangkok (BKK)

Dates: Dec 10–15 (5 nights)

Pax: 1 adult

Budget: CAD 1,200

Goal: Find the cheapest feasible combo (flight + hotel + local transit), show top results, and re-check prices at checkout.


# Flight search → then revalidate

POST /v2/shopping/flight-offers
{
  "currencyCode": "CAD",
  "originDestinations": [{
    "id": "1",
    "originLocationCode": "YYZ",
    "destinationLocationCode": "BKK",
    "departureDateTimeRange": { "date": "2025-12-10" }
  },{
    "id": "2",
    "originLocationCode": "BKK",
    "destinationLocationCode": "YYZ",
    "departureDateTimeRange": { "date": "2025-12-15" }
  }],
  "travelers": [{ "id": "1", "travelerType": "ADULT" }],
  "sources": ["GDS"],
  "max": 20
}


# Hotels with tax-inclusive totals
[
  { "id":"H1","name":"Sukhumvit Budget Inn","total": { "amount":"300.00","currency":"CAD" }, "nights":5, "rating":3.5 },
  { "id":"H2","name":"Riverside Stay","total": { "amount":"360.00","currency":"CAD" }, "nights":5, "rating":4.0 }
]


# Local transit cost (airport transfer + daily)

If we want to put constant price like Transitland
Airport rail link + BTS day passes (example assumption for demo):
 - Airport transfer: CAD 15.00
 - Local transit (5 days): CAD 5.00/day × 5 = 25.00
 - Transit subtotal: CAD 40.00


 ## Options you found

Flights

- Air Canada (YYZ → BKK, 1 stop) = CAD 825.00

- Thai Airways (YYZ → BKK, 1 stop) = CAD 760.00

Hotels

- Sukhumvit Budget Inn (3★) = CAD 300.00 (5 nights, taxes included)

- Riverside Stay (4★) = CAD 360.00 (5 nights, taxes included)

Extras for any combo

 - Local transit total = CAD 40.00
 - Weather/contingency buffer = CAD 20.00
 - Budget = CAD 1,200

# Build combos & totals
## Combo A = Air Canada + Sukhumvit Budget Inn

Flight: 825.00

Hotel: 300.00

Transit: 40.00

Buffer: 20.00
Total = 825 + 300 + 40 + 20 = 1,185 CAD ✅ under budget

## Combo B = Thai Airways + Riverside Stay

Flight: 760.00

Hotel: 360.00

Transit: 40.00

Buffer: 20.00
Total = 760 + 360 + 40 + 20 = 1,180 CAD ✅ under budget

## Result: both fit the 1,200 CAD budget, but Thai Airways + Riverside Stay is cheaper (1,180) → that’s the optimizer’s pick.
==========================================
# What to do (step-by-step)

- Pick 1–2 flight options you want to compare (e.g., the two cheapest after repricing).
- Pick 1–2 hotel options (e.g., two best by price/rating).
- Add fixed extras that apply to any combo:
- transit_total (e.g., 40 CAD)
- weather_buffer (e.g., 20 CAD)
- Build combos = each flight × each hotel.
- Total = flight + hotel + transit + buffer.

----------------------------
*** # choose the best combo
------------------------------
Compare to budget; pick the lowest total that’s ≤ budget.
Label & return as “Combo A”, “Combo B” with names, price breakdown, total, and status.

{
  "currency": "CAD",
  "budget": 1200,
  "combos": [
    {
      "label": "Combo A",
      "flight": "Air Canada (YYZ→BKK)",
      "hotel": "Sukhumvit Budget Inn (3★)",
      "total": 1185,
      "status": "within-budget"
    },
    {
      "label": "Combo B",
      "flight": "Thai Airways (YYZ→BKK)",
      "hotel": "Riverside Stay (4★)",
      "total": 1180,
      "status": "within-budget"
    }
  ],
  "winner": "Combo B"
}




