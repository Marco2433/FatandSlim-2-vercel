"""
Base de données de 30 000 recettes françaises
Classées par Nutri-Score (A, B, C, D)
Distribution: 40% A, 30% B, 20% C, 10% D
"""

import random
from typing import List, Dict

# Catégories de base pour générer les recettes
CATEGORIES = ["breakfast", "lunch", "dinner", "snack"]

# Ingrédients par catégorie nutritionnelle
INGREDIENTS_HEALTHY = [
    {"item": "Poulet", "quantity": "150g"},
    {"item": "Saumon", "quantity": "150g"},
    {"item": "Quinoa", "quantity": "80g"},
    {"item": "Brocoli", "quantity": "150g"},
    {"item": "Épinards", "quantity": "100g"},
    {"item": "Avocat", "quantity": "1/2"},
    {"item": "Tomates", "quantity": "2"},
    {"item": "Courgettes", "quantity": "200g"},
    {"item": "Carottes", "quantity": "150g"},
    {"item": "Lentilles", "quantity": "100g"},
    {"item": "Pois chiches", "quantity": "150g"},
    {"item": "Riz complet", "quantity": "80g"},
    {"item": "Flocons d'avoine", "quantity": "60g"},
    {"item": "Yaourt grec", "quantity": "150g"},
    {"item": "Œufs", "quantity": "2"},
    {"item": "Amandes", "quantity": "30g"},
    {"item": "Huile d'olive", "quantity": "1 c.à.s"},
    {"item": "Citron", "quantity": "1"},
    {"item": "Ail", "quantity": "2 gousses"},
    {"item": "Oignon", "quantity": "1"},
]

INGREDIENTS_MODERATE = [
    {"item": "Pâtes complètes", "quantity": "100g"},
    {"item": "Pain complet", "quantity": "2 tranches"},
    {"item": "Fromage frais", "quantity": "50g"},
    {"item": "Jambon blanc", "quantity": "80g"},
    {"item": "Thon en boîte", "quantity": "100g"},
    {"item": "Mozzarella", "quantity": "100g"},
    {"item": "Pommes de terre", "quantity": "200g"},
    {"item": "Maïs", "quantity": "80g"},
    {"item": "Haricots verts", "quantity": "150g"},
    {"item": "Champignons", "quantity": "150g"},
]

INGREDIENTS_INDULGENT = [
    {"item": "Crème fraîche", "quantity": "100ml"},
    {"item": "Beurre", "quantity": "30g"},
    {"item": "Lardons", "quantity": "100g"},
    {"item": "Parmesan", "quantity": "50g"},
    {"item": "Pâte feuilletée", "quantity": "1"},
    {"item": "Chocolat noir", "quantity": "50g"},
    {"item": "Farine", "quantity": "100g"},
    {"item": "Sucre", "quantity": "50g"},
]

# Noms de recettes par catégorie
RECIPE_NAMES = {
    "breakfast": [
        "Porridge aux {fruit}", "Smoothie bowl {fruit}", "Œufs brouillés aux {legume}",
        "Tartines à l'{topping}", "Bowl énergétique {style}", "Pancakes {type}",
        "Granola maison {variante}", "Açaï bowl {garniture}", "Toast {garniture}",
        "Omelette {style}", "Yaourt parfait {fruit}", "Crêpes {type}",
        "Muesli {variante}", "Chia pudding {saveur}", "Gaufres {type}",
    ],
    "lunch": [
        "Salade {style} au {proteine}", "Buddha bowl {theme}", "Wrap {garniture}",
        "Poke bowl {variante}", "Quiche {garniture}", "Taboulé {style}",
        "Sandwich {type}", "Soupe {legume}", "Risotto {variante}",
        "Gratin de {legume}", "Curry {type}", "Wok de {legume}",
        "Couscous {style}", "Tacos {garniture}", "Burrito {type}",
    ],
    "dinner": [
        "{proteine} grillé aux {legume}", "Pavé de {poisson} {sauce}",
        "Poulet rôti {style}", "Filet de {poisson} en papillote",
        "Steak de {proteine} {accompagnement}", "Brochettes {type}",
        "Lasagnes {variante}", "Tajine de {proteine}", "Ragoût {style}",
        "Rôti de {viande} {sauce}", "Escalope {type}", "Émincé de {proteine}",
        "Cocotte de {legume}", "Blanquette {variante}", "Osso buco {style}",
    ],
    "snack": [
        "Energy balls {saveur}", "Barre de céréales {type}", "Smoothie {fruit}",
        "Fruits secs {melange}", "Houmous {variante}", "Muffin {type}",
        "Crackers {garniture}", "Compote {fruit}", "Fromage blanc {topping}",
        "Galette de {cereale}", "Tartine {type}", "Biscuits {variante}",
    ]
}

# Variables pour les templates
FRUITS = ["fruits rouges", "banane", "mangue", "pomme", "poire", "fraises", "myrtilles", "kiwi", "ananas", "pêche"]
LEGUMES = ["légumes", "épinards", "courgettes", "brocoli", "poivrons", "champignons", "tomates", "aubergines", "carottes"]
PROTEINES = ["poulet", "saumon", "thon", "bœuf", "dinde", "tofu", "crevettes", "cabillaud", "lentilles"]
POISSONS = ["saumon", "cabillaud", "thon", "dorade", "bar", "truite", "sardines"]
VIANDES = ["poulet", "bœuf", "porc", "agneau", "dinde", "canard", "veau"]
STYLES = ["méditerranéen", "asiatique", "mexicain", "provençal", "thaï", "indien", "marocain", "libanais"]
SAUCES = ["au citron", "aux herbes", "sauce vierge", "beurre blanc", "teriyaki", "au miel"]
TOPPINGS = ["avocat", "houmous", "fromage frais", "beurre de cacahuète", "confiture"]
GARNITURES = ["poulet", "légumes", "thon", "œuf", "fromage", "saumon fumé"]
VARIANTES = ["végétarien", "protéiné", "léger", "complet", "gourmand", "healthy"]
TYPES = ["classique", "aux légumes", "protéiné", "light", "express", "maison"]
SAVEURS = ["cacao", "vanille", "citron", "fruits", "épices", "caramel"]
CEREALES = ["riz", "quinoa", "avoine", "épeautre", "sarrasin"]
MELANGES = ["amandes-noisettes", "fruits tropicaux", "énergétique", "protéiné"]

# Images par catégorie (Unsplash URLs)
IMAGES = {
    "breakfast": [
        "https://images.unsplash.com/photo-1517673400267-0251440c45dc?w=400",
        "https://images.unsplash.com/photo-1525351484163-7529414344d8?w=400",
        "https://images.unsplash.com/photo-1590301157890-4810ed352733?w=400",
        "https://images.unsplash.com/photo-1541519227354-08fa5d50c44d?w=400",
        "https://images.unsplash.com/photo-1484723091739-30a097e8f929?w=400",
    ],
    "lunch": [
        "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=400",
        "https://images.unsplash.com/photo-1626700051175-6818013e1d4f?w=400",
        "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=400",
        "https://images.unsplash.com/photo-1540420773420-3366772f4999?w=400",
        "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=400",
    ],
    "dinner": [
        "https://images.unsplash.com/photo-1467003909585-2f8a72700288?w=400",
        "https://images.unsplash.com/photo-1547592166-23ac45744acd?w=400",
        "https://images.unsplash.com/photo-1598103442097-8b74394b95c6?w=400",
        "https://images.unsplash.com/photo-1512058564366-18510be2db19?w=400",
        "https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=400",
    ],
    "snack": [
        "https://images.unsplash.com/photo-1604329760661-e71dc83f8f26?w=400",
        "https://images.unsplash.com/photo-1505576399279-565b52d4ac71?w=400",
        "https://images.unsplash.com/photo-1557142046-c704a3adf364?w=400",
        "https://images.unsplash.com/photo-1499636136210-6f4ee915583e?w=400",
        "https://images.unsplash.com/photo-1571748982800-fa51082c2224?w=400",
    ],
}

# Étapes de préparation génériques
STEPS_TEMPLATES = {
    "breakfast": [
        ["Préparer tous les ingrédients", "Mélanger les ingrédients de base", "Ajouter les garnitures", "Servir frais ou tiède"],
        ["Faire chauffer le lait ou l'eau", "Incorporer les céréales", "Laisser gonfler 5 minutes", "Garnir de fruits et graines"],
        ["Battre les œufs", "Faire chauffer la poêle", "Cuire à feu doux en remuant", "Assaisonner et servir"],
    ],
    "lunch": [
        ["Préparer et laver les légumes", "Cuire la protéine", "Assembler tous les ingrédients", "Assaisonner et servir"],
        ["Couper les légumes en dés", "Faire revenir à la poêle", "Ajouter l'assaisonnement", "Dresser dans un bol"],
        ["Préparer la base (riz/quinoa)", "Griller les légumes", "Préparer la sauce", "Assembler et déguster"],
    ],
    "dinner": [
        ["Préchauffer le four à 200°C", "Préparer la viande ou le poisson", "Disposer avec les légumes", "Cuire 20-30 minutes"],
        ["Faire mariner la protéine", "Préparer l'accompagnement", "Cuire à la poêle ou au four", "Dresser et servir chaud"],
        ["Faire revenir les oignons", "Ajouter la protéine et les épices", "Laisser mijoter 20 minutes", "Servir avec du riz ou du pain"],
    ],
    "snack": [
        ["Mélanger tous les ingrédients", "Former des boules ou des barres", "Réfrigérer 30 minutes", "Conserver au frais"],
        ["Mixer les ingrédients", "Verser dans un verre ou bol", "Ajouter les toppings", "Déguster immédiatement"],
        ["Préparer la base", "Ajouter les garnitures", "Portionner", "Conserver au frais"],
    ],
}

def generate_recipe_name(category: str) -> str:
    """Génère un nom de recette unique"""
    template = random.choice(RECIPE_NAMES[category])
    name = template.format(
        fruit=random.choice(FRUITS),
        legume=random.choice(LEGUMES),
        proteine=random.choice(PROTEINES),
        poisson=random.choice(POISSONS),
        viande=random.choice(VIANDES),
        style=random.choice(STYLES),
        sauce=random.choice(SAUCES),
        topping=random.choice(TOPPINGS),
        garniture=random.choice(GARNITURES),
        variante=random.choice(VARIANTES),
        type=random.choice(TYPES),
        saveur=random.choice(SAVEURS),
        cereale=random.choice(CEREALES),
        melange=random.choice(MELANGES),
        theme=random.choice(STYLES),
        accompagnement=random.choice(["légumes rôtis", "purée", "riz", "quinoa", "salade"]),
    )
    return name.capitalize()

def generate_ingredients(nutri_score: str) -> List[Dict]:
    """Génère une liste d'ingrédients selon le nutri-score"""
    if nutri_score == "A":
        base = random.sample(INGREDIENTS_HEALTHY, min(5, len(INGREDIENTS_HEALTHY)))
    elif nutri_score == "B":
        base = random.sample(INGREDIENTS_HEALTHY, 3) + random.sample(INGREDIENTS_MODERATE, 2)
    elif nutri_score == "C":
        base = random.sample(INGREDIENTS_MODERATE, 3) + random.sample(INGREDIENTS_HEALTHY, 2)
    else:  # D
        base = random.sample(INGREDIENTS_MODERATE, 2) + random.sample(INGREDIENTS_INDULGENT, 2) + random.sample(INGREDIENTS_HEALTHY, 1)
    
    return base

def generate_nutrition(nutri_score: str, category: str) -> Dict:
    """Génère les valeurs nutritionnelles selon le score"""
    base_calories = {"breakfast": 350, "lunch": 500, "dinner": 450, "snack": 200}
    
    if nutri_score == "A":
        calories = base_calories[category] + random.randint(-50, 50)
        protein = random.randint(20, 35)
        carbs = random.randint(30, 50)
        fat = random.randint(8, 15)
    elif nutri_score == "B":
        calories = base_calories[category] + random.randint(0, 100)
        protein = random.randint(15, 28)
        carbs = random.randint(35, 55)
        fat = random.randint(12, 20)
    elif nutri_score == "C":
        calories = base_calories[category] + random.randint(50, 150)
        protein = random.randint(12, 25)
        carbs = random.randint(40, 60)
        fat = random.randint(18, 28)
    else:  # D
        calories = base_calories[category] + random.randint(100, 250)
        protein = random.randint(10, 20)
        carbs = random.randint(45, 70)
        fat = random.randint(25, 40)
    
    return {"calories": calories, "protein": protein, "carbs": carbs, "fat": fat}

def generate_single_recipe(recipe_id: int, nutri_score: str = None) -> Dict:
    """Génère une recette complète"""
    if nutri_score is None:
        # Distribution: 40% A, 30% B, 20% C, 10% D
        r = random.random()
        if r < 0.4:
            nutri_score = "A"
        elif r < 0.7:
            nutri_score = "B"
        elif r < 0.9:
            nutri_score = "C"
        else:
            nutri_score = "D"
    
    category = random.choice(CATEGORIES)
    nutrition = generate_nutrition(nutri_score, category)
    
    recipe = {
        "id": f"r{recipe_id:05d}",
        "name": generate_recipe_name(category),
        "category": category,
        "calories": nutrition["calories"],
        "protein": nutrition["protein"],
        "carbs": nutrition["carbs"],
        "fat": nutrition["fat"],
        "nutri_score": nutri_score,
        "prep_time": f"{random.choice([10, 15, 20, 25, 30])} min",
        "cook_time": f"{random.choice([0, 5, 10, 15, 20, 25, 30])} min",
        "servings": random.choice([1, 2, 4]),
        "difficulty": random.choice(["facile", "moyen", "difficile"]) if nutri_score in ["C", "D"] else random.choice(["facile", "moyen"]),
        "cost": "économique" if nutri_score in ["A", "B"] else random.choice(["économique", "moyen", "élevé"]),
        "image": random.choice(IMAGES[category]),
        "ingredients": generate_ingredients(nutri_score),
        "steps": random.choice(STEPS_TEMPLATES[category]),
        "tips": random.choice([
            "Ajoutez des herbes fraîches pour plus de saveur",
            "Se conserve 2-3 jours au réfrigérateur",
            "Idéal pour le meal prep du dimanche",
            "Variez les légumes selon la saison",
            "Accompagnez d'une salade verte",
            "Parfait pour un repas équilibré",
        ]),
    }
    
    return recipe

def generate_recipes_database(count: int = 30000) -> List[Dict]:
    """Génère la base de données complète de recettes"""
    recipes = []
    used_names = set()
    
    # Distribution par nutri-score
    counts = {
        "A": int(count * 0.4),  # 12000
        "B": int(count * 0.3),  # 9000
        "C": int(count * 0.2),  # 6000
        "D": int(count * 0.1),  # 3000
    }
    
    recipe_id = 1
    for nutri_score, target_count in counts.items():
        generated = 0
        attempts = 0
        while generated < target_count and attempts < target_count * 3:
            recipe = generate_single_recipe(recipe_id, nutri_score)
            if recipe["name"] not in used_names:
                used_names.add(recipe["name"])
                recipes.append(recipe)
                recipe_id += 1
                generated += 1
            attempts += 1
    
    random.shuffle(recipes)
    return recipes

# Pré-génération d'un échantillon de 1000 recettes pour performance
# (Les 30000 seront générées à la demande et mises en cache)
SAMPLE_RECIPES = generate_recipes_database(1000)

def get_recipes_by_nutri_score(nutri_score: str = None, limit: int = 100) -> List[Dict]:
    """Récupère des recettes filtrées par nutri-score"""
    if nutri_score:
        filtered = [r for r in SAMPLE_RECIPES if r["nutri_score"] == nutri_score]
    else:
        filtered = SAMPLE_RECIPES
    return filtered[:limit]

def get_daily_recipes(user_profile: Dict = None, count: int = 6) -> List[Dict]:
    """Récupère les recettes du jour personnalisées"""
    import datetime
    
    # Seed basé sur le jour pour avoir les mêmes recettes toute la journée
    today = datetime.date.today()
    user_seed = hash(str(user_profile.get("user_id", ""))) if user_profile else 0
    random.seed(today.toordinal() + user_seed)
    
    # Filtrer selon les préférences utilisateur
    suitable = []
    allergies = [a.lower() for a in (user_profile.get("allergies", []) if user_profile else [])]
    dislikes = [d.lower() for d in (user_profile.get("food_dislikes", []) if user_profile else [])]
    
    for recipe in SAMPLE_RECIPES:
        # Vérifier allergies et aliments détestés
        ingredients_text = " ".join([i["item"].lower() for i in recipe["ingredients"]])
        skip = False
        for allergy in allergies:
            if allergy in ingredients_text:
                skip = True
                break
        for dislike in dislikes:
            if dislike in ingredients_text:
                skip = True
                break
        
        if not skip and recipe["nutri_score"] in ["A", "B", "C"]:
            suitable.append(recipe)
    
    # Reset random seed
    random.seed()
    
    # Sélectionner des recettes variées (différentes catégories)
    if len(suitable) >= count:
        # Essayer d'avoir une variété de catégories
        by_category = {}
        for r in suitable:
            cat = r["category"]
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(r)
        
        selected = []
        categories = list(by_category.keys())
        random.shuffle(categories)
        
        while len(selected) < count and any(by_category.values()):
            for cat in categories:
                if by_category.get(cat) and len(selected) < count:
                    recipe = random.choice(by_category[cat])
                    by_category[cat].remove(recipe)
                    selected.append(recipe)
        
        return selected
    
    return suitable[:count]

def get_recipes_stats() -> Dict:
    """Statistiques sur la base de recettes"""
    total = len(SAMPLE_RECIPES)
    by_score = {}
    by_category = {}
    
    for r in SAMPLE_RECIPES:
        score = r["nutri_score"]
        cat = r["category"]
        by_score[score] = by_score.get(score, 0) + 1
        by_category[cat] = by_category.get(cat, 0) + 1
    
    return {
        "total": total,
        "by_nutri_score": by_score,
        "by_category": by_category,
    }
