
# from typing import Dict, Any, List

# def _activity_cost_for_types(types: list) -> float:
#     # Simple heuristic: parks free, museums 12 CAD, other 5 CAD
#     types = types or []
#     if "park" in types:
#         return 0.0
#     if "museum" in types:
#         return 12.0
#     return 5.0

# def _meal_cost_for_price_level(price_level) -> float:
#     # Google price_level 0–4, or None when unknown.
#     # Map to per-person cost in CAD.
#     if price_level is None:
#         return 20.0
#     # e.g., 15 + 5*level → level 2 ≈ 25
#     return float(15 + 5 * int(price_level))

# def estimate_activity_and_meal_cost(itinerary: Dict[str, Any], currency: str) -> Dict[str, float]:
#     activities_total = 0.0
#     meals_total = 0.0

#     for day in itinerary.get("plan_struct", []):
#         for a in day.get("attractions", []):
#             activities_total += _activity_cost_for_types(a.get("types", []))
#         for r in day.get("restaurants", []):
#             meals_total += _meal_cost_for_price_level(r.get("price_level"))

#     return {"activities": round(activities_total, 2), "meals": round(meals_total, 2), "currency": currency}

# def summarize_daily_costs(itinerary: Dict[str, Any], currency: str):
#     days = []
#     for day in itinerary.get("plan_struct", []):
#         a_sum = sum(_activity_cost_for_types(a.get("types", [])) for a in day.get("attractions", []))
#         m_sum = sum(_meal_cost_for_price_level(r.get("price_level")) for r in day.get("restaurants", []))
#         days.append({"day": day.get("day"), "activities": round(a_sum, 2), "meals": round(m_sum, 2), "currency": currency})
#     return days