"""
# Budget Routes Complete Guide

## 📋 Table of Contents
1. [Overview](#overview)
2. [Route Comparison](#route-comparison)
3. [When to Use Which Route](#when-to-use-which-route)
4. [API Endpoints Reference](#api-endpoints-reference)
5. [Integration Examples](#integration-examples)
6. [Use Cases](#use-cases)

---

## 🎯 Overview

Your SmartTravelSystem has **TWO types of budget routes**:

### **Type 1: Travel Package Optimizer** (No ML)
- **Purpose:** Find complete travel packages (flights + hotels + activities)
- **Technology:** Amadeus API + optimization algorithms
- **Use Case:** User wants to book actual travel

### **Type 2: Budget Allocation Predictor** (With ML/Rules)
- **Purpose:** Suggest how to split budget across categories
- **Technology:** Machine Learning model OR rule-based system
- **Use Case:** User wants budget planning advice

---

## 📊 Route Comparison

| Feature | `/optimize-trip` | `/ml/optimize` |
|---------|------------------|----------------|
| **Purpose** | Find bookable packages | Budget allocation advice |
| **Uses ML?** | ❌ No | ✅ Yes (or rules) |
| **Data Source** | Amadeus API | ML model / rules |
| **Output** | Complete packages | Percentage breakdown |
| **Bookable?** | ✅ Yes | ❌ No (advice only) |
| **Returns** | Flight/hotel details | Allocation percentages |

---

## 🔄 When to Use Which Route

### **Scenario 1: User Wants Complete Travel Package**
**Question:** "Find me flights + hotels within my $3,000 budget"

✅ **Use:** `POST /api/budget/optimize-trip`

**Request:**
```json
{
  "origin": "YYZ",
  "destination": "BKK",
  "city_code": "BKK",
  "depart_date": "2025-12-01",
  "return_date": "2025-12-05",
  "budget": 3000,
  "currency": "CAD"
}
```

**Response:**
```json
{
  "success": true,
  "packages": [
    {
      "flight": {
        "price": 800,
        "airline": "Emirates",
        "departure": "10:30",
        "arrival": "14:45"
      },
      "hotel": {
        "price": 150,
        "name": "Bangkok Plaza Hotel",
        "rating": 4.5
      },
      "activities": 200,
      "meals": 300,
      "total": 1450,
      "status": "within-budget"
    }
  ],
  "total_packages": 3
}
```

---

### **Scenario 2: User Wants Budget Allocation Advice**
**Question:** "I have $3,000 for Paris - how much should I spend on hotels vs food?"

✅ **Use:** `POST /api/budget/ml/optimize`

**Request:**
```json
{
  "destination": "Paris",
  "duration": 7,
  "total_budget": 3000,
  "travelers": 2,
  "purpose": "romantic",
  "accommodation_type": "hotel"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "allocation_percentages": {
      "accommodation": 0.42,
      "transportation": 0.23,
      "food": 0.18,
      "activities": 0.12,
      "miscellaneous": 0.05
    },
    "allocation_amounts": {
      "accommodation": 1260,
      "transportation": 690,
      "food": 540,
      "activities": 360,
      "miscellaneous": 150
    },
    "total_budget": 3000,
    "method": "ml",
    "confidence": "high",
    "tips": [
      "💡 Your accommodation budget is high. Consider Airbnb or hostels to save money.",
      "💰 Keep 20% of miscellaneous budget as emergency reserve."
    ],
    "feedback_id": 123
  },
  "message": "Budget allocation calculated using ml"
}
```

---

## 📡 API Endpoints Reference

### **Group 1: Travel Package Routes (No ML)**

#### 1. Get Multiple Packages
```
POST /api/budget/optimize-trip
```

**Description:** Returns up to 3 optimized packages sorted by price

**Request Body:**
```json
{
  "origin": "YYZ",
  "destination": "BKK",
  "city_code": "BKK",
  "depart_date": "2025-12-01",
  "return_date": "2025-12-05",
  "budget": 3000,
  "currency": "CAD",
  "transit_cost": 50,
  "activities_cost": 200,
  "meals_cost": 300,
  "daily_activities": 50.0,
  "daily_meals": 75.0
}
```

**Response:** Array of complete travel packages

---

#### 2. Get Best Package Only
```
POST /api/budget/optimize-trip/best
```

**Description:** Returns only the cheapest package within budget

**Request Body:** Same as above

**Response:** Single best package

---

#### 3. Stream Optimization Progress
```
POST /api/budget/optimize-trip/stream
```

**Description:** Returns real-time progress via Server-Sent Events (SSE)

**Response:** Streaming events showing progress

---

#### 4. Convert Currency
```
GET /api/budget/convert-currency?amount=100&from_currency=USD&to_currency=CAD
```

**Description:** Convert between currencies using real-time rates

---

### **Group 2: ML Budget Allocation Routes**

#### 1. Get ML Budget Allocation
```
POST /api/budget/ml/optimize
```

**Description:** Get smart budget allocation using ML or rules

**Request Body:**
```json
{
  "destination": "Paris",
  "duration": 7,
  "total_budget": 3000,
  "travelers": 2,
  "region": "Europe",
  "season": "peak",
  "purpose": "romantic",
  "accommodation_type": "hotel"
}
```

**Required Fields:**
- `destination` (string)
- `duration` (integer, >= 1)
- `total_budget` (float, > 0)

**Optional Fields:**
- `travelers` (integer, default: 1)
- `region` (string)
- `season` (string: "peak", "off_peak", "shoulder")
- `purpose` (string: "leisure", "business", "family", "adventure", "romantic")
- `accommodation_type` (string: "hotel", "hostel", "airbnb", "resort", "apartment")

---

#### 2. Submit Actual Spending
```
PUT /api/budget/ml/feedback/{feedback_id}/actual-spending
```

**Description:** Submit actual spending after trip completion (for ML improvement)

**Request Body:**
```json
{
  "accommodation": 1300.00,
  "transportation": 650.00,
  "food": 580.00,
  "activities": 320.00,
  "miscellaneous": 150.00
}
```

---

#### 3. Submit User Rating
```
PUT /api/budget/ml/feedback/{feedback_id}/rating
```

**Description:** Rate the budget recommendation quality

**Request Body:**
```json
{
  "rating": 5,
  "was_helpful": true,
  "comments": "Very accurate recommendations!"
}
```

---

#### 4. Get Feedback History
```
GET /api/budget/ml/feedback/history?user_id=1&limit=10
```

**Description:** Get user's previous budget allocations

---

#### 5. Get ML Statistics
```
GET /api/budget/ml/stats
```

**Description:** View system statistics (public endpoint)

**Response:**
```json
{
  "success": true,
  "data": {
    "total_predictions": 1500,
    "with_actual_spending": 250,
    "with_user_ratings": 180,
    "ml_predictions": 800,
    "rule_based_predictions": 700,
    "ready_for_retraining": true
  }
}
```

---

## 💻 Integration Examples

### **Example 1: Two-Step Process (Recommended)**

```javascript
// Step 1: Get Budget Allocation Advice
async function getBudgetAdvice() {
  const response = await fetch('/api/budget/ml/optimize', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      destination: 'Tokyo',
      duration: 5,
      total_budget: 2500,
      travelers: 2,
      purpose: 'leisure'
    })
  });
  
  const data = await response.json();
  
  // Display allocation breakdown
  console.log('Accommodation:', data.data.allocation_amounts.accommodation);
  console.log('Transportation:', data.data.allocation_amounts.transportation);
  console.log('Food:', data.data.allocation_amounts.food);
  
  return data;
}

// Step 2: Find Actual Travel Packages
async function findPackages(allocation) {
  const response = await fetch('/api/budget/optimize-trip', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      origin: 'LAX',
      destination: 'Tokyo',
      city_code: 'TYO',
      depart_date: '2026-03-15',
      return_date: '2026-03-20',
      budget: 2500,
      currency: 'USD'
    })
  });
  
  const packages = await response.json();
  
  // Display bookable packages
  packages.packages.forEach(pkg => {
    console.log('Package Total:', pkg.total);
    console.log('Flight:', pkg.flight.price);
    console.log('Hotel:', pkg.hotel.price);
  });
  
  return packages;
}

// Combined flow
async function planTrip() {
  const advice = await getBudgetAdvice();
  const packages = await findPackages(advice);
  
  return { advice, packages };
}
```

---

### **Example 2: React Component**

```jsx
import React, { useState } from 'react';

function TripPlanner() {
  const [allocation, setAllocation] = useState(null);
  const [packages, setPackages] = useState([]);
  const [loading, setLoading] = useState(false);

  const handleGetAdvice = async () => {
    setLoading(true);
    
    try {
      // Get ML allocation
      const response = await fetch('/api/budget/ml/optimize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          destination: 'Paris',
          duration: 7,
          total_budget: 3000,
          travelers: 2,
          purpose: 'romantic'
        })
      });
      
      const data = await response.json();
      setAllocation(data.data);
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSearchPackages = async () => {
    setLoading(true);
    
    try {
      const response = await fetch('/api/budget/optimize-trip', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          origin: 'YYZ',
          destination: 'Paris',
          city_code: 'PAR',
          depart_date: '2026-06-01',
          return_date: '2026-06-08',
          budget: 3000,
          currency: 'CAD'
        })
      });
      
      const data = await response.json();
      setPackages(data.packages);
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="trip-planner">
      <h1>Trip Planner</h1>
      
      <button onClick={handleGetAdvice} disabled={loading}>
        Get Budget Advice
      </button>
      
      {allocation && (
        <div className="allocation-section">
          <h2>Suggested Budget Allocation</h2>
          <p>Accommodation: ${allocation.allocation_amounts.accommodation}</p>
          <p>Transportation: ${allocation.allocation_amounts.transportation}</p>
          <p>Food: ${allocation.allocation_amounts.food}</p>
          <p>Activities: ${allocation.allocation_amounts.activities}</p>
          <p>Miscellaneous: ${allocation.allocation_amounts.miscellaneous}</p>
          
          <h3>Tips:</h3>
          <ul>
            {allocation.tips.map((tip, i) => <li key={i}>{tip}</li>)}
          </ul>
          
          <button onClick={handleSearchPackages}>
            Find Travel Packages
          </button>
        </div>
      )}
      
      {packages.length > 0 && (
        <div className="packages-section">
          <h2>Available Packages</h2>
          {packages.map((pkg, i) => (
            <div key={i} className="package-card">
              <h3>Package {i + 1} - ${pkg.total}</h3>
              <p>Flight: ${pkg.flight.price}</p>
              <p>Hotel: ${pkg.hotel.price}</p>
              <p>Status: {pkg.status}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default TripPlanner;
```

---

## 🎯 Use Cases

### **Use Case 1: Budget-Conscious Traveler**

**User Story:** Sarah has $2,000 for a 5-day trip to Bangkok and wants to maximize value.

**Flow:**
1. Call `/ml/optimize` to get smart allocation
   - Result: $600 accommodation, $500 transportation, $400 food, etc.
2. Call `/optimize-trip` to find packages within budget
   - Result: 3 packages ranging from $1,450 to $1,900
3. Sarah picks Package 1 ($1,450) and saves $550

---

### **Use Case 2: Business Traveler**

**User Story:** John needs a business trip to Tokyo with company budget of $4,000.

**Flow:**
1. Call `/ml/optimize` with `purpose: "business"`
   - Result: Higher allocation for accommodation (45%) and food (20%)
2. Call `/optimize-trip/best` to get the best professional package
   - Result: Best package with 4-star hotel + direct flights
3. John books immediately

---

### **Use Case 3: Family Vacation**

**User Story:** The Smith family (4 people) wants a 10-day European vacation.

**Flow:**
1. Call `/ml/optimize` with `travelers: 4, purpose: "family"`
   - Result: Balanced allocation with more for accommodation
2. Call `/optimize-trip` for multiple destination options
   - Result: Packages for Paris, Rome, Barcelona
3. Family compares and chooses based on activities included

---

### **Use Case 4: Last-Minute Trip**

**User Story:** Emma needs to book a weekend getaway (2 days) quickly.

**Flow:**
1. Call `/optimize-trip/stream` for real-time progress
   - Streams: "Fetching flights... Found 15 options..."
2. Get results as they come in
3. Book the first available package

---

## 🔧 Testing Guide

### **Test 1: Health Check**
```bash
curl http://localhost:8000/api/budget/health
```

**Expected:**
```json
{
  "service": "Budget Optimization & ML Recommendations",
  "status": "running",
  "ml_available": true
}
```

---

### **Test 2: ML Allocation**
```bash
curl -X POST http://localhost:8000/api/budget/ml/optimize \
  -H "Content-Type: application/json" \
  -d '{
    "destination": "Paris",
    "duration": 7,
    "total_budget": 3000,
    "travelers": 2
  }'
```

---

### **Test 3: Travel Packages**
```bash
curl -X POST http://localhost:8000/api/budget/optimize-trip \
  -H "Content-Type: application/json" \
  -d '{
    "origin": "YYZ",
    "destination": "BKK",
    "city_code": "BKK",
    "depart_date": "2025-12-01",
    "return_date": "2025-12-05",
    "budget": 3000,
    "currency": "CAD"
  }'
```

---

## 📊 Decision Guide

**Quick Questions:**

| Question | Answer | Use This Route |
|----------|--------|----------------|
| Need actual flights/hotels? | Yes | `/optimize-trip` |
| Need budget advice only? | Yes | `/ml/optimize` |
| User wants to book travel? | Yes | `/optimize-trip` |
| User is planning budget? | Yes | `/ml/optimize` |
| Need percentage breakdown? | Yes | `/ml/optimize` |
| Need complete packages? | Yes | `/optimize-trip` |

---

## 🎉 Summary

- **Both routes are valuable** - use them together!
- **ML route** (`/ml/optimize`) = Planning & advice
- **Package route** (`/optimize-trip`) = Booking & search
- **Best practice**: Use ML route first, then package route
- **They complement each other** perfectly!

---

## 📞 Support

For issues or questions:
1. Check API response for error messages
2. Verify model is trained (for ML route)
3. Check Amadeus API credentials (for package route)
4. Review logs for detailed errors

---

*Last Updated: October 27, 2025*
*Version: 2.0.0*
"""