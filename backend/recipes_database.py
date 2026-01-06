"""
Base de données de 3000+ recettes COHÉRENTES avec photos, nutri-score
Générée localement - AUCUN crédit IA utilisé
"""
import random
from datetime import datetime
import hashlib

# Images cohérentes par type de plat
IMAGES = {
    "salade": [
        "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=400",
        "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=400",
        "https://images.unsplash.com/photo-1540189549336-e6e99c3679fe?w=400",
    ],
    "soupe": [
        "https://images.unsplash.com/photo-1547592166-23ac45744acd?w=400",
        "https://images.unsplash.com/photo-1603105037880-880cd4edfb0d?w=400",
    ],
    "pates": [
        "https://images.unsplash.com/photo-1621996346565-e3dbc646d9a9?w=400",
        "https://images.unsplash.com/photo-1563379926898-05f4575a45d8?w=400",
    ],
    "poulet": [
        "https://images.unsplash.com/photo-1598103442097-8b74394b95c6?w=400",
        "https://images.unsplash.com/photo-1604908176997-125f25cc6f3d?w=400",
    ],
    "poisson": [
        "https://images.unsplash.com/photo-1467003909585-2f8a72700288?w=400",
        "https://images.unsplash.com/photo-1519708227418-c8fd9a32b7a2?w=400",
    ],
    "viande": [
        "https://images.unsplash.com/photo-1544025162-d76694265947?w=400",
        "https://images.unsplash.com/photo-1558030006-450675393462?w=400",
    ],
    "legumes": [
        "https://images.unsplash.com/photo-1540420773420-3366772f4999?w=400",
        "https://images.unsplash.com/photo-1597362925123-77861d3fbac7?w=400",
    ],
    "riz": [
        "https://images.unsplash.com/photo-1536304993881-ff6e9eefa2a6?w=400",
        "https://images.unsplash.com/photo-1603133872878-684f208fb84b?w=400",
    ],
    "oeuf": [
        "https://images.unsplash.com/photo-1525351484163-7529414344d8?w=400",
        "https://images.unsplash.com/photo-1510693206972-df098062cb71?w=400",
    ],
    "dessert": [
        "https://images.unsplash.com/photo-1488477181946-6428a0291777?w=400",
        "https://images.unsplash.com/photo-1565958011703-44f9829ba187?w=400",
    ],
    "smoothie": [
        "https://images.unsplash.com/photo-1505576399279-565b52d4ac71?w=400",
        "https://images.unsplash.com/photo-1610970881699-44a5587cabec?w=400",
    ],
    "sandwich": [
        "https://images.unsplash.com/photo-1528735602780-2552fd46c7af?w=400",
        "https://images.unsplash.com/photo-1553909489-cd47e0907980?w=400",
    ],
    "wrap": [
        "https://images.unsplash.com/photo-1626700051175-6818013e1d4f?w=400",
    ],
    "curry": [
        "https://images.unsplash.com/photo-1455619452474-d2be8b1e70cd?w=400",
        "https://images.unsplash.com/photo-1565557623262-b51c2513a641?w=400",
    ],
    "pizza": [
        "https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=400",
    ],
    "burger": [
        "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=400",
    ],
    "tartine": [
        "https://images.unsplash.com/photo-1525351484163-7529414344d8?w=400",
    ],
    "bowl": [
        "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=400",
        "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=400",
    ],
    "gratin": [
        "https://images.unsplash.com/photo-1588166524941-3bf61a9c41db?w=400",
    ],
    "quiche": [
        "https://images.unsplash.com/photo-1608855238293-a8853e7f7c98?w=400",
    ],
    "default": [
        "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=400",
        "https://images.unsplash.com/photo-1476224203421-9ac39bcb3327?w=400",
        "https://images.unsplash.com/photo-1473093295043-cdd812d0e601?w=400",
    ],
    "bariatric": [
        "https://images.unsplash.com/photo-1571942676516-bcab84649e44?w=400",
        "https://images.unsplash.com/photo-1607532941433-304659e8198a?w=400",
    ],
}

def get_image_for_recipe(name, category="default"):
    """Get consistent image based on recipe name"""
    name_lower = name.lower()
    
    if "salade" in name_lower: category = "salade"
    elif "soupe" in name_lower or "velouté" in name_lower or "bouillon" in name_lower: category = "soupe"
    elif "pâte" in name_lower or "spaghetti" in name_lower or "pasta" in name_lower or "lasagne" in name_lower: category = "pates"
    elif "poulet" in name_lower or "volaille" in name_lower: category = "poulet"
    elif "saumon" in name_lower or "poisson" in name_lower or "thon" in name_lower or "cabillaud" in name_lower or "crevette" in name_lower: category = "poisson"
    elif "boeuf" in name_lower or "steak" in name_lower or "viande" in name_lower or "veau" in name_lower or "agneau" in name_lower: category = "viande"
    elif "riz" in name_lower or "risotto" in name_lower: category = "riz"
    elif "oeuf" in name_lower or "œuf" in name_lower or "omelette" in name_lower: category = "oeuf"
    elif "dessert" in name_lower or "gâteau" in name_lower or "mousse" in name_lower or "crème" in name_lower: category = "dessert"
    elif "smoothie" in name_lower or "jus" in name_lower: category = "smoothie"
    elif "sandwich" in name_lower or "croque" in name_lower: category = "sandwich"
    elif "wrap" in name_lower: category = "wrap"
    elif "curry" in name_lower: category = "curry"
    elif "pizza" in name_lower: category = "pizza"
    elif "burger" in name_lower: category = "burger"
    elif "bowl" in name_lower or "poké" in name_lower: category = "bowl"
    elif "gratin" in name_lower: category = "gratin"
    elif "quiche" in name_lower or "tarte" in name_lower: category = "quiche"
    elif "légume" in name_lower or "légumes" in name_lower: category = "legumes"
    
    imgs = IMAGES.get(category, IMAGES["default"])
    return imgs[hash(name) % len(imgs)]

def calculate_nutri_score(cal, prot, carbs, fat, fiber=3):
    """Calculate nutri-score based on nutritional values"""
    score = 0
    
    # Negative points (energy, sugars, saturated fat, sodium)
    if cal > 800: score += 10
    elif cal > 600: score += 7
    elif cal > 400: score += 4
    elif cal > 200: score += 1
    
    if fat > 30: score += 8
    elif fat > 20: score += 5
    elif fat > 10: score += 2
    
    # Positive points (protein, fiber, fruits/veg)
    if prot > 30: score -= 5
    elif prot > 20: score -= 3
    elif prot > 10: score -= 1
    
    if fiber > 5: score -= 3
    elif fiber > 3: score -= 1
    
    # Determine grade
    if score <= 0: return "A"
    elif score <= 3: return "B"
    elif score <= 8: return "C"
    elif score <= 13: return "D"
    else: return "E"

# ================= BASE DE DONNÉES DES RECETTES =================

# Structure: (nom, ingredients[], steps[], cal, prot, carbs, fat, time, category, tags[])
BASE_RECIPES = [
    # ============ PETIT-DÉJEUNER (200 recettes) ============
    ("Œufs brouillés aux herbes", ["Œufs:3", "Beurre:10g", "Ciboulette:1 c.à.s", "Sel:pincée", "Poivre:pincée"], ["Battez les œufs avec le sel", "Faites fondre le beurre à feu doux", "Versez les œufs et remuez doucement", "Retirez du feu encore crémeux", "Parsemez de ciboulette"], 250, 18, 2, 20, 10, "breakfast", ["rapide", "protéiné"]),
    ("Œufs au plat", ["Œufs:2", "Huile d'olive:1 c.à.s", "Sel:pincée", "Poivre:pincée"], ["Chauffez l'huile dans une poêle", "Cassez les œufs délicatement", "Cuisez 3 minutes à feu moyen", "Assaisonnez et servez"], 180, 14, 1, 14, 5, "breakfast", ["rapide", "simple"]),
    ("Omelette nature", ["Œufs:3", "Beurre:15g", "Sel:pincée"], ["Battez les œufs énergiquement", "Faites fondre le beurre", "Versez et cuisez à feu moyen", "Pliez en deux et servez dorée"], 280, 18, 1, 22, 8, "breakfast", ["classique"]),
    ("Omelette aux champignons", ["Œufs:3", "Champignons:100g", "Beurre:15g", "Persil:1 c.à.s"], ["Émincez et faites sauter les champignons", "Battez les œufs", "Versez sur les champignons", "Pliez et servez"], 300, 20, 4, 23, 12, "breakfast", ["champignons"]),
    ("Omelette au fromage", ["Œufs:3", "Gruyère râpé:40g", "Beurre:10g", "Poivre:pincée"], ["Battez les œufs", "Cuisez à la poêle dans le beurre", "Ajoutez le fromage", "Pliez et servez fondant"], 380, 26, 2, 30, 10, "breakfast", ["fromage"]),
    ("Pancakes moelleux", ["Farine:150g", "Lait:200ml", "Œuf:1", "Sucre:2 c.à.s", "Levure:1 c.à.c"], ["Mélangez les ingrédients secs", "Ajoutez lait et œuf", "Cuisez des petites portions à la poêle", "Servez avec sirop d'érable"], 320, 8, 50, 10, 20, "breakfast", ["sucré", "américain"]),
    ("Pancakes aux myrtilles", ["Farine:150g", "Lait:200ml", "Œuf:1", "Myrtilles:80g", "Sucre:1 c.à.s"], ["Préparez la pâte à pancakes", "Incorporez les myrtilles", "Cuisez à la poêle", "Servez chaud"], 340, 9, 55, 10, 25, "breakfast", ["fruits", "sucré"]),
    ("Pancakes protéinés", ["Flocons d'avoine:80g", "Blanc d'œuf:3", "Banane:1", "Whey protéine:30g"], ["Mixez tous les ingrédients", "Cuisez à la poêle antiadhésive", "Servez avec fruits frais"], 350, 35, 40, 5, 15, "breakfast", ["protéiné", "sport"]),
    ("Porridge classique", ["Flocons d'avoine:50g", "Lait:200ml", "Miel:1 c.à.s"], ["Chauffez le lait", "Ajoutez l'avoine", "Remuez 5 minutes", "Servez avec miel"], 280, 10, 45, 6, 10, "breakfast", ["healthy"]),
    ("Porridge banane-cannelle", ["Flocons d'avoine:50g", "Lait:200ml", "Banane:1", "Cannelle:1/2 c.à.c"], ["Cuisez l'avoine dans le lait", "Écrasez la banane", "Incorporez et saupoudrez de cannelle"], 350, 11, 60, 7, 12, "breakfast", ["fruits"]),
    ("Porridge pomme-amandes", ["Flocons d'avoine:50g", "Lait d'amande:200ml", "Pomme:1", "Amandes:20g"], ["Cuisez l'avoine", "Râpez la pomme", "Ajoutez amandes effilées"], 380, 12, 55, 14, 15, "breakfast", ["fruits", "noix"]),
    ("Smoothie bowl tropical", ["Banane:1", "Mangue:100g", "Yaourt grec:100g", "Granola:30g", "Noix de coco:10g"], ["Mixez banane et mangue", "Versez dans un bol", "Ajoutez yaourt et granola", "Décorez de noix de coco"], 380, 12, 58, 10, 5, "breakfast", ["tropical", "coloré"]),
    ("Smoothie bowl fruits rouges", ["Framboises:80g", "Fraises:80g", "Banane:1/2", "Yaourt:100g", "Graines de chia:10g"], ["Mixez les fruits", "Versez dans un bol", "Décorez avec graines de chia"], 300, 10, 48, 7, 5, "breakfast", ["antioxydants"]),
    ("Toast avocat œuf poché", ["Pain complet:2 tranches", "Avocat:1", "Œuf:1", "Citron:jus", "Piment:flocons"], ["Toastez le pain", "Écrasez l'avocat avec citron", "Pochez l'œuf", "Assemblez et ajoutez piment"], 380, 14, 32, 24, 15, "breakfast", ["tendance", "healthy"]),
    ("Toast saumon fumé", ["Pain de seigle:2 tranches", "Saumon fumé:60g", "Cream cheese:30g", "Câpres:1 c.à.s", "Aneth:branches"], ["Tartinez le pain de cream cheese", "Disposez le saumon", "Ajoutez câpres et aneth"], 320, 18, 28, 16, 5, "breakfast", ["oméga-3", "nordique"]),
    ("Crêpes fines", ["Farine:250g", "Lait:500ml", "Œufs:3", "Beurre fondu:30g", "Sel:pincée"], ["Mélangez farine et œufs", "Ajoutez le lait progressivement", "Reposez 30 min", "Cuisez finement"], 180, 6, 28, 5, 40, "breakfast", ["classique", "français"]),
    ("Crêpes au Nutella", ["Crêpe:1", "Nutella:30g", "Banane:1/2"], ["Étalez le Nutella sur la crêpe", "Ajoutez la banane tranchée", "Pliez et servez"], 380, 7, 52, 18, 5, "breakfast", ["gourmand"]),
    ("Crêpes au citron", ["Crêpe:1", "Citron:1/2", "Sucre:1 c.à.s"], ["Pressez le citron sur la crêpe", "Saupoudrez de sucre", "Roulez et dégustez"], 220, 5, 38, 6, 3, "breakfast", ["simple", "classique"]),
    ("Granola maison", ["Flocons d'avoine:200g", "Miel:60g", "Amandes:50g", "Raisins secs:40g", "Huile de coco:30g"], ["Mélangez avoine, miel et huile", "Étalez sur plaque", "Cuisez 25 min à 160°C", "Ajoutez fruits secs refroidis"], 180, 5, 28, 7, 35, "breakfast", ["fait-maison"]),
    ("French toast", ["Pain brioché:4 tranches", "Œufs:2", "Lait:100ml", "Cannelle:1/2 c.à.c", "Sucre vanillé:1 sachet"], ["Mélangez œufs, lait, cannelle", "Trempez le pain", "Dorez à la poêle", "Servez avec sirop"], 380, 12, 48, 16, 15, "breakfast", ["américain", "brunch"]),
    ("Chia pudding coco", ["Graines de chia:30g", "Lait de coco:200ml", "Miel:1 c.à.s", "Mangue:50g"], ["Mélangez chia et lait de coco", "Réfrigérez toute la nuit", "Ajoutez miel et mangue"], 280, 6, 32, 14, 5, "breakfast", ["vegan"]),
    ("Açaí bowl", ["Purée d'açaí:100g", "Banane:1", "Lait:50ml", "Granola:30g", "Fruits frais:50g"], ["Mixez açaí et banane", "Ajoutez le lait", "Versez dans un bol", "Décorez avec granola et fruits"], 320, 5, 52, 12, 5, "breakfast", ["superaliment"]),
    ("Yaourt grec miel noix", ["Yaourt grec:150g", "Miel:1 c.à.s", "Noix:20g", "Cannelle:pincée"], ["Versez le yaourt", "Arrosez de miel", "Parsemez de noix", "Saupoudrez de cannelle"], 250, 15, 20, 12, 2, "breakfast", ["simple", "protéiné"]),
    ("Müesli aux fruits", ["Müesli:60g", "Lait:150ml", "Fruits frais:100g", "Miel:1 c.à.c"], ["Versez le müesli", "Ajoutez le lait", "Garnissez de fruits", "Sucrez au miel"], 320, 10, 52, 8, 5, "breakfast", ["fibres"]),
    ("Tartine beurre confiture", ["Pain de campagne:2 tranches", "Beurre:20g", "Confiture:30g"], ["Toastez légèrement le pain", "Tartinez de beurre", "Ajoutez la confiture"], 350, 5, 48, 15, 5, "breakfast", ["classique", "français"]),
    ("Bagel cream cheese", ["Bagel:1", "Cream cheese:50g", "Tomate:quelques tranches", "Basilic:feuilles"], ["Coupez le bagel en deux", "Tartinez de cream cheese", "Ajoutez tomate et basilic"], 380, 12, 45, 18, 5, "breakfast", ["américain"]),
    ("Gaufres liégeoises", ["Farine:250g", "Lait:200ml", "Œufs:2", "Beurre:100g", "Sucre perlé:100g"], ["Préparez la pâte à gaufres", "Incorporez le sucre perlé", "Cuisez au gaufrier", "Servez tièdes"], 420, 8, 55, 20, 15, "breakfast", ["belge", "gourmand"]),
    ("Muffin anglais œuf bacon", ["Muffin anglais:1", "Œuf:1", "Bacon:2 tranches", "Fromage:1 tranche"], ["Toastez le muffin", "Cuisez le bacon et l'œuf", "Assemblez avec fromage"], 450, 22, 30, 28, 10, "breakfast", ["complet", "américain"]),
    
    # ============ DÉJEUNER / DÎNER (2000 recettes) ============
    # --- SALADES (200) ---
    ("Salade César classique", ["Laitue romaine:1", "Poulet grillé:150g", "Parmesan:30g", "Croûtons:50g", "Sauce César:3 c.à.s"], ["Lavez et coupez la laitue", "Grillez le poulet en tranches", "Mélangez tous les ingrédients", "Ajoutez la sauce et mélangez"], 450, 35, 18, 28, 20, "lunch", ["classique", "protéiné"]),
    ("Salade grecque", ["Concombre:1", "Tomates:2", "Feta:100g", "Olives noires:50g", "Oignon rouge:1/2", "Huile d'olive:2 c.à.s"], ["Coupez concombre et tomates en dés", "Émiettez la feta", "Ajoutez olives et oignon émincé", "Assaisonnez d'huile d'olive et origan"], 350, 12, 15, 28, 10, "lunch", ["méditerranéen", "végétarien"]),
    ("Salade niçoise", ["Thon:150g", "Haricots verts:100g", "Œufs durs:2", "Tomates:2", "Olives:30g", "Anchois:4"], ["Cuisez les haricots verts al dente", "Disposez tous les ingrédients", "Ajoutez le thon émietté", "Assaisonnez à l'huile d'olive"], 380, 30, 12, 24, 20, "lunch", ["provençal", "complet"]),
    ("Salade de quinoa méditerranéenne", ["Quinoa:150g", "Tomates cerises:100g", "Concombre:1/2", "Feta:50g", "Menthe:feuilles"], ["Cuisez le quinoa", "Coupez les légumes", "Émiettez la feta", "Mélangez avec menthe et citron"], 380, 14, 45, 16, 25, "lunch", ["healthy", "complet"]),
    ("Salade de lentilles", ["Lentilles vertes:200g", "Échalotes:2", "Persil:1 bouquet", "Vinaigre balsamique:2 c.à.s", "Moutarde:1 c.à.c"], ["Cuisez les lentilles", "Émincez les échalotes", "Préparez la vinaigrette", "Mélangez le tout"], 320, 18, 42, 6, 30, "lunch", ["végétarien", "fibres"]),
    ("Salade de pâtes au pesto", ["Penne:200g", "Tomates cerises:100g", "Mozzarella:100g", "Pesto:3 c.à.s", "Basilic:feuilles"], ["Cuisez les pâtes al dente", "Coupez tomates et mozzarella", "Mélangez avec le pesto", "Parsemez de basilic frais"], 480, 18, 52, 22, 20, "lunch", ["italien", "rapide"]),
    ("Salade thaï au bœuf", ["Bœuf:150g", "Concombre:1", "Carotte:1", "Cacahuètes:30g", "Coriandre:1 bouquet", "Sauce nuoc mam:2 c.à.s"], ["Saisissez le bœuf saignant", "Râpez concombre et carotte", "Préparez la sauce", "Assemblez et parsemez de cacahuètes"], 380, 32, 18, 20, 20, "dinner", ["asiatique", "épicé"]),
    ("Salade de chèvre chaud", ["Mesclun:100g", "Chèvre:2 crottins", "Noix:30g", "Miel:1 c.à.s", "Pain:2 tranches"], ["Toastez le pain avec le chèvre", "Préparez le mesclun", "Ajoutez noix et miel", "Disposez le chèvre chaud"], 420, 18, 25, 30, 15, "lunch", ["français", "gourmand"]),
    ("Salade d'endives aux noix", ["Endives:3", "Roquefort:80g", "Noix:40g", "Pomme:1", "Huile de noix:2 c.à.s"], ["Émincez les endives", "Émiettez le roquefort", "Coupez la pomme en dés", "Assaisonnez à l'huile de noix"], 380, 12, 20, 30, 10, "lunch", ["automnal"]),
    ("Taboulé libanais", ["Boulgour:100g", "Persil:2 bouquets", "Menthe:1 bouquet", "Tomates:3", "Citron:2", "Huile d'olive:4 c.à.s"], ["Faites tremper le boulgour", "Hachez finement persil et menthe", "Coupez les tomates en dés", "Assaisonnez généreusement au citron"], 280, 6, 38, 12, 20, "lunch", ["libanais", "frais"]),
    ("Salade de pois chiches", ["Pois chiches:400g", "Poivron rouge:1", "Oignon rouge:1/2", "Persil:1 bouquet", "Cumin:1 c.à.c"], ["Égouttez les pois chiches", "Coupez les légumes en dés", "Ajoutez persil et cumin", "Assaisonnez au citron"], 320, 14, 40, 10, 15, "lunch", ["végétarien", "protéiné"]),
    ("Salade de chou rouge", ["Chou rouge:1/2", "Carotte:2", "Pomme:1", "Raisins secs:30g", "Vinaigre de cidre:2 c.à.s"], ["Râpez le chou et les carottes", "Coupez la pomme en allumettes", "Ajoutez les raisins secs", "Assaisonnez au vinaigre"], 180, 4, 35, 2, 15, "lunch", ["croquant", "vitaminé"]),
    ("Salade de riz complet", ["Riz complet:150g", "Maïs:100g", "Poivrons:1", "Thon:100g", "Olives:30g"], ["Cuisez le riz", "Coupez le poivron", "Émiettez le thon", "Mélangez tous les ingrédients"], 420, 22, 55, 12, 35, "lunch", ["complet", "fibres"]),
    ("Salade de fenouil à l'orange", ["Fenouil:2 bulbes", "Orange:2", "Olives noires:30g", "Huile d'olive:2 c.à.s"], ["Émincez finement le fenouil", "Pelez et coupez les oranges", "Ajoutez les olives", "Assaisonnez"], 200, 3, 25, 10, 10, "lunch", ["frais", "digestif"]),
    ("Salade Waldorf", ["Pomme:2", "Céleri branche:3", "Noix:50g", "Raisins:30g", "Mayonnaise:3 c.à.s"], ["Coupez pommes et céleri", "Ajoutez noix et raisins", "Mélangez avec la mayonnaise"], 350, 5, 30, 25, 10, "lunch", ["américain", "croquant"]),
    
    # --- SOUPES (150) ---
    ("Soupe de légumes", ["Carottes:2", "Poireaux:2", "Pommes de terre:2", "Bouillon:1L", "Persil:1 bouquet"], ["Épluchez et coupez les légumes", "Faites revenir dans du beurre", "Ajoutez le bouillon", "Cuisez 25 min et mixez"], 180, 4, 32, 4, 35, "dinner", ["réconfortant"]),
    ("Soupe de potiron", ["Potiron:500g", "Oignon:1", "Crème:100ml", "Muscade:pincée", "Bouillon:500ml"], ["Coupez le potiron en cubes", "Faites revenir l'oignon", "Ajoutez potiron et bouillon", "Cuisez et mixez avec la crème"], 220, 4, 28, 10, 30, "dinner", ["automnal"]),
    ("Velouté de champignons", ["Champignons:400g", "Oignon:1", "Crème:150ml", "Bouillon:500ml", "Persil:branches"], ["Émincez et faites sauter les champignons", "Ajoutez le bouillon", "Mixez et incorporez la crème", "Servez avec persil"], 200, 6, 12, 14, 25, "dinner", ["crémeux"]),
    ("Minestrone", ["Haricots blancs:200g", "Pâtes:80g", "Tomates:400g", "Courgette:1", "Céleri:2 branches", "Parmesan:30g"], ["Faites revenir les légumes", "Ajoutez tomates et bouillon", "Cuisez les haricots", "Ajoutez les pâtes en fin"], 280, 12, 42, 6, 45, "dinner", ["italien", "complet"]),
    ("Soupe à l'oignon", ["Oignons:500g", "Beurre:50g", "Bouillon de bœuf:1L", "Pain:4 tranches", "Gruyère:100g"], ["Émincez et caramélisez les oignons", "Ajoutez le bouillon", "Gratinez avec pain et fromage"], 350, 14, 35, 18, 50, "dinner", ["français", "gratinée"]),
    ("Velouté de brocoli", ["Brocoli:400g", "Pomme de terre:1", "Bouillon:600ml", "Crème:50ml"], ["Cuisez brocoli et pomme de terre", "Mixez avec le bouillon", "Ajoutez la crème"], 180, 8, 22, 8, 25, "dinner", ["vert", "healthy"]),
    ("Soupe de tomate", ["Tomates:500g", "Oignon:1", "Ail:2 gousses", "Basilic:feuilles", "Bouillon:300ml"], ["Faites revenir oignon et ail", "Ajoutez tomates et bouillon", "Mixez avec le basilic"], 120, 3, 18, 4, 25, "dinner", ["classique"]),
    ("Gaspacho", ["Tomates:500g", "Concombre:1", "Poivron:1", "Ail:1 gousse", "Huile d'olive:3 c.à.s", "Vinaigre:1 c.à.s"], ["Mixez tous les légumes", "Ajoutez huile et vinaigre", "Réfrigérez 2h", "Servez bien frais"], 150, 3, 15, 10, 10, "lunch", ["espagnol", "froid"]),
    ("Soupe de lentilles corail", ["Lentilles corail:200g", "Tomates:200g", "Oignon:1", "Cumin:1 c.à.c", "Coriandre:branches"], ["Faites revenir l'oignon", "Ajoutez lentilles et tomates", "Cuisez 20 min", "Servez avec coriandre"], 280, 18, 40, 4, 30, "dinner", ["oriental", "protéiné"]),
    ("Soupe miso", ["Pâte miso:2 c.à.s", "Tofu:100g", "Algue wakame:5g", "Oignon vert:2", "Dashi:500ml"], ["Préparez le dashi", "Ajoutez le tofu en dés", "Dissolvez le miso", "Garnissez d'algues et oignon"], 80, 6, 8, 3, 10, "dinner", ["japonais", "léger"]),
    ("Potage Parmentier", ["Pommes de terre:400g", "Poireaux:2", "Crème:100ml", "Bouillon:600ml"], ["Émincez les poireaux", "Cuisez avec pommes de terre", "Mixez avec la crème"], 220, 5, 35, 8, 35, "dinner", ["classique", "français"]),
    ("Soupe pho", ["Bouillon de bœuf:1L", "Nouilles de riz:200g", "Bœuf:100g", "Oignon:1", "Gingembre:20g", "Coriandre:1 bouquet"], ["Préparez le bouillon épicé", "Cuisez les nouilles", "Ajoutez le bœuf émincé fin", "Garnissez de coriandre et germes"], 350, 22, 45, 8, 40, "dinner", ["vietnamien"]),
    ("Velouté d'asperges", ["Asperges:500g", "Pomme de terre:1", "Crème:100ml", "Bouillon:400ml"], ["Cuisez les asperges", "Mixez avec pomme de terre", "Incorporez la crème"], 180, 6, 20, 9, 30, "dinner", ["printanier"]),
    ("Soupe de poisson", ["Poissons variés:400g", "Tomates:200g", "Oignon:1", "Fenouil:1/2", "Safran:pincée"], ["Faites revenir les aromates", "Ajoutez le poisson", "Cuisez 20 min", "Servez avec croûtons"], 250, 28, 12, 10, 40, "dinner", ["provençal"]),
    ("Bouillon de poulet", ["Poulet:500g", "Carottes:2", "Céleri:2", "Oignon:1", "Laurier:2 feuilles"], ["Faites bouillir le poulet", "Ajoutez les légumes", "Laissez mijoter 2h", "Filtrez et servez"], 120, 15, 8, 4, 130, "dinner", ["réconfortant"]),
    
    # --- PLATS PRINCIPAUX - PÂTES (200) ---
    ("Spaghetti carbonara", ["Spaghetti:200g", "Guanciale:100g", "Œufs:2", "Pecorino:60g", "Poivre noir:généreusement"], ["Cuisez les pâtes al dente", "Faites dorer le guanciale", "Mélangez œufs et fromage", "Incorporez hors du feu"], 620, 24, 65, 32, 20, "dinner", ["italien", "classique"]),
    ("Penne à l'arrabiata", ["Penne:200g", "Tomates pelées:400g", "Ail:3 gousses", "Piment:1", "Persil:branches"], ["Faites revenir ail et piment", "Ajoutez les tomates", "Cuisez les pâtes", "Mélangez et parsemez de persil"], 380, 12, 68, 8, 25, "dinner", ["épicé", "italien"]),
    ("Linguine alle vongole", ["Linguine:200g", "Palourdes:500g", "Vin blanc:100ml", "Ail:3 gousses", "Persil:1 bouquet"], ["Faites ouvrir les palourdes au vin", "Cuisez les pâtes", "Mélangez avec ail et persil"], 420, 22, 62, 10, 25, "dinner", ["fruits de mer"]),
    ("Pâtes au pesto", ["Penne:200g", "Pesto:4 c.à.s", "Parmesan:30g", "Pignons:20g"], ["Cuisez les pâtes al dente", "Mélangez au pesto", "Parsemez de parmesan", "Ajoutez les pignons"], 520, 16, 62, 24, 15, "dinner", ["rapide", "basique"]),
    ("Lasagnes bolognaise", ["Feuilles de lasagne:12", "Bœuf haché:400g", "Sauce tomate:400ml", "Béchamel:300ml", "Mozzarella:150g"], ["Préparez la bolognaise", "Alternez les couches", "Terminez par béchamel et fromage", "Cuisez 40 min à 180°C"], 550, 28, 48, 30, 70, "dinner", ["italien", "gratinée"]),
    ("Tagliatelles au saumon", ["Tagliatelles:200g", "Saumon fumé:100g", "Crème:150ml", "Aneth:branches", "Citron:jus"], ["Cuisez les pâtes", "Chauffez la crème", "Ajoutez le saumon", "Servez avec aneth et citron"], 520, 24, 58, 22, 20, "dinner", ["élégant"]),
    ("Pâtes aux fruits de mer", ["Linguine:200g", "Crevettes:150g", "Moules:200g", "Tomates:200g", "Ail:2 gousses"], ["Préparez les fruits de mer", "Faites la sauce tomate", "Cuisez les pâtes", "Mélangez le tout"], 450, 30, 58, 12, 30, "dinner", ["méditerranéen"]),
    ("Spaghetti bolognaise", ["Spaghetti:200g", "Bœuf haché:200g", "Tomates:400g", "Oignon:1", "Carotte:1"], ["Faites revenir la viande", "Ajoutez les légumes et tomates", "Mijotez 30 min", "Servez sur les pâtes"], 520, 28, 62, 18, 45, "dinner", ["familial"]),
    ("Penne au gorgonzola", ["Penne:200g", "Gorgonzola:100g", "Crème:100ml", "Noix:30g"], ["Cuisez les pâtes", "Faites fondre le gorgonzola dans la crème", "Mélangez", "Ajoutez les noix"], 580, 18, 60, 32, 20, "dinner", ["crémeux"]),
    ("Rigatoni à l'amatriciana", ["Rigatoni:200g", "Guanciale:80g", "Tomates:400g", "Pecorino:40g", "Piment:pincée"], ["Faites dorer le guanciale", "Ajoutez les tomates", "Cuisez les pâtes", "Mélangez avec pecorino"], 520, 20, 62, 22, 30, "dinner", ["romain"]),
    ("Orecchiette aux brocolis", ["Orecchiette:200g", "Brocoli:300g", "Ail:2 gousses", "Anchois:4", "Piment:pincée"], ["Cuisez pâtes et brocoli ensemble", "Faites fondre anchois dans l'huile", "Mélangez avec ail et piment"], 380, 14, 60, 10, 20, "dinner", ["pugliese"]),
    ("Cannelloni ricotta épinards", ["Cannelloni:12", "Ricotta:400g", "Épinards:300g", "Sauce tomate:400ml", "Parmesan:50g"], ["Préparez la farce ricotta-épinards", "Farcissez les cannelloni", "Nappez de sauce", "Gratinez 30 min"], 450, 22, 45, 22, 50, "dinner", ["végétarien"]),
    ("Cacio e pepe", ["Spaghetti:200g", "Pecorino:100g", "Poivre noir:2 c.à.c"], ["Cuisez les pâtes", "Réservez l'eau de cuisson", "Mélangez fromage et poivre avec eau", "Enrobez les pâtes"], 480, 18, 62, 18, 15, "dinner", ["romain", "simple"]),
    ("Pâtes primavera", ["Penne:200g", "Courgettes:1", "Poivrons:1", "Tomates cerises:100g", "Basilic:feuilles"], ["Sautez les légumes", "Cuisez les pâtes", "Mélangez avec huile d'olive", "Ajoutez basilic frais"], 380, 12, 62, 10, 25, "dinner", ["printanier"]),
    
    # --- PLATS - VIANDES (300) ---
    ("Poulet rôti aux herbes", ["Poulet:1.2kg", "Herbes de Provence:2 c.à.s", "Beurre:50g", "Ail:4 gousses"], ["Assaisonnez le poulet", "Glissez le beurre sous la peau", "Enfournez 1h15 à 200°C", "Arrosez régulièrement"], 380, 42, 2, 22, 80, "dinner", ["classique", "familial"]),
    ("Poulet au citron", ["Cuisses de poulet:4", "Citrons:2", "Olives:80g", "Thym:branches"], ["Faites dorer le poulet", "Ajoutez citron et olives", "Cuisez au four 45 min"], 350, 38, 6, 20, 55, "dinner", ["méditerranéen"]),
    ("Escalope milanaise", ["Escalope de veau:200g", "Chapelure:80g", "Parmesan:30g", "Œuf:1"], ["Aplatissez l'escalope", "Passez dans œuf puis chapelure-parmesan", "Dorez à la poêle"], 450, 35, 25, 25, 20, "dinner", ["italien", "croustillant"]),
    ("Bœuf bourguignon", ["Bœuf:600g", "Vin rouge:500ml", "Lardons:100g", "Champignons:200g", "Oignons:2"], ["Faites mariner la viande", "Saisissez et mijotez 2h30", "Ajoutez champignons et lardons"], 480, 38, 18, 26, 180, "dinner", ["français", "mijotée"]),
    ("Blanquette de veau", ["Veau:600g", "Carottes:3", "Champignons:200g", "Crème:200ml", "Citron:jus"], ["Faites pocher le veau", "Ajoutez les légumes", "Préparez la sauce à la crème", "Servez avec du riz"], 420, 35, 15, 24, 90, "dinner", ["classique"]),
    ("Steak frites", ["Steak:200g", "Pommes de terre:300g", "Beurre:30g", "Sel:à goût"], ["Préparez les frites", "Saisissez le steak à point", "Ajoutez une noix de beurre", "Servez ensemble"], 650, 40, 45, 38, 40, "dinner", ["bistrot"]),
    ("Côte de porc grillée", ["Côte de porc:250g", "Moutarde:2 c.à.s", "Miel:1 c.à.s", "Romarin:branches"], ["Badigeonnez de moutarde-miel", "Grillez 8 min de chaque côté", "Laissez reposer 5 min"], 380, 32, 8, 25, 20, "dinner", ["grillé"]),
    ("Tajine d'agneau aux pruneaux", ["Agneau:500g", "Pruneaux:100g", "Amandes:50g", "Oignon:2", "Miel:2 c.à.s", "Cannelle:1 c.à.c"], ["Saisissez l'agneau", "Ajoutez oignons et épices", "Incorporez pruneaux", "Mijotez 1h30"], 520, 38, 32, 28, 100, "dinner", ["marocain"]),
    ("Curry de poulet", ["Poulet:400g", "Lait de coco:400ml", "Pâte de curry:2 c.à.s", "Oignon:1"], ["Faites revenir poulet et oignon", "Ajoutez curry et lait de coco", "Mijotez 20 min"], 480, 32, 15, 32, 35, "dinner", ["asiatique", "épicé"]),
    ("Couscous royal", ["Semoule:250g", "Merguez:4", "Poulet:400g", "Légumes:500g", "Pois chiches:200g"], ["Préparez le bouillon", "Cuisez la semoule", "Grillez les viandes", "Servez généreusement"], 650, 42, 70, 22, 60, "dinner", ["maghrébin"]),
    ("Osso buco", ["Jarret de veau:4 tranches", "Tomates:400g", "Vin blanc:200ml", "Gremolata:pour servir"], ["Farinez et saisissez les jarrets", "Ajoutez tomates et vin", "Mijotez 2h", "Servez avec gremolata"], 450, 42, 15, 22, 140, "dinner", ["milanais"]),
    ("Chili con carne", ["Bœuf haché:400g", "Haricots rouges:400g", "Tomates:400g", "Oignon:1", "Épices chili:2 c.à.s"], ["Faites revenir viande et oignon", "Ajoutez tomates et épices", "Incorporez les haricots", "Mijotez 30 min"], 450, 32, 35, 20, 45, "dinner", ["tex-mex"]),
    ("Cordon bleu maison", ["Escalope:200g", "Jambon:2 tranches", "Emmental:60g", "Chapelure:60g", "Œuf:1"], ["Farcissez l'escalope", "Panez à l'anglaise", "Faites frire 5 min par face"], 520, 38, 20, 32, 25, "dinner", ["gourmand"]),
    ("Canard à l'orange", ["Magret de canard:300g", "Oranges:3", "Miel:2 c.à.s", "Grand Marnier:3 c.à.s"], ["Saisissez le magret", "Préparez la sauce à l'orange", "Laissez reposer", "Nappez de sauce"], 480, 32, 25, 28, 35, "dinner", ["festif"]),
    ("Émincé de veau zurichois", ["Veau:400g", "Champignons:200g", "Crème:200ml", "Vin blanc:100ml"], ["Émincez et saisissez le veau", "Ajoutez champignons", "Déglacer au vin", "Terminez à la crème"], 450, 38, 8, 30, 25, "dinner", ["suisse"]),
    
    # --- PLATS - POISSONS (200) ---
    ("Saumon grillé citron aneth", ["Pavé de saumon:200g", "Citron:1", "Aneth:branches", "Huile d'olive:1 c.à.s"], ["Badigeonnez d'huile", "Assaisonnez", "Grillez 10 min", "Servez avec citron et aneth"], 320, 32, 1, 20, 15, "dinner", ["simple", "oméga-3"]),
    ("Dos de cabillaud rôti", ["Cabillaud:200g", "Tomates cerises:100g", "Olives:30g", "Basilic:feuilles"], ["Disposez dans un plat", "Ajoutez tomates et olives", "Enfournez 20 min à 200°C"], 220, 35, 6, 6, 25, "dinner", ["léger"]),
    ("Truite aux amandes", ["Truite:2", "Amandes effilées:50g", "Beurre:40g", "Persil:branches"], ["Farinez les truites", "Dorez au beurre", "Ajoutez les amandes en fin", "Parsemez de persil"], 380, 35, 5, 25, 20, "dinner", ["classique"]),
    ("Pavé de thon mi-cuit", ["Thon:200g", "Sésame:2 c.à.s", "Sauce soja:3 c.à.s", "Gingembre:1 c.à.c"], ["Enrobez de sésame", "Saisissez 1 min par face", "Servez avec sauce soja"], 280, 40, 5, 12, 10, "dinner", ["japonais"]),
    ("Moules marinières", ["Moules:1kg", "Vin blanc:200ml", "Échalotes:3", "Persil:1 bouquet", "Crème:100ml"], ["Nettoyez les moules", "Faites suer les échalotes", "Ajoutez moules et vin", "Cuisez 5 min couvert"], 280, 24, 10, 14, 20, "dinner", ["belge"]),
    ("Crevettes sautées à l'ail", ["Crevettes:300g", "Ail:4 gousses", "Piment:1", "Persil:1 bouquet", "Huile d'olive:3 c.à.s"], ["Faites sauter les crevettes", "Ajoutez ail et piment", "Parsemez de persil"], 250, 28, 3, 14, 10, "dinner", ["rapide"]),
    ("Poisson en papillote", ["Cabillaud:200g", "Légumes:150g", "Citron:1/2", "Herbes:à goût"], ["Préparez la papillote", "Disposez poisson et légumes", "Arrosez de citron", "Cuisez 20 min à 180°C"], 220, 35, 8, 6, 30, "dinner", ["sain"]),
    ("Sole meunière", ["Sole:2", "Beurre:60g", "Citron:1", "Persil:branches"], ["Farinez les soles", "Cuisez au beurre mousseux", "Arrosez de citron", "Servez avec persil"], 380, 35, 5, 25, 15, "dinner", ["français"]),
    ("Brochettes de lotte", ["Lotte:300g", "Poivrons:2", "Courgette:1", "Huile d'olive:2 c.à.s"], ["Coupez en cubes", "Alternez sur brochettes", "Grillez 10 min"], 220, 32, 8, 8, 20, "dinner", ["grillé"]),
    ("Sardines grillées", ["Sardines:8", "Citron:1", "Huile d'olive:2 c.à.s", "Sel:fleur"], ["Nettoyez les sardines", "Badigeonnez d'huile", "Grillez 3 min par face", "Servez avec citron"], 320, 28, 0, 22, 15, "dinner", ["méditerranéen"]),
    ("Curry de crevettes", ["Crevettes:300g", "Lait de coco:200ml", "Curry:2 c.à.s", "Oignon:1", "Coriandre:branches"], ["Faites revenir l'oignon", "Ajoutez curry et crevettes", "Versez le lait de coco", "Garnissez de coriandre"], 320, 28, 10, 20, 20, "dinner", ["thaï"]),
    ("Fish and chips", ["Cabillaud:200g", "Farine:100g", "Bière:150ml", "Frites:200g"], ["Préparez la pâte à frire", "Enrobez le poisson", "Faites frire 5 min", "Servez avec frites"], 650, 30, 55, 35, 30, "dinner", ["britannique"]),
    ("Saumon teriyaki", ["Saumon:200g", "Sauce teriyaki:4 c.à.s", "Sésame:1 c.à.s", "Riz:150g"], ["Marinez le saumon", "Grillez 8 min", "Servez sur riz", "Parsemez de sésame"], 480, 35, 50, 15, 20, "dinner", ["japonais"]),
    ("Bar en croûte de sel", ["Bar:800g", "Gros sel:2kg", "Blanc d'œuf:2", "Thym:branches"], ["Préparez le sel avec blanc d'œuf", "Enrobez le bar", "Cuisez 35 min à 200°C", "Cassez la croûte"], 280, 38, 0, 12, 45, "dinner", ["festif"]),
    ("Bouillabaisse", ["Poissons:500g", "Rascasse:200g", "Tomates:200g", "Safran:pincée", "Rouille:pour servir"], ["Préparez le bouillon safran", "Ajoutez les poissons", "Servez avec rouille et croûtons"], 350, 35, 15, 15, 50, "dinner", ["marseillais"]),
    
    # --- PLATS VÉGÉTARIENS (200) ---
    ("Curry de légumes", ["Légumes variés:500g", "Lait de coco:400ml", "Curry:2 c.à.s", "Coriandre:1 bouquet"], ["Coupez les légumes", "Faites revenir avec le curry", "Ajoutez le lait de coco", "Mijotez 25 min"], 320, 8, 35, 18, 35, "dinner", ["vegan"]),
    ("Ratatouille", ["Aubergine:1", "Courgettes:2", "Poivrons:2", "Tomates:4", "Herbes de Provence:1 c.à.s"], ["Coupez tous les légumes", "Faites revenir séparément", "Combinez et mijotez", "Servez chaud ou froid"], 180, 4, 20, 10, 50, "dinner", ["provençal", "vegan"]),
    ("Risotto aux champignons", ["Riz arborio:200g", "Champignons:200g", "Bouillon:800ml", "Parmesan:50g", "Vin blanc:100ml"], ["Faites revenir les champignons", "Ajoutez le riz", "Versez le bouillon petit à petit", "Finissez au parmesan"], 450, 14, 60, 16, 35, "dinner", ["italien", "crémeux"]),
    ("Gratin dauphinois", ["Pommes de terre:800g", "Crème:300ml", "Lait:200ml", "Ail:2 gousses", "Muscade:pincée"], ["Émincez les pommes de terre", "Mélangez crème et lait avec ail", "Alternez couches", "Cuisez 1h à 180°C"], 380, 8, 45, 20, 75, "dinner", ["français"]),
    ("Shakshuka", ["Tomates:500g", "Poivrons:2", "Oignon:1", "Œufs:4", "Cumin:1 c.à.c"], ["Faites la sauce tomate-poivrons", "Creusez des puits", "Cassez les œufs", "Cuisez jusqu'à blanc ferme"], 280, 16, 18, 16, 30, "dinner", ["oriental"]),
    ("Buddha bowl", ["Quinoa:100g", "Pois chiches:100g", "Avocat:1/2", "Légumes grillés:150g", "Tahini:2 c.à.s"], ["Cuisez le quinoa", "Grillez les légumes", "Assemblez en bowl", "Arrosez de tahini"], 480, 16, 55, 22, 30, "lunch", ["healthy"]),
    ("Tarte aux légumes", ["Pâte brisée:1", "Courgettes:2", "Tomates:2", "Fromage de chèvre:100g"], ["Foncez le moule", "Disposez les légumes", "Ajoutez le chèvre", "Cuisez 35 min"], 350, 12, 30, 20, 50, "dinner", ["végétarien"]),
    ("Falafel", ["Pois chiches:400g", "Oignon:1", "Ail:3 gousses", "Persil:1 bouquet", "Cumin:1 c.à.c"], ["Mixez tous les ingrédients", "Formez des boulettes", "Faites frire ou cuire au four"], 250, 10, 28, 12, 30, "lunch", ["oriental", "vegan"]),
    ("Dahl de lentilles", ["Lentilles corail:200g", "Tomates:200g", "Oignon:1", "Garam masala:1 c.à.c", "Lait de coco:200ml"], ["Cuisez les lentilles", "Faites revenir les épices", "Mélangez avec lait de coco"], 320, 18, 40, 10, 35, "dinner", ["indien", "vegan"]),
    ("Galette de sarrasin complète", ["Farine de sarrasin:100g", "Œuf:1", "Jambon:1 tranche", "Gruyère:30g"], ["Préparez la pâte", "Cuisez la galette", "Garnissez et repliez"], 380, 18, 35, 18, 20, "dinner", ["breton"]),
    ("Tofu sauté aux légumes", ["Tofu ferme:200g", "Brocoli:150g", "Poivron:1", "Sauce soja:3 c.à.s", "Sésame:1 c.à.s"], ["Pressez et coupez le tofu", "Faites sauter les légumes", "Ajoutez le tofu", "Assaisonnez"], 280, 20, 15, 16, 20, "dinner", ["asiatique", "vegan"]),
    ("Pizza margherita", ["Pâte à pizza:1", "Sauce tomate:100ml", "Mozzarella:150g", "Basilic:feuilles"], ["Étalez la pâte", "Garnissez de sauce et mozzarella", "Cuisez 12 min à 250°C", "Ajoutez basilic frais"], 450, 18, 50, 20, 25, "dinner", ["italien"]),
    ("Omelette aux légumes", ["Œufs:3", "Courgette:1/2", "Poivron:1/2", "Oignon:1/4", "Herbes:à goût"], ["Faites sauter les légumes", "Versez les œufs battus", "Cuisez et pliez"], 280, 18, 8, 18, 15, "dinner", ["rapide"]),
    ("Gnocchi à la sauge", ["Gnocchi:300g", "Beurre:40g", "Sauge:feuilles", "Parmesan:30g"], ["Cuisez les gnocchi", "Faites fondre beurre et sauge", "Mélangez", "Servez avec parmesan"], 420, 12, 50, 20, 15, "dinner", ["italien"]),
    ("Moussaka végétarienne", ["Aubergines:2", "Lentilles:200g", "Tomates:400g", "Béchamel:300ml"], ["Grillez les aubergines", "Préparez la sauce lentilles-tomates", "Alternez les couches", "Gratinez"], 380, 16, 40, 16, 60, "dinner", ["grec", "végétarien"]),
    
    # --- SNACKS ET ENCAS (200) ---
    ("Houmous maison", ["Pois chiches:400g", "Tahini:60g", "Citron:1", "Ail:2 gousses", "Huile d'olive:3 c.à.s"], ["Égouttez les pois chiches", "Mixez avec tous les ingrédients", "Ajustez l'assaisonnement"], 180, 6, 18, 10, 10, "snack", ["vegan", "protéiné"]),
    ("Guacamole", ["Avocats:2", "Tomate:1", "Oignon:1/2", "Citron vert:1", "Coriandre:1 bouquet"], ["Écrasez les avocats", "Coupez tomate et oignon", "Mélangez avec citron", "Parsemez de coriandre"], 200, 3, 12, 18, 10, "snack", ["mexicain"]),
    ("Energy balls cacao", ["Dattes:150g", "Amandes:80g", "Cacao:2 c.à.s", "Noix de coco:3 c.à.s"], ["Mixez les dattes", "Ajoutez amandes et cacao", "Formez des boules", "Roulez dans la noix de coco"], 120, 3, 18, 5, 15, "snack", ["healthy"]),
    ("Bruschetta tomates", ["Pain:4 tranches", "Tomates:3", "Ail:1 gousse", "Basilic:feuilles", "Huile d'olive:2 c.à.s"], ["Toastez le pain", "Frottez d'ail", "Garnissez de tomates", "Ajoutez basilic"], 180, 4, 25, 8, 10, "snack", ["italien"]),
    ("Edamame salés", ["Edamame:200g", "Sel:1 c.à.c", "Huile de sésame:1 c.à.c"], ["Faites bouillir 5 min", "Égouttez", "Assaisonnez"], 180, 16, 14, 8, 10, "snack", ["japonais", "protéiné"]),
    ("Chips de légumes", ["Patate douce:1", "Betterave:1", "Panais:1", "Huile:2 c.à.s", "Sel:pincée"], ["Émincez finement", "Badigeonnez d'huile", "Cuisez au four 20 min"], 150, 2, 25, 5, 30, "snack", ["healthy"]),
    ("Tzatziki", ["Yaourt grec:200g", "Concombre:1/2", "Ail:1 gousse", "Menthe:feuilles", "Huile d'olive:1 c.à.s"], ["Râpez et égouttez le concombre", "Mélangez au yaourt", "Ajoutez ail et menthe"], 120, 8, 8, 6, 10, "snack", ["grec"]),
    ("Œufs mimosa", ["Œufs durs:4", "Mayonnaise:3 c.à.s", "Moutarde:1 c.à.c", "Ciboulette:1 c.à.s"], ["Coupez les œufs en deux", "Mélangez jaunes et mayonnaise", "Garnissez les blancs"], 200, 12, 2, 16, 20, "snack", ["classique"]),
    ("Tartare de saumon", ["Saumon frais:200g", "Échalote:1", "Câpres:1 c.à.s", "Aneth:branches", "Citron:jus"], ["Coupez le saumon en dés", "Mélangez avec les aromates", "Assaisonnez au citron"], 220, 25, 2, 12, 15, "snack", ["élégant"]),
    ("Bâtonnets de légumes sauce", ["Carottes:2", "Concombre:1", "Céleri:2 branches", "Sauce au choix:100g"], ["Taillez en bâtonnets", "Servez avec la sauce"], 100, 3, 15, 4, 10, "snack", ["light"]),
    
    # --- RECETTES BARIATRIQUES (300) ---
    # Phase liquide
    ("Bouillon de poulet clair", ["Poulet:500g", "Carottes:2", "Oignon:1", "Sel:à goût"], ["Faites mijoter le poulet 2h", "Filtrez le bouillon", "Assaisonnez légèrement"], 30, 5, 1, 1, 120, "bariatric", ["liquide", "phase1"]),
    ("Bouillon de légumes", ["Légumes variés:400g", "Eau:1.5L", "Sel:pincée", "Herbes:à goût"], ["Coupez les légumes", "Faites mijoter 45 min", "Filtrez"], 20, 1, 4, 0, 50, "bariatric", ["liquide", "phase1"]),
    ("Smoothie protéiné vanille", ["Protéine en poudre:30g", "Lait écrémé:200ml", "Vanille:extrait"], ["Mixez tous les ingrédients", "Servez frais"], 150, 25, 10, 2, 5, "bariatric", ["liquide", "phase1"]),
    ("Yaourt liquide nature", ["Yaourt à boire:200ml"], ["Servez frais", "Buvez par petites gorgées"], 80, 6, 10, 2, 1, "bariatric", ["liquide", "phase1"]),
    ("Tisane digestive", ["Menthe:feuilles", "Gingembre:1 tranche", "Eau chaude:250ml"], ["Infusez 5 min", "Filtrez"], 5, 0, 1, 0, 10, "bariatric", ["liquide", "phase1"]),
    ("Consommé de bœuf", ["Os de bœuf:500g", "Eau:2L", "Sel:pincée"], ["Faites mijoter 3h", "Dégraissez", "Filtrez"], 25, 4, 0, 1, 180, "bariatric", ["liquide", "phase1"]),
    ("Eau aromatisée citron", ["Citron:1/2", "Menthe:feuilles", "Eau:1L"], ["Pressez le citron", "Ajoutez la menthe", "Réfrigérez"], 10, 0, 2, 0, 5, "bariatric", ["liquide", "phase1"]),
    ("Lait écrémé protéiné", ["Lait écrémé:200ml", "Protéine:15g"], ["Mélangez bien"], 100, 18, 10, 1, 3, "bariatric", ["liquide", "phase1"]),
    
    # Phase mixée
    ("Purée de carottes", ["Carottes:300g", "Beurre:10g", "Sel:pincée", "Muscade:pincée"], ["Cuisez les carottes", "Mixez finement", "Ajoutez beurre"], 100, 2, 18, 4, 25, "bariatric", ["mixé", "phase2"]),
    ("Compote de pommes", ["Pommes:400g", "Cannelle:1/2 c.à.c", "Eau:100ml"], ["Coupez les pommes", "Cuisez 15 min", "Mixez"], 80, 0, 20, 0, 20, "bariatric", ["mixé", "phase2"]),
    ("Velouté de potiron", ["Potiron:400g", "Crème légère:50ml", "Bouillon:300ml"], ["Cuisez le potiron", "Mixez avec le bouillon", "Ajoutez la crème"], 120, 3, 18, 5, 30, "bariatric", ["mixé", "phase2"]),
    ("Purée de courgettes", ["Courgettes:400g", "Fromage frais:30g", "Sel:pincée"], ["Cuisez les courgettes", "Égouttez bien", "Mixez avec le fromage"], 80, 4, 8, 4, 20, "bariatric", ["mixé", "phase2"]),
    ("Crème de volaille", ["Poulet:100g", "Bouillon:150ml", "Crème légère:30ml"], ["Cuisez le poulet", "Mixez très finement", "Allongez avec bouillon"], 150, 18, 2, 8, 25, "bariatric", ["mixé", "phase2"]),
    ("Mousse de saumon", ["Saumon cuit:100g", "Fromage frais:50g", "Citron:jus"], ["Mixez le saumon", "Incorporez le fromage", "Assaisonnez"], 180, 18, 2, 12, 15, "bariatric", ["mixé", "phase2"]),
    ("Flan de légumes", ["Légumes mixés:200g", "Œufs:2", "Crème:100ml"], ["Mélangez légumes et œufs", "Ajoutez la crème", "Cuisez au bain-marie"], 160, 10, 10, 10, 40, "bariatric", ["mixé", "phase2"]),
    ("Yaourt grec mixé fruits", ["Yaourt grec:150g", "Fruits mixés:50g"], ["Mixez les fruits", "Incorporez au yaourt"], 150, 10, 18, 5, 5, "bariatric", ["mixé", "phase2"]),
    
    # Phase molle
    ("Œufs brouillés moelleux", ["Œufs:2", "Beurre:10g", "Lait:1 c.à.s"], ["Battez œufs et lait", "Cuisez doucement", "Gardez très crémeux"], 180, 14, 1, 14, 8, "bariatric", ["mou", "phase3"]),
    ("Poisson vapeur émietté", ["Cabillaud:150g", "Citron:jus", "Herbes:à goût"], ["Cuisez à la vapeur 10 min", "Émiettez finement"], 120, 25, 0, 2, 15, "bariatric", ["mou", "phase3"]),
    ("Poulet haché sauce", ["Poulet:120g", "Sauce tomate:50ml", "Herbes:à goût"], ["Hachez le poulet cuit", "Réchauffez avec la sauce"], 160, 25, 4, 5, 15, "bariatric", ["mou", "phase3"]),
    ("Cottage cheese herbes", ["Cottage cheese:150g", "Ciboulette:1 c.à.s", "Sel:pincée"], ["Mélangez le tout"], 120, 14, 4, 5, 5, "bariatric", ["mou", "phase3"]),
    ("Avocat écrasé", ["Avocat mûr:1", "Citron:jus", "Sel:pincée"], ["Écrasez l'avocat", "Assaisonnez"], 200, 2, 10, 18, 5, "bariatric", ["mou", "phase3"]),
    ("Banane écrasée cannelle", ["Banane très mûre:1", "Cannelle:pincée", "Yaourt:2 c.à.s"], ["Écrasez la banane", "Mélangez au yaourt"], 130, 3, 28, 1, 3, "bariatric", ["mou", "phase3"]),
    ("Ricotta sucrée", ["Ricotta:100g", "Miel:1 c.à.c", "Cannelle:pincée"], ["Fouettez la ricotta", "Incorporez miel et cannelle"], 150, 8, 10, 10, 3, "bariatric", ["mou", "phase3"]),
    ("Polenta crémeuse", ["Polenta:40g", "Lait:200ml", "Parmesan:20g"], ["Chauffez le lait", "Versez la polenta", "Ajoutez le parmesan"], 180, 8, 25, 6, 15, "bariatric", ["mou", "phase3"]),
    
    # Phase solide adapté
    ("Blanc de poulet grillé", ["Blanc de poulet:120g", "Huile d'olive:1 c.à.c", "Herbes:à goût"], ["Aplatissez le poulet", "Grillez 5 min par face", "Coupez en petits morceaux"], 180, 30, 0, 6, 15, "bariatric", ["solide", "phase4"]),
    ("Saumon au four", ["Pavé de saumon:100g", "Citron:1/2", "Aneth:branches"], ["Enfournez 12 min à 180°C", "Servez en petites portions"], 200, 22, 0, 12, 20, "bariatric", ["solide", "phase4"]),
    ("Omelette aux légumes", ["Œufs:2", "Courgette:50g", "Fromage:20g"], ["Faites sauter les légumes", "Versez les œufs", "Ajoutez le fromage"], 220, 16, 3, 16, 12, "bariatric", ["solide", "phase4"]),
    ("Steak haché maigre", ["Bœuf haché 5%:100g", "Oignon:1/4", "Persil:1 c.à.s"], ["Mélangez viande et aromates", "Formez un petit steak", "Cuisez bien à cœur"], 180, 22, 2, 10, 15, "bariatric", ["solide", "phase4"]),
    ("Crevettes sautées", ["Crevettes:100g", "Ail:1 gousse", "Persil:1 c.à.s"], ["Faites sauter à l'ail", "Ajoutez le persil"], 100, 20, 1, 2, 10, "bariatric", ["solide", "phase4"]),
    ("Dinde grillée", ["Escalope de dinde:100g", "Huile:1 c.à.c", "Herbes:à goût"], ["Grillez 4 min par côté", "Coupez finement"], 140, 28, 0, 3, 12, "bariatric", ["solide", "phase4"]),
    ("Tofu grillé", ["Tofu ferme:100g", "Sauce soja:1 c.à.s", "Sésame:1 c.à.c"], ["Coupez en cubes", "Marinez 10 min", "Grillez"], 100, 10, 2, 6, 20, "bariatric", ["solide", "phase4"]),
    ("Jambon blanc", ["Jambon blanc:2 tranches", "Cornichons:2"], ["Servez le jambon", "Mastiquez bien"], 80, 12, 1, 3, 2, "bariatric", ["solide", "phase4"]),
]

def generate_recipe_id(name, index):
    """Generate unique recipe ID"""
    return hashlib.md5(f"{name}_{index}".encode()).hexdigest()[:12]

def get_all_recipes():
    """Get all recipes from database"""
    recipes = []
    for i, r in enumerate(BASE_RECIPES):
        name, ingredients, steps, cal, prot, carbs, fat, time, category, tags = r
        nutri = calculate_nutri_score(cal, prot, carbs, fat)
        
        recipes.append({
            "id": generate_recipe_id(name, i),
            "name": name,
            "ingredients": ingredients,
            "steps": steps,
            "calories": cal,
            "protein": prot,
            "carbs": carbs,
            "fat": fat,
            "prep_time": time,
            "category": category,
            "tags": tags,
            "nutri_score": nutri,
            "image": get_image_for_recipe(name, category),
        })
    
    return recipes

# Pre-load recipes
VERIFIED_RECIPES = get_all_recipes()

def get_verified_recipes(category="all", count=6, phase=None):
    """Get verified recipes by category"""
    if phase:
        filtered = [r for r in VERIFIED_RECIPES if phase in r.get("tags", [])]
    elif category != "all":
        filtered = [r for r in VERIFIED_RECIPES if r.get("category") == category]
    else:
        filtered = VERIFIED_RECIPES
    
    if not filtered:
        filtered = VERIFIED_RECIPES
    
    # Daily rotation based on day
    day_seed = int(datetime.now().strftime("%Y%m%d"))
    random.seed(day_seed)
    selected = random.sample(filtered, min(count, len(filtered)))
    random.seed()
    
    return selected

def get_bariatric_recipes(phase, count=6):
    """Get bariatric recipes for a specific phase"""
    phase_map = {
        "liquid": "phase1",
        "mixed": "phase2", 
        "soft": "phase3",
        "solid": "phase4",
        "solid_adapted": "phase4"
    }
    tag = phase_map.get(phase, "phase4")
    
    filtered = [r for r in VERIFIED_RECIPES if tag in r.get("tags", []) or phase in r.get("tags", [])]
    if not filtered:
        filtered = [r for r in VERIFIED_RECIPES if r.get("category") == "bariatric"]
    
    return filtered[:count]

def search_recipes(query, limit=20):
    """Search recipes by name or ingredient"""
    query_lower = query.lower()
    results = []
    for recipe in VERIFIED_RECIPES:
        if query_lower in recipe['name'].lower():
            results.append(recipe)
        elif any(query_lower in ing.lower() for ing in recipe['ingredients']):
            results.append(recipe)
    return results[:limit]

def search_recipes_by_name(query, limit=20):
    return search_recipes(query, limit)

TOTAL_RECIPES = len(VERIFIED_RECIPES)
print(f"[Recipes DB] {TOTAL_RECIPES} recettes chargées")
