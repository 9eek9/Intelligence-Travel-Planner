"""
LLM Cost Calculator Service
Uses AI to generate intelligent meal and transit cost estimates based on destination and travel context
"""

import os
import json
from datetime import datetime
from typing import Dict, Any, Optional
import google.generativeai as genai

# Configure Gemini (same pattern as sentiment_service.py)
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
genai.configure(api_key=GEMINI_KEY)

class LLMCostCalculator:
    """Calculate meal and transit costs using LLM intelligence"""
    
    def __init__(self):
        """Initialize LLM Cost Calculator with Gemini"""
        if not GEMINI_KEY:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
        # Use genai.GenerativeModel directly (same as sentiment_service)
        self.model = genai.GenerativeModel(MODEL_NAME)
    
    def calculate_costs(
        self,
        destination: str,
        depart_date: str,
        return_date: str,
        total_budget: float,
        remaining_budget: Optional[float] = None,
        currency: str = "CAD",
        travel_style: str = "moderate"
    ) -> Dict[str, Any]:
        """
        Calculate meal and transit costs using LLM
        
        Args:
            destination: City/country name
            depart_date: Departure date (YYYY-MM-DD)
            return_date: Return date (YYYY-MM-DD)
            total_budget: Total trip budget
            remaining_budget: Budget remaining after flights/hotels/activities (if known)
            currency: Currency code
            travel_style: 'budget', 'moderate', or 'luxury'
            
        Returns:
            Dict with daily_meals, daily_transit, total_meals, total_transit, and reasoning
        """
        # Calculate trip duration
        depart = datetime.strptime(depart_date, "%Y-%m-%d")
        return_dt = datetime.strptime(return_date, "%Y-%m-%d")
        days = (return_dt - depart).days
        
        prompt = self._build_prompt(
            destination, days, total_budget, remaining_budget, currency, travel_style
        )
        
        response = self._call_gemini(prompt)
        
        # Parse and validate response
        return self._parse_response(response, days)
    
    def _build_prompt(
        self,
        destination: str,
        days: int,
        total_budget: float,
        remaining_budget: Optional[float],
        currency: str,
        travel_style: str
    ) -> str:
        """Build the LLM prompt for cost estimation"""
        budget_context = f"- Total Trip Budget: {total_budget} {currency}\n"
        if remaining_budget is not None:
            budget_context += f"- Remaining Budget (for meals & transit): {remaining_budget} {currency}\n"
            budget_context += f"- Note: Flights, hotels, and a reserve for activities are already accounted for\n"
        
        return f"""You are a travel cost estimation expert. Calculate realistic daily meal and transit costs for a trip.

**Trip Details:**
- Destination: {destination}
- Duration: {days} days
{budget_context}- Travel Style: {travel_style}

**Instructions:**
1. Research typical costs in {destination}
2. Consider the travel style ({travel_style}):
   - Budget: Local food, public transport
   - Moderate: Mix of local and tourist spots, mix of transport
   - Luxury: Fine dining, taxis/private transport
3. Provide realistic daily estimates in {currency}
4. Ensure costs are appropriate for the destination's cost of living
5. Activities will be added separately, so focus ONLY on meals and local transit
{"6. IMPORTANT: Total meals + transit should fit within the remaining budget of " + str(remaining_budget) + " " + currency if remaining_budget else ""}

**Response Format (JSON only):**
{{
    "daily_meals": <float>,
    "daily_transit": <float>,
    "reasoning": "<brief explanation of your estimates>"
}}

Provide only valid JSON, no additional text."""
    
    def _call_gemini(self, prompt: str) -> str:
        """Call Gemini API (matching sentiment_service pattern)"""
        try:
            # Simple generate_content call (same as sentiment_service)
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            raise RuntimeError(f"Gemini API call failed: {str(e)}")
    
    def _parse_response(self, response: str, days: int) -> Dict[str, Any]:
        """Parse and validate LLM response"""
        # Clean response - remove markdown code blocks if present
        cleaned_response = response.strip()
        if cleaned_response.startswith("```json"):
            cleaned_response = cleaned_response[7:]
        if cleaned_response.startswith("```"):
            cleaned_response = cleaned_response[3:]
        if cleaned_response.endswith("```"):
            cleaned_response = cleaned_response[:-3]
        cleaned_response = cleaned_response.strip()
        
        try:
            # Parse JSON from LLM
            data = json.loads(cleaned_response)
            
            # Ensure required fields exist - no defaults!
            if "daily_meals" not in data or "daily_transit" not in data:
                raise ValueError("LLM response missing required fields: daily_meals or daily_transit")
            
            # Extract values from LLM response only
            daily_meals = float(data["daily_meals"])
            daily_transit = float(data["daily_transit"])
            reasoning = data.get("reasoning", "No reasoning provided")
            
            # Validate values are reasonable
            if daily_meals <= 0 or daily_transit <= 0:
                raise ValueError(f"Invalid LLM values: meals=${daily_meals}, transit=${daily_transit}")
            
            # Log what we got from LLM for debugging
            print(f"LLM Response - Meals: ${daily_meals}/day, Transit: ${daily_transit}/day")
            print(f"LLM Reasoning: {reasoning}")
            
            return {
                "daily_meals": round(daily_meals, 2),
                "daily_transit": round(daily_transit, 2),
                "total_meals": round(daily_meals * days, 2),
                "total_transit": round(daily_transit * days, 2),
                "reasoning": reasoning,
                "days": days,
                "source": "llm"
            }
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            # Don't use fallback values - raise error instead
            print(f"LLM parsing failed: {str(e)}")
            print(f"Raw LLM response: {response[:500]}")
            raise RuntimeError(f"Failed to get valid cost estimates from LLM: {str(e)}")


# Convenience function
def calculate_costs_with_llm(
    destination: str,
    depart_date: str,
    return_date: str,
    total_budget: float,
    remaining_budget: Optional[float] = None,
    currency: str = "CAD",
    travel_style: str = "moderate"
) -> Dict[str, Any]:
    """
    Calculate meal and transit costs using LLM (Gemini)
    
    Args:
        destination: City/country name
        depart_date: Departure date (YYYY-MM-DD)
        return_date: Return date (YYYY-MM-DD)
        total_budget: Total trip budget
        remaining_budget: Budget remaining after flights/hotels/activities
        currency: Currency code
        travel_style: 'budget', 'moderate', or 'luxury'
        
    Returns:
        Dict with cost estimates and reasoning
    """
    calculator = LLMCostCalculator()
    return calculator.calculate_costs(
        destination, depart_date, return_date, total_budget, remaining_budget, currency, travel_style
    )
