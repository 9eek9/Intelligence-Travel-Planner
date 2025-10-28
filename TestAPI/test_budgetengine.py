from services.budget_service.budget_engine import find_best_budget_combo

if __name__ == "__main__":
    result = find_best_budget_combo("YYZ", "BKK", "2025-12-10", "2025-12-15", 1200)
    print(result)
