import requests
import json
import time

BASE_URL = "https://www.themealdb.com/api/json/v1/1"

def fetch_all_recipes():
    all_recipes = []
    
    # Fetch by first letter (a-z)
    for letter in 'abcdefghijklmnopqrstuvwxyz':
        try:
            response = requests.get(f"{BASE_URL}/search.php?f={letter}", timeout=10)
            data = response.json()
            if data.get('meals'):
                for meal in data['meals']:
                    recipe = transform_meal(meal)
                    if recipe:
                        all_recipes.append(recipe)
            print(f"Letter {letter}: {len(data.get('meals', []) or [])} recipes")
            time.sleep(0.1)  # Rate limit
        except Exception as e:
            print(f"Error fetching letter {letter}: {e}")
    
    return all_recipes

def transform_meal(meal):
    """Transform TheMealDB meal to our format"""
    try:
        # Get ingredients and measures
        ingredients = []
        for i in range(1, 21):
            ing = meal.get(f'strIngredient{i}', '').strip()
            measure = meal.get(f'strMeasure{i}', '').strip()
            if ing:
                ingredients.append(f"{measure} {ing}".strip())
        
        # Map category to our categories
        category_map = {
            'Beef': 'viande',
            'Chicken': 'volaille',
            'Dessert': 'desserts',
            'Lamb': 'viande',
            'Miscellaneous': 'autre',
            'Pasta': 'pates',
            'Pork': 'viande',
            'Seafood': 'poisson',
            'Side': 'accompagnement',
            'Starter': 'entree',
            'Vegan': 'vegan',
            'Vegetarian': 'vegetarien',
            'Breakfast': 'petit_dejeuner',
            'Goat': 'viande'
        }
        
        # Calculate nutri-score based on category
        nutriscore_map = {
            'vegan': 'A',
            'vegetarien': 'A',
            'poisson': 'A',
            'entree': 'B',
            'accompagnement': 'B',
            'volaille': 'B',
            'petit_dejeuner': 'B',
            'pates': 'C',
            'viande': 'C',
            'desserts': 'D',
            'autre': 'C'
        }
        
        category = category_map.get(meal.get('strCategory', ''), 'autre')
        
        # Estimate calories based on category
        calorie_ranges = {
            'entree': (80, 200),
            'vegan': (150, 350),
            'vegetarien': (200, 400),
            'poisson': (200, 400),
            'volaille': (250, 450),
            'viande': (300, 550),
            'pates': (350, 550),
            'accompagnement': (100, 250),
            'petit_dejeuner': (200, 400),
            'desserts': (200, 450),
            'autre': (200, 400)
        }
        cal_range = calorie_ranges.get(category, (200, 400))
        import random
        calories = random.randint(cal_range[0], cal_range[1])
        
        return {
            'id': f"mealdb_{meal['idMeal']}",
            'name': meal['strMeal'],
            'category': category,
            'nutriscore': nutriscore_map.get(category, 'C'),
            'calories': calories,
            'proteins': round(calories * random.uniform(0.08, 0.15)),
            'carbs': round(calories * random.uniform(0.1, 0.3)),
            'fats': round(calories * random.uniform(0.03, 0.12)),
            'prep_time': random.randint(15, 60),
            'image': meal.get('strMealThumb', ''),
            'ingredients': ingredients,
            'instructions': meal.get('strInstructions', '').replace('\r\n', '\n'),
            'source': 'TheMealDB',
            'area': meal.get('strArea', 'International'),
            'youtube': meal.get('strYoutube', ''),
            'tags': meal.get('strTags', '').split(',') if meal.get('strTags') else []
        }
    except Exception as e:
        print(f"Error transforming meal: {e}")
        return None

if __name__ == "__main__":
    print("Fetching all recipes from TheMealDB...")
    recipes = fetch_all_recipes()
    print(f"\nTotal recipes fetched: {len(recipes)}")
    
    # Save to file
    with open('mealdb_recipes.json', 'w', encoding='utf-8') as f:
        json.dump(recipes, f, ensure_ascii=False, indent=2)
    print(f"Saved to mealdb_recipes.json")
    
    # Print sample
    if recipes:
        print(f"\nSample recipe: {recipes[0]['name']}")
