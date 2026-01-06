"""
Complete recipe database with 3000+ verified recipes
Sources: TheMealDB (570 real recipes), French cuisine, International, Bariatric specialized
"""
import json
import os
from pathlib import Path

# Load recipes from JSON file
_RECIPES_FILE = Path(__file__).parent / 'recipes_3000.json'

def _load_recipes():
    """Load recipes from JSON file"""
    try:
        with open(_RECIPES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading recipes: {e}")
        return []

# Load all recipes at module import
VERIFIED_RECIPES = _load_recipes()

def get_verified_recipes():
    """Get all verified recipes"""
    return VERIFIED_RECIPES

def get_recipes_count():
    """Get total recipe count"""
    return len(VERIFIED_RECIPES)

def search_recipes_by_name(query: str, limit: int = 20):
    """Search recipes by name"""
    query_lower = query.lower()
    results = []
    for recipe in VERIFIED_RECIPES:
        if query_lower in recipe.get('name', '').lower():
            results.append(recipe)
            if len(results) >= limit:
                break
    return results

def get_recipes_by_category(category: str, limit: int = 50):
    """Get recipes by category"""
    results = []
    for recipe in VERIFIED_RECIPES:
        if recipe.get('category') == category:
            results.append(recipe)
            if len(results) >= limit:
                break
    return results

def get_recipes_by_nutriscore(nutriscore: str, limit: int = 50):
    """Get recipes by nutri-score"""
    results = []
    for recipe in VERIFIED_RECIPES:
        if recipe.get('nutriscore') == nutriscore:
            results.append(recipe)
            if len(results) >= limit:
                break
    return results

def get_bariatric_recipes(phase: str = None, limit: int = 50):
    """Get bariatric specialized recipes"""
    results = []
    for recipe in VERIFIED_RECIPES:
        cat = recipe.get('category', '')
        if 'bariatric' in cat:
            if phase is None or recipe.get('bariatric_phase') == phase:
                results.append(recipe)
                if len(results) >= limit:
                    break
    return results

def get_random_recipes(count: int = 10, category: str = None, nutriscore: str = None):
    """Get random recipes with optional filters"""
    import random
    filtered = VERIFIED_RECIPES
    
    if category:
        filtered = [r for r in filtered if r.get('category') == category]
    if nutriscore:
        filtered = [r for r in filtered if r.get('nutriscore') == nutriscore]
    
    if len(filtered) <= count:
        return filtered
    
    return random.sample(filtered, count)

# Print stats on load
if VERIFIED_RECIPES:
    print(f"✅ Loaded {len(VERIFIED_RECIPES)} recipes from database")
    
    # Category stats
    categories = {}
    for r in VERIFIED_RECIPES:
        cat = r.get('category', 'autre')
        categories[cat] = categories.get(cat, 0) + 1
    
    bariatric = sum(v for k, v in categories.items() if 'bariatric' in k)
    print(f"   - Bariatric recipes: {bariatric}")
    print(f"   - Categories: {len(categories)}")
