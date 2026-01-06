"""
Build 3000+ recipe database from TheMealDB + French recipes + Bariatric recipes
"""
import json
import random
import hashlib

# Load TheMealDB recipes
with open('mealdb_recipes.json', 'r', encoding='utf-8') as f:
    MEALDB_RECIPES = json.load(f)

print(f"Loaded {len(MEALDB_RECIPES)} TheMealDB recipes")

# French recipe base data
FRENCH_RECIPES = [
    # Entrées
    {"name": "Salade Niçoise", "category": "entree", "nutriscore": "A", "calories": 180, "proteins": 12, "carbs": 15, "fats": 8, "prep_time": 15,
     "image": "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=400",
     "ingredients": ["Thon en conserve 150g", "Haricots verts 100g", "Œufs durs 2", "Tomates cerises 100g", "Olives noires 50g", "Anchois 4 filets", "Huile d'olive 2 c.s."],
     "instructions": "1. Cuire les haricots verts 5 min à l'eau bouillante. Refroidir.\n2. Couper les tomates en deux, les œufs en quartiers.\n3. Disposer tous les ingrédients dans un plat.\n4. Arroser d'huile d'olive et servir frais."},
    {"name": "Soupe à l'oignon gratinée", "category": "entree", "nutriscore": "B", "calories": 220, "proteins": 8, "carbs": 25, "fats": 10, "prep_time": 45,
     "image": "https://images.unsplash.com/photo-1547592166-23ac45744acd?w=400",
     "ingredients": ["Oignons 500g", "Bouillon de bœuf 1L", "Pain rassis 4 tranches", "Gruyère râpé 150g", "Beurre 30g", "Vin blanc 10cl"],
     "instructions": "1. Émincer finement les oignons. Faire fondre dans le beurre 20 min.\n2. Déglacer au vin blanc, ajouter le bouillon. Cuire 20 min.\n3. Verser dans des bols, ajouter le pain et le fromage.\n4. Gratiner au four 5 min."},
    {"name": "Terrine de campagne", "category": "entree", "nutriscore": "C", "calories": 280, "proteins": 18, "carbs": 5, "fats": 22, "prep_time": 30,
     "image": "https://images.unsplash.com/photo-1544025162-d76694265947?w=400",
     "ingredients": ["Porc haché 400g", "Foie de volaille 200g", "Échalotes 2", "Cognac 3 c.s.", "Thym", "Laurier", "Sel, poivre"],
     "instructions": "1. Mixer le foie avec les échalotes.\n2. Mélanger avec le porc, le cognac, les épices.\n3. Verser dans une terrine, couvrir de laurier.\n4. Cuire au bain-marie 1h30 à 180°C."},
    {"name": "Velouté de champignons", "category": "entree", "nutriscore": "A", "calories": 150, "proteins": 5, "carbs": 12, "fats": 9, "prep_time": 25,
     "image": "https://images.unsplash.com/photo-1603105037880-880cd4edfb0d?w=400",
     "ingredients": ["Champignons de Paris 500g", "Crème fraîche 15cl", "Échalotes 2", "Bouillon de légumes 50cl", "Persil"],
     "instructions": "1. Faire revenir les échalotes et champignons émincés.\n2. Ajouter le bouillon, cuire 15 min.\n3. Mixer, ajouter la crème.\n4. Servir avec du persil."},
    {"name": "Quiche Lorraine", "category": "entree", "nutriscore": "C", "calories": 350, "proteins": 14, "carbs": 22, "fats": 24, "prep_time": 45,
     "image": "https://images.unsplash.com/photo-1608855238293-a8853e7f7c98?w=400",
     "ingredients": ["Pâte brisée 1", "Lardons 200g", "Œufs 3", "Crème fraîche 20cl", "Lait 10cl", "Gruyère râpé 100g", "Muscade"],
     "instructions": "1. Préchauffer le four à 180°C.\n2. Foncer un moule avec la pâte.\n3. Faire revenir les lardons.\n4. Battre œufs, crème, lait. Ajouter lardons et fromage.\n5. Verser sur la pâte. Cuire 35 min."},
    
    # Plats principaux
    {"name": "Bœuf Bourguignon", "category": "viande", "nutriscore": "C", "calories": 450, "proteins": 35, "carbs": 18, "fats": 28, "prep_time": 180,
     "image": "https://images.unsplash.com/photo-1544025162-d76694265947?w=400",
     "ingredients": ["Bœuf à braiser 1kg", "Vin rouge Bourgogne 75cl", "Carottes 4", "Oignons 2", "Champignons 250g", "Lardons 150g", "Bouquet garni"],
     "instructions": "1. Couper le bœuf en cubes, faire mariner dans le vin.\n2. Saisir la viande, réserver.\n3. Faire revenir lardons, oignons, carottes.\n4. Ajouter la viande et le vin. Mijoter 2h30.\n5. Ajouter les champignons 30 min avant la fin."},
    {"name": "Coq au vin", "category": "volaille", "nutriscore": "B", "calories": 420, "proteins": 38, "carbs": 15, "fats": 24, "prep_time": 120,
     "image": "https://images.unsplash.com/photo-1604908176997-125f25cc6f3d?w=400",
     "ingredients": ["Poulet fermier 1.5kg", "Vin rouge 75cl", "Lardons 150g", "Champignons 200g", "Oignons grelots 12", "Cognac 5cl", "Thym, laurier"],
     "instructions": "1. Découper le poulet. Faire dorer dans une cocotte.\n2. Flamber au cognac.\n3. Ajouter les lardons, oignons, le vin et le bouquet garni.\n4. Mijoter 1h30. Ajouter les champignons à mi-cuisson."},
    {"name": "Blanquette de veau", "category": "viande", "nutriscore": "B", "calories": 380, "proteins": 32, "carbs": 12, "fats": 22, "prep_time": 120,
     "image": "https://images.unsplash.com/photo-1558030006-450675393462?w=400",
     "ingredients": ["Veau (épaule) 1kg", "Carottes 3", "Poireaux 2", "Champignons 200g", "Crème fraîche 20cl", "Jaunes d'œufs 2", "Citron"],
     "instructions": "1. Blanchir la viande 5 min à l'eau bouillante.\n2. Cuire dans un bouillon avec les légumes 1h30.\n3. Filtrer le bouillon, lier avec crème et jaunes d'œufs.\n4. Napper la viande. Servir avec du riz."},
    {"name": "Cassoulet", "category": "viande", "nutriscore": "C", "calories": 550, "proteins": 35, "carbs": 45, "fats": 28, "prep_time": 240,
     "image": "https://images.unsplash.com/photo-1544025162-d76694265947?w=400",
     "ingredients": ["Haricots blancs secs 500g", "Confit de canard 4 cuisses", "Saucisses de Toulouse 4", "Poitrine de porc 300g", "Tomates 400g", "Ail, thym"],
     "instructions": "1. Tremper les haricots 12h. Les cuire 1h.\n2. Faire revenir les viandes.\n3. Monter le cassoulet en couches dans une cassole.\n4. Cuire au four 2h à 150°C. Casser la croûte 3 fois."},
    {"name": "Poulet rôti aux herbes", "category": "volaille", "nutriscore": "A", "calories": 320, "proteins": 35, "carbs": 5, "fats": 18, "prep_time": 75,
     "image": "https://images.unsplash.com/photo-1598103442097-8b74394b95c6?w=400",
     "ingredients": ["Poulet fermier 1.5kg", "Beurre 50g", "Thym frais", "Romarin", "Ail 4 gousses", "Citron 1", "Sel, poivre"],
     "instructions": "1. Préchauffer le four à 200°C.\n2. Glisser le beurre aux herbes sous la peau.\n3. Insérer citron et ail dans la cavité.\n4. Rôtir 1h15, arroser régulièrement."},
    {"name": "Gratin dauphinois", "category": "accompagnement", "nutriscore": "C", "calories": 280, "proteins": 8, "carbs": 28, "fats": 16, "prep_time": 75,
     "image": "https://images.unsplash.com/photo-1588166524941-3bf61a9c41db?w=400",
     "ingredients": ["Pommes de terre 1kg", "Crème fraîche 40cl", "Lait 20cl", "Ail 2 gousses", "Muscade", "Sel, poivre"],
     "instructions": "1. Éplucher et trancher finement les pommes de terre.\n2. Frotter un plat à l'ail, beurrer.\n3. Disposer en couches, verser crème et lait.\n4. Cuire 1h à 180°C."},
    {"name": "Ratatouille", "category": "vegetarien", "nutriscore": "A", "calories": 120, "proteins": 3, "carbs": 15, "fats": 6, "prep_time": 60,
     "image": "https://images.unsplash.com/photo-1540420773420-3366772f4999?w=400",
     "ingredients": ["Aubergines 2", "Courgettes 2", "Poivrons 2", "Tomates 4", "Oignons 2", "Ail 3 gousses", "Huile d'olive", "Herbes de Provence"],
     "instructions": "1. Couper tous les légumes en cubes.\n2. Faire revenir chaque légume séparément.\n3. Réunir dans une cocotte avec ail et herbes.\n4. Mijoter 30 min à feu doux."},
    {"name": "Tarte Tatin", "category": "desserts", "nutriscore": "D", "calories": 320, "proteins": 4, "carbs": 45, "fats": 15, "prep_time": 60,
     "image": "https://images.unsplash.com/photo-1488477181946-6428a0291777?w=400",
     "ingredients": ["Pommes Golden 1kg", "Pâte feuilletée 1", "Beurre 80g", "Sucre 150g", "Cannelle"],
     "instructions": "1. Faire un caramel avec beurre et sucre dans un moule.\n2. Disposer les pommes coupées en quartiers.\n3. Cuire 20 min à feu moyen.\n4. Couvrir de pâte, cuire 25 min à 200°C.\n5. Retourner sur un plat."},
    {"name": "Crème brûlée", "category": "desserts", "nutriscore": "D", "calories": 350, "proteins": 5, "carbs": 35, "fats": 22, "prep_time": 45,
     "image": "https://images.unsplash.com/photo-1565958011703-44f9829ba187?w=400",
     "ingredients": ["Crème fraîche 50cl", "Jaunes d'œufs 6", "Sucre 100g", "Vanille 1 gousse", "Cassonade"],
     "instructions": "1. Chauffer la crème avec la vanille.\n2. Fouetter jaunes et sucre jusqu'à blanchiment.\n3. Verser la crème sur les œufs, mélanger.\n4. Cuire au bain-marie 40 min à 150°C.\n5. Refroidir, saupoudrer de cassonade et caraméliser."},
    {"name": "Mousse au chocolat", "category": "desserts", "nutriscore": "C", "calories": 280, "proteins": 6, "carbs": 28, "fats": 16, "prep_time": 30,
     "image": "https://images.unsplash.com/photo-1565958011703-44f9829ba187?w=400",
     "ingredients": ["Chocolat noir 200g", "Œufs 6", "Sucre 50g", "Beurre 30g"],
     "instructions": "1. Faire fondre le chocolat avec le beurre.\n2. Séparer blancs et jaunes.\n3. Incorporer les jaunes au chocolat.\n4. Monter les blancs en neige avec le sucre.\n5. Incorporer délicatement. Réfrigérer 4h."},
    
    # Poissons
    {"name": "Sole meunière", "category": "poisson", "nutriscore": "A", "calories": 280, "proteins": 28, "carbs": 8, "fats": 15, "prep_time": 20,
     "image": "https://images.unsplash.com/photo-1467003909585-2f8a72700288?w=400",
     "ingredients": ["Sole 4 filets", "Beurre 80g", "Farine 50g", "Citron 2", "Persil", "Sel, poivre"],
     "instructions": "1. Fariner légèrement les soles.\n2. Cuire dans le beurre mousseux 3 min par côté.\n3. Ajouter le jus de citron.\n4. Servir avec le beurre noisette et persil."},
    {"name": "Bouillabaisse", "category": "poisson", "nutriscore": "A", "calories": 320, "proteins": 35, "carbs": 15, "fats": 14, "prep_time": 90,
     "image": "https://images.unsplash.com/photo-1519708227418-c8fd9a32b7a2?w=400",
     "ingredients": ["Poissons variés 1.5kg", "Tomates 500g", "Fenouil 1", "Oignons 2", "Safran", "Rouille", "Croûtons"],
     "instructions": "1. Préparer un fond avec têtes de poisson, légumes.\n2. Cuire les poissons fermes d'abord, puis les tendres.\n3. Servir la soupe à part avec croûtons et rouille."},
    {"name": "Saumon en papillote", "category": "poisson", "nutriscore": "A", "calories": 300, "proteins": 30, "carbs": 8, "fats": 18, "prep_time": 30,
     "image": "https://images.unsplash.com/photo-1467003909585-2f8a72700288?w=400",
     "ingredients": ["Pavés de saumon 4", "Courgettes 2", "Tomates cerises 200g", "Citron 1", "Aneth", "Huile d'olive"],
     "instructions": "1. Préchauffer le four à 180°C.\n2. Placer chaque pavé sur une feuille d'aluminium.\n3. Ajouter les légumes, l'aneth, le citron.\n4. Fermer les papillotes. Cuire 20 min."},
    {"name": "Moules marinières", "category": "poisson", "nutriscore": "A", "calories": 180, "proteins": 20, "carbs": 8, "fats": 8, "prep_time": 25,
     "image": "https://images.unsplash.com/photo-1519708227418-c8fd9a32b7a2?w=400",
     "ingredients": ["Moules 2kg", "Vin blanc 20cl", "Échalotes 3", "Persil", "Beurre 50g", "Crème (optionnel)"],
     "instructions": "1. Nettoyer et ébarber les moules.\n2. Faire suer les échalotes dans le beurre.\n3. Ajouter le vin, porter à ébullition.\n4. Ajouter les moules, couvrir. Cuire 5 min.\n5. Servir avec le jus et persil."},
    
    # Petit-déjeuner
    {"name": "Croissant", "category": "petit_dejeuner", "nutriscore": "D", "calories": 270, "proteins": 5, "carbs": 30, "fats": 15, "prep_time": 180,
     "image": "https://images.unsplash.com/photo-1555507036-ab1f4038808a?w=400",
     "ingredients": ["Farine 500g", "Beurre 280g", "Levure 20g", "Lait 25cl", "Sucre 50g", "Sel 10g"],
     "instructions": "1. Préparer la détrempe avec farine, lait, levure, sucre, sel.\n2. Incorporer le beurre en feuilletage (3 tours).\n3. Façonner les croissants.\n4. Laisser lever 2h. Cuire 15 min à 200°C."},
    {"name": "Pain perdu", "category": "petit_dejeuner", "nutriscore": "C", "calories": 250, "proteins": 8, "carbs": 30, "fats": 12, "prep_time": 15,
     "image": "https://images.unsplash.com/photo-1525351484163-7529414344d8?w=400",
     "ingredients": ["Pain rassis 4 tranches", "Œufs 2", "Lait 15cl", "Sucre 40g", "Beurre 30g", "Cannelle"],
     "instructions": "1. Battre œufs, lait, sucre et cannelle.\n2. Tremper les tranches de pain.\n3. Cuire dans le beurre 2-3 min par côté.\n4. Saupoudrer de sucre et servir."},
    {"name": "Œufs brouillés crémeux", "category": "petit_dejeuner", "nutriscore": "B", "calories": 200, "proteins": 14, "carbs": 2, "fats": 16, "prep_time": 10,
     "image": "https://images.unsplash.com/photo-1525351484163-7529414344d8?w=400",
     "ingredients": ["Œufs 4", "Beurre 30g", "Crème fraîche 2 c.s.", "Ciboulette", "Sel, poivre"],
     "instructions": "1. Battre les œufs avec sel et poivre.\n2. Cuire au bain-marie en remuant constamment.\n3. Retirer du feu quand crémeux.\n4. Ajouter beurre et crème. Parsemer de ciboulette."},
    
    # Salades
    {"name": "Salade César", "category": "entree", "nutriscore": "B", "calories": 280, "proteins": 18, "carbs": 15, "fats": 18, "prep_time": 20,
     "image": "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=400",
     "ingredients": ["Laitue romaine 1", "Poulet grillé 200g", "Parmesan 50g", "Croûtons 100g", "Anchois 4", "Sauce César"],
     "instructions": "1. Préparer la sauce César.\n2. Couper la romaine, le poulet en tranches.\n3. Mélanger avec croûtons et parmesan.\n4. Napper de sauce et servir."},
    {"name": "Salade de chèvre chaud", "category": "entree", "nutriscore": "B", "calories": 320, "proteins": 15, "carbs": 18, "fats": 22, "prep_time": 20,
     "image": "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=400",
     "ingredients": ["Mesclun 200g", "Chèvre frais 4 tranches", "Pain de campagne 4 tranches", "Noix 50g", "Miel 2 c.s.", "Vinaigrette"],
     "instructions": "1. Toaster le pain avec le chèvre sous le gril.\n2. Dresser le mesclun dans les assiettes.\n3. Poser le chèvre chaud dessus.\n4. Parsemer de noix, arroser de miel et vinaigrette."},
]

# Bariatric specialized recipes
BARIATRIC_RECIPES = [
    # Phase 1 - Liquide clair
    {"name": "Bouillon de légumes clair", "category": "bariatric_liquide", "nutriscore": "A", "calories": 15, "proteins": 1, "carbs": 3, "fats": 0, "prep_time": 30,
     "image": "https://images.unsplash.com/photo-1547592166-23ac45744acd?w=400",
     "ingredients": ["Carottes 2", "Céleri 2 branches", "Poireau 1", "Oignon 1", "Sel"],
     "instructions": "1. Porter 2L d'eau à ébullition.\n2. Ajouter les légumes coupés grossièrement.\n3. Mijoter 30 min.\n4. Filtrer et servir uniquement le liquide clair.",
     "bariatric_phase": "liquide"},
    {"name": "Eau aromatisée citron-gingembre", "category": "bariatric_liquide", "nutriscore": "A", "calories": 5, "proteins": 0, "carbs": 1, "fats": 0, "prep_time": 5,
     "image": "https://images.unsplash.com/photo-1505576399279-565b52d4ac71?w=400",
     "ingredients": ["Eau 1L", "Citron 1/2", "Gingembre frais 1cm"],
     "instructions": "1. Presser le citron dans l'eau.\n2. Râper le gingembre, infuser 5 min.\n3. Filtrer et servir frais.",
     "bariatric_phase": "liquide"},
    {"name": "Thé vert léger sans sucre", "category": "bariatric_liquide", "nutriscore": "A", "calories": 2, "proteins": 0, "carbs": 0, "fats": 0, "prep_time": 5,
     "image": "https://images.unsplash.com/photo-1505576399279-565b52d4ac71?w=400",
     "ingredients": ["Thé vert 1 sachet", "Eau chaude 25cl"],
     "instructions": "1. Faire infuser le thé 3 min.\n2. Retirer le sachet.\n3. Laisser tiédir avant de boire par petites gorgées.",
     "bariatric_phase": "liquide"},
    {"name": "Bouillon de poulet dégraissé", "category": "bariatric_liquide", "nutriscore": "A", "calories": 20, "proteins": 3, "carbs": 1, "fats": 0, "prep_time": 120,
     "image": "https://images.unsplash.com/photo-1547592166-23ac45744acd?w=400",
     "ingredients": ["Carcasse de poulet 1", "Oignon 1", "Carotte 1", "Céleri 1 branche", "Eau 2L"],
     "instructions": "1. Faire mijoter tous les ingrédients 2h.\n2. Laisser refroidir au réfrigérateur.\n3. Retirer la graisse figée en surface.\n4. Réchauffer et filtrer avant de servir.",
     "bariatric_phase": "liquide"},
    {"name": "Infusion menthe-camomille", "category": "bariatric_liquide", "nutriscore": "A", "calories": 2, "proteins": 0, "carbs": 0, "fats": 0, "prep_time": 10,
     "image": "https://images.unsplash.com/photo-1505576399279-565b52d4ac71?w=400",
     "ingredients": ["Menthe fraîche 5 feuilles", "Camomille séchée 1 c.c.", "Eau chaude 25cl"],
     "instructions": "1. Placer les herbes dans une tasse.\n2. Verser l'eau frémissante.\n3. Infuser 5-7 min, filtrer.\n4. Boire tiède.",
     "bariatric_phase": "liquide"},
    
    # Phase 2 - Mixé/Lisse
    {"name": "Velouté de carottes protéiné", "category": "bariatric_mixe", "nutriscore": "A", "calories": 120, "proteins": 15, "carbs": 12, "fats": 2, "prep_time": 25,
     "image": "https://images.unsplash.com/photo-1603105037880-880cd4edfb0d?w=400",
     "ingredients": ["Carottes 300g", "Protéines en poudre neutres 20g", "Bouillon de légumes 30cl", "Cumin"],
     "instructions": "1. Cuire les carottes dans le bouillon 20 min.\n2. Mixer très finement.\n3. Ajouter les protéines, bien mélanger.\n4. Servir tiède, texture très lisse.",
     "bariatric_phase": "mixe"},
    {"name": "Purée de courgettes au fromage frais", "category": "bariatric_mixe", "nutriscore": "A", "calories": 90, "proteins": 8, "carbs": 6, "fats": 4, "prep_time": 20,
     "image": "https://images.unsplash.com/photo-1540420773420-3366772f4999?w=400",
     "ingredients": ["Courgettes 400g", "Fromage frais 0% 100g", "Herbes de Provence"],
     "instructions": "1. Cuire les courgettes à la vapeur 15 min.\n2. Mixer avec le fromage frais.\n3. Assaisonner légèrement.\n4. La texture doit être parfaitement lisse.",
     "bariatric_phase": "mixe"},
    {"name": "Compote de pommes sans sucre", "category": "bariatric_mixe", "nutriscore": "A", "calories": 50, "proteins": 0, "carbs": 12, "fats": 0, "prep_time": 20,
     "image": "https://images.unsplash.com/photo-1488477181946-6428a0291777?w=400",
     "ingredients": ["Pommes Golden 4", "Eau 5cl", "Cannelle"],
     "instructions": "1. Éplucher et couper les pommes.\n2. Cuire à feu doux avec l'eau 15 min.\n3. Mixer finement.\n4. Ajouter une pincée de cannelle.",
     "bariatric_phase": "mixe"},
    {"name": "Mousse de saumon", "category": "bariatric_mixe", "nutriscore": "A", "calories": 150, "proteins": 18, "carbs": 2, "fats": 8, "prep_time": 15,
     "image": "https://images.unsplash.com/photo-1467003909585-2f8a72700288?w=400",
     "ingredients": ["Saumon cuit 150g", "Fromage frais 50g", "Citron 1/2", "Aneth"],
     "instructions": "1. Émietter le saumon.\n2. Mixer avec le fromage frais et le jus de citron.\n3. Obtenir une texture très lisse.\n4. Servir frais avec de l'aneth.",
     "bariatric_phase": "mixe"},
    {"name": "Velouté de potiron protéiné", "category": "bariatric_mixe", "nutriscore": "A", "calories": 100, "proteins": 14, "carbs": 10, "fats": 1, "prep_time": 30,
     "image": "https://images.unsplash.com/photo-1603105037880-880cd4edfb0d?w=400",
     "ingredients": ["Potiron 400g", "Protéines en poudre 20g", "Bouillon 30cl", "Muscade"],
     "instructions": "1. Cuire le potiron dans le bouillon 25 min.\n2. Mixer jusqu'à obtenir une texture veloutée.\n3. Incorporer les protéines.\n4. Assaisonner de muscade.",
     "bariatric_phase": "mixe"},
    {"name": "Purée de haricots verts au poulet", "category": "bariatric_mixe", "nutriscore": "A", "calories": 130, "proteins": 16, "carbs": 8, "fats": 4, "prep_time": 25,
     "image": "https://images.unsplash.com/photo-1540420773420-3366772f4999?w=400",
     "ingredients": ["Haricots verts 200g", "Blanc de poulet cuit 100g", "Bouillon 10cl"],
     "instructions": "1. Cuire les haricots verts 15 min.\n2. Mixer avec le poulet et le bouillon.\n3. La texture doit être totalement lisse.\n4. Réchauffer et servir.",
     "bariatric_phase": "mixe"},
    {"name": "Crème de betterave", "category": "bariatric_mixe", "nutriscore": "A", "calories": 80, "proteins": 6, "carbs": 10, "fats": 2, "prep_time": 20,
     "image": "https://images.unsplash.com/photo-1603105037880-880cd4edfb0d?w=400",
     "ingredients": ["Betterave cuite 200g", "Fromage blanc 0% 100g", "Ciboulette"],
     "instructions": "1. Mixer la betterave avec le fromage blanc.\n2. Passer au tamis si nécessaire.\n3. Servir frais avec ciboulette.",
     "bariatric_phase": "mixe"},
    {"name": "Purée d'avocat citronnée", "category": "bariatric_mixe", "nutriscore": "A", "calories": 140, "proteins": 2, "carbs": 6, "fats": 13, "prep_time": 5,
     "image": "https://images.unsplash.com/photo-1540420773420-3366772f4999?w=400",
     "ingredients": ["Avocat mûr 1", "Citron vert 1/2", "Sel"],
     "instructions": "1. Écraser l'avocat à la fourchette.\n2. Ajouter le jus de citron.\n3. Mixer pour obtenir une texture lisse.\n4. Consommer immédiatement.",
     "bariatric_phase": "mixe"},
    
    # Phase 3 - Mou/Tendre
    {"name": "Œufs brouillés moelleux", "category": "bariatric_mou", "nutriscore": "A", "calories": 180, "proteins": 14, "carbs": 1, "fats": 14, "prep_time": 10,
     "image": "https://images.unsplash.com/photo-1525351484163-7529414344d8?w=400",
     "ingredients": ["Œufs 3", "Lait écrémé 2 c.s.", "Sel", "Poivre"],
     "instructions": "1. Battre les œufs avec le lait.\n2. Cuire à feu très doux en remuant.\n3. Retirer du feu quand encore crémeux.\n4. La texture doit être très tendre.",
     "bariatric_phase": "mou"},
    {"name": "Filet de poisson vapeur", "category": "bariatric_mou", "nutriscore": "A", "calories": 120, "proteins": 25, "carbs": 0, "fats": 2, "prep_time": 15,
     "image": "https://images.unsplash.com/photo-1467003909585-2f8a72700288?w=400",
     "ingredients": ["Filet de cabillaud 150g", "Citron", "Aneth", "Sel"],
     "instructions": "1. Placer le poisson dans un panier vapeur.\n2. Cuire 10-12 min jusqu'à ce qu'il s'effrite.\n3. Servir avec citron et aneth.\n4. Le poisson doit se défaire facilement.",
     "bariatric_phase": "mou"},
    {"name": "Poulet effiloché tendre", "category": "bariatric_mou", "nutriscore": "A", "calories": 150, "proteins": 28, "carbs": 0, "fats": 4, "prep_time": 45,
     "image": "https://images.unsplash.com/photo-1604908176997-125f25cc6f3d?w=400",
     "ingredients": ["Blanc de poulet 200g", "Bouillon de légumes 30cl", "Herbes"],
     "instructions": "1. Pocher le poulet dans le bouillon 30-40 min.\n2. Effilocher finement à la fourchette.\n3. Humidifier avec un peu de bouillon.\n4. La viande doit être très tendre.",
     "bariatric_phase": "mou"},
    {"name": "Fromage blanc aux fruits", "category": "bariatric_mou", "nutriscore": "A", "calories": 100, "proteins": 12, "carbs": 10, "fats": 1, "prep_time": 5,
     "image": "https://images.unsplash.com/photo-1488477181946-6428a0291777?w=400",
     "ingredients": ["Fromage blanc 0% 150g", "Banane mûre 1/2", "Cannelle"],
     "instructions": "1. Écraser la banane très mûre.\n2. Mélanger au fromage blanc.\n3. Saupoudrer de cannelle.\n4. La texture doit être onctueuse.",
     "bariatric_phase": "mou"},
    {"name": "Omelette soufflée", "category": "bariatric_mou", "nutriscore": "A", "calories": 160, "proteins": 12, "carbs": 2, "fats": 12, "prep_time": 15,
     "image": "https://images.unsplash.com/photo-1510693206972-df098062cb71?w=400",
     "ingredients": ["Œufs 2", "Lait écrémé 3 c.s.", "Fines herbes", "Sel"],
     "instructions": "1. Séparer blancs et jaunes.\n2. Monter les blancs en neige.\n3. Incorporer les jaunes et le lait.\n4. Cuire doucement. L'omelette doit être baveuse.",
     "bariatric_phase": "mou"},
    {"name": "Ricotta aux herbes", "category": "bariatric_mou", "nutriscore": "A", "calories": 90, "proteins": 10, "carbs": 3, "fats": 5, "prep_time": 5,
     "image": "https://images.unsplash.com/photo-1540420773420-3366772f4999?w=400",
     "ingredients": ["Ricotta 100g", "Basilic frais", "Huile d'olive 1 c.c.", "Sel, poivre"],
     "instructions": "1. Mélanger la ricotta avec le basilic ciselé.\n2. Ajouter l'huile d'olive.\n3. Assaisonner légèrement.\n4. Servir à température ambiante.",
     "bariatric_phase": "mou"},
    {"name": "Thon en conserve émietté", "category": "bariatric_mou", "nutriscore": "A", "calories": 130, "proteins": 26, "carbs": 0, "fats": 3, "prep_time": 5,
     "image": "https://images.unsplash.com/photo-1467003909585-2f8a72700288?w=400",
     "ingredients": ["Thon au naturel 120g", "Fromage frais 1 c.s.", "Citron"],
     "instructions": "1. Égoutter et émietter finement le thon.\n2. Mélanger avec le fromage frais.\n3. Ajouter quelques gouttes de citron.\n4. La texture doit être facile à mastiquer.",
     "bariatric_phase": "mou"},
    {"name": "Compote de poire vanillée", "category": "bariatric_mou", "nutriscore": "A", "calories": 60, "proteins": 0, "carbs": 14, "fats": 0, "prep_time": 20,
     "image": "https://images.unsplash.com/photo-1488477181946-6428a0291777?w=400",
     "ingredients": ["Poires mûres 3", "Vanille 1/2 gousse", "Eau 5cl"],
     "instructions": "1. Éplucher et couper les poires.\n2. Cuire avec l'eau et la vanille 15 min.\n3. Écraser grossièrement à la fourchette.\n4. La texture doit rester un peu morcelée.",
     "bariatric_phase": "mou"},
    
    # Phase 4 - Normal adapté
    {"name": "Saumon grillé petite portion", "category": "bariatric_normal", "nutriscore": "A", "calories": 180, "proteins": 22, "carbs": 0, "fats": 10, "prep_time": 15,
     "image": "https://images.unsplash.com/photo-1467003909585-2f8a72700288?w=400",
     "ingredients": ["Pavé de saumon 100g", "Huile d'olive 1 c.c.", "Citron", "Aneth"],
     "instructions": "1. Badigeonner le saumon d'huile.\n2. Cuire au grill 4 min par côté.\n3. Servir avec citron.\n4. Mâcher très lentement, petites bouchées.",
     "bariatric_phase": "normal"},
    {"name": "Poulet grillé aux herbes (petite portion)", "category": "bariatric_normal", "nutriscore": "A", "calories": 150, "proteins": 28, "carbs": 0, "fats": 4, "prep_time": 20,
     "image": "https://images.unsplash.com/photo-1598103442097-8b74394b95c6?w=400",
     "ingredients": ["Blanc de poulet 100g", "Herbes de Provence", "Huile d'olive 1 c.c."],
     "instructions": "1. Aplatir légèrement le poulet.\n2. Assaisonner et griller 6-7 min par côté.\n3. Laisser reposer avant de trancher.\n4. Couper en très petits morceaux.",
     "bariatric_phase": "normal"},
    {"name": "Légumes vapeur assortis", "category": "bariatric_normal", "nutriscore": "A", "calories": 60, "proteins": 3, "carbs": 10, "fats": 1, "prep_time": 20,
     "image": "https://images.unsplash.com/photo-1540420773420-3366772f4999?w=400",
     "ingredients": ["Haricots verts 100g", "Courgettes 100g", "Carottes 100g", "Sel"],
     "instructions": "1. Couper les légumes en petits morceaux.\n2. Cuire à la vapeur 15-18 min.\n3. Les légumes doivent être bien tendres.\n4. Manger lentement en mâchant bien.",
     "bariatric_phase": "normal"},
    {"name": "Tofu soyeux nature", "category": "bariatric_normal", "nutriscore": "A", "calories": 70, "proteins": 8, "carbs": 2, "fats": 4, "prep_time": 5,
     "image": "https://images.unsplash.com/photo-1540420773420-3366772f4999?w=400",
     "ingredients": ["Tofu soyeux 100g", "Sauce soja légère 1 c.c.", "Sésame"],
     "instructions": "1. Couper le tofu en cubes.\n2. Arroser de sauce soja.\n3. Parsemer de sésame.\n4. Manger par petites bouchées.",
     "bariatric_phase": "normal"},
    {"name": "Omelette aux fines herbes (petite)", "category": "bariatric_normal", "nutriscore": "A", "calories": 140, "proteins": 12, "carbs": 1, "fats": 10, "prep_time": 10,
     "image": "https://images.unsplash.com/photo-1510693206972-df098062cb71?w=400",
     "ingredients": ["Œufs 2", "Ciboulette", "Persil", "Beurre 5g"],
     "instructions": "1. Battre les œufs avec les herbes.\n2. Cuire dans le beurre à feu moyen.\n3. Plier quand encore baveuse.\n4. Couper en petits morceaux avant de manger.",
     "bariatric_phase": "normal"},
]

# Additional international recipes to reach 3000+
INTERNATIONAL_BASE = [
    {"name": "Pad Thai", "category": "pates", "nutriscore": "B", "calories": 380, "area": "Thai"},
    {"name": "Sushi Maki", "category": "poisson", "nutriscore": "A", "calories": 250, "area": "Japanese"},
    {"name": "Tacos al Pastor", "category": "viande", "nutriscore": "C", "calories": 350, "area": "Mexican"},
    {"name": "Falafel", "category": "vegetarien", "nutriscore": "A", "calories": 280, "area": "Middle Eastern"},
    {"name": "Pho Bo", "category": "viande", "nutriscore": "B", "calories": 320, "area": "Vietnamese"},
    {"name": "Tikka Masala", "category": "volaille", "nutriscore": "B", "calories": 400, "area": "Indian"},
    {"name": "Paella", "category": "poisson", "nutriscore": "B", "calories": 420, "area": "Spanish"},
    {"name": "Moussaka", "category": "viande", "nutriscore": "C", "calories": 380, "area": "Greek"},
    {"name": "Goulash", "category": "viande", "nutriscore": "C", "calories": 400, "area": "Hungarian"},
    {"name": "Bibimbap", "category": "viande", "nutriscore": "B", "calories": 350, "area": "Korean"},
]

def build_database():
    """Build complete recipe database"""
    all_recipes = []
    
    # 1. Add TheMealDB recipes (570)
    all_recipes.extend(MEALDB_RECIPES)
    print(f"Added {len(MEALDB_RECIPES)} TheMealDB recipes")
    
    # 2. Add French recipes (with unique IDs)
    for i, recipe in enumerate(FRENCH_RECIPES):
        recipe['id'] = f"fr_{i+1:04d}"
        recipe['source'] = 'French Cuisine'
        recipe['area'] = 'French'
        all_recipes.append(recipe)
    print(f"Added {len(FRENCH_RECIPES)} French recipes")
    
    # 3. Add Bariatric recipes
    for i, recipe in enumerate(BARIATRIC_RECIPES):
        recipe['id'] = f"bari_{i+1:04d}"
        recipe['source'] = 'Bariatric Nutrition'
        recipe['area'] = 'Bariatric'
        all_recipes.append(recipe)
    print(f"Added {len(BARIATRIC_RECIPES)} Bariatric recipes")
    
    print(f"\nTotal unique recipes: {len(all_recipes)}")
    return all_recipes

if __name__ == "__main__":
    recipes = build_database()
    
    # Save as Python module
    with open('recipes_database_final.py', 'w', encoding='utf-8') as f:
        f.write('"""Complete recipe database with 600+ real recipes"""\n\n')
        f.write(f'RECIPES = {repr(recipes)}\n\n')
        f.write('def get_recipes():\n')
        f.write('    return RECIPES\n\n')
        f.write(f'def get_recipe_count():\n')
        f.write(f'    return len(RECIPES)\n')
    
    print(f"\nSaved to recipes_database_final.py")
    
    # Stats by category
    categories = {}
    for r in recipes:
        cat = r.get('category', 'autre')
        categories[cat] = categories.get(cat, 0) + 1
    print("\nRecipes by category:")
    for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
        print(f"  {cat}: {count}")
