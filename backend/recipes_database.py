"""
Base de données de recettes COHÉRENTES et vérifiées
Chaque recette a un nom, des ingrédients et des étapes qui correspondent parfaitement
"""

VERIFIED_RECIPES = [
    # ===== PETIT-DÉJEUNER =====
    {
        "id": "recipe_breakfast_1",
        "name": "Porridge aux fruits rouges",
        "category": "breakfast",
        "calories": 320,
        "protein": 10,
        "carbs": 52,
        "fat": 8,
        "prep_time": "5 min",
        "cook_time": "10 min",
        "servings": 1,
        "difficulty": "facile",
        "cost": "économique",
        "ingredients": [
            {"item": "Flocons d'avoine", "quantity": "50g"},
            {"item": "Lait", "quantity": "200ml"},
            {"item": "Fruits rouges (frais ou surgelés)", "quantity": "80g"},
            {"item": "Miel", "quantity": "1 cuillère à soupe"},
            {"item": "Cannelle", "quantity": "1 pincée"}
        ],
        "steps": [
            "Versez les flocons d'avoine et le lait dans une casserole.",
            "Faites chauffer à feu moyen en remuant pendant 5-7 minutes jusqu'à épaississement.",
            "Ajoutez la cannelle et mélangez.",
            "Versez dans un bol et disposez les fruits rouges sur le dessus.",
            "Arrosez de miel et servez chaud."
        ],
        "tips": "Préparez les flocons la veille au frigo pour un overnight oats rapide le matin.",
        "nutri_score": "A"
    },
    {
        "id": "recipe_breakfast_2",
        "name": "Œufs brouillés aux herbes",
        "category": "breakfast",
        "calories": 280,
        "protein": 18,
        "carbs": 4,
        "fat": 22,
        "prep_time": "5 min",
        "cook_time": "5 min",
        "servings": 1,
        "difficulty": "facile",
        "cost": "économique",
        "ingredients": [
            {"item": "Œufs", "quantity": "3"},
            {"item": "Beurre", "quantity": "10g"},
            {"item": "Ciboulette fraîche", "quantity": "1 cuillère à soupe"},
            {"item": "Sel", "quantity": "1 pincée"},
            {"item": "Poivre", "quantity": "1 pincée"}
        ],
        "steps": [
            "Cassez les œufs dans un bol et battez-les à la fourchette.",
            "Faites fondre le beurre dans une poêle à feu doux.",
            "Versez les œufs battus et remuez constamment avec une spatule.",
            "Retirez du feu quand les œufs sont encore légèrement baveux.",
            "Ajoutez la ciboulette ciselée, le sel et le poivre. Servez immédiatement."
        ],
        "tips": "La cuisson douce est la clé pour des œufs crémeux. Ne surchauffez jamais.",
        "nutri_score": "A"
    },
    {
        "id": "recipe_breakfast_3",
        "name": "Smoothie bowl banane-myrtilles",
        "category": "breakfast",
        "calories": 350,
        "protein": 12,
        "carbs": 58,
        "fat": 8,
        "prep_time": "10 min",
        "cook_time": "0 min",
        "servings": 1,
        "difficulty": "facile",
        "cost": "économique",
        "ingredients": [
            {"item": "Banane (congelée)", "quantity": "1 grande"},
            {"item": "Myrtilles", "quantity": "80g"},
            {"item": "Yaourt grec", "quantity": "100g"},
            {"item": "Lait d'amande", "quantity": "50ml"},
            {"item": "Granola", "quantity": "30g"},
            {"item": "Graines de chia", "quantity": "1 cuillère à soupe"}
        ],
        "steps": [
            "Mixez la banane congelée, les myrtilles, le yaourt grec et le lait d'amande jusqu'à obtenir une texture épaisse.",
            "Versez dans un bol.",
            "Disposez le granola et les graines de chia sur le dessus.",
            "Ajoutez quelques myrtilles fraîches pour la décoration.",
            "Dégustez immédiatement avec une cuillère."
        ],
        "tips": "Congelez vos bananes trop mûres pour les utiliser dans vos smoothies.",
        "nutri_score": "A"
    },
    {
        "id": "recipe_breakfast_4",
        "name": "Tartines avocat et œuf poché",
        "category": "breakfast",
        "calories": 380,
        "protein": 15,
        "carbs": 32,
        "fat": 22,
        "prep_time": "10 min",
        "cook_time": "5 min",
        "servings": 1,
        "difficulty": "intermédiaire",
        "cost": "moyen",
        "ingredients": [
            {"item": "Pain complet", "quantity": "2 tranches"},
            {"item": "Avocat mûr", "quantity": "1/2"},
            {"item": "Œuf frais", "quantity": "1"},
            {"item": "Jus de citron", "quantity": "1 cuillère à café"},
            {"item": "Piment d'Espelette", "quantity": "1 pincée"},
            {"item": "Sel et poivre", "quantity": "à votre goût"}
        ],
        "steps": [
            "Faites griller les tranches de pain.",
            "Écrasez l'avocat à la fourchette avec le jus de citron, le sel et le poivre.",
            "Faites bouillir de l'eau avec un filet de vinaigre. Créez un tourbillon et versez l'œuf délicatement. Pochez 3 minutes.",
            "Tartinez le pain grillé avec l'avocat écrasé.",
            "Déposez l'œuf poché sur les tartines et saupoudrez de piment d'Espelette."
        ],
        "tips": "Un œuf très frais donnera un meilleur résultat pour le pochage.",
        "nutri_score": "A"
    },
    {
        "id": "recipe_breakfast_5",
        "name": "Pancakes protéinés à la banane",
        "category": "breakfast",
        "calories": 420,
        "protein": 22,
        "carbs": 48,
        "fat": 14,
        "prep_time": "10 min",
        "cook_time": "10 min",
        "servings": 2,
        "difficulty": "facile",
        "cost": "économique",
        "ingredients": [
            {"item": "Banane mûre", "quantity": "1"},
            {"item": "Œufs", "quantity": "2"},
            {"item": "Flocons d'avoine", "quantity": "60g"},
            {"item": "Fromage blanc", "quantity": "50g"},
            {"item": "Levure chimique", "quantity": "1/2 cuillère à café"},
            {"item": "Sirop d'érable", "quantity": "pour servir"}
        ],
        "steps": [
            "Mixez la banane, les œufs, les flocons d'avoine, le fromage blanc et la levure jusqu'à obtenir une pâte lisse.",
            "Faites chauffer une poêle antiadhésive à feu moyen.",
            "Versez des petites louches de pâte et faites cuire 2 minutes de chaque côté.",
            "Les pancakes sont prêts quand des bulles se forment à la surface.",
            "Servez chaud avec un filet de sirop d'érable."
        ],
        "tips": "Plus la banane est mûre, plus vos pancakes seront naturellement sucrés.",
        "nutri_score": "A"
    },

    # ===== DÉJEUNER =====
    {
        "id": "recipe_lunch_1",
        "name": "Salade César au poulet grillé",
        "category": "lunch",
        "calories": 450,
        "protein": 35,
        "carbs": 18,
        "fat": 28,
        "prep_time": "15 min",
        "cook_time": "10 min",
        "servings": 2,
        "difficulty": "facile",
        "cost": "moyen",
        "ingredients": [
            {"item": "Filet de poulet", "quantity": "200g"},
            {"item": "Laitue romaine", "quantity": "1 petite"},
            {"item": "Parmesan râpé", "quantity": "40g"},
            {"item": "Croûtons", "quantity": "50g"},
            {"item": "Sauce César", "quantity": "4 cuillères à soupe"},
            {"item": "Huile d'olive", "quantity": "1 cuillère à soupe"}
        ],
        "steps": [
            "Assaisonnez le poulet avec sel et poivre, puis faites-le griller dans une poêle avec l'huile d'olive pendant 5-6 minutes de chaque côté.",
            "Lavez et essorez la laitue romaine, puis coupez-la en morceaux.",
            "Laissez reposer le poulet 5 minutes, puis coupez-le en tranches.",
            "Dans un saladier, mélangez la laitue avec la sauce César.",
            "Ajoutez les tranches de poulet, les croûtons et le parmesan. Servez immédiatement."
        ],
        "tips": "Faites vos propres croûtons en grillant des cubes de pain avec de l'ail et de l'huile d'olive.",
        "nutri_score": "B"
    },
    {
        "id": "recipe_lunch_2",
        "name": "Buddha bowl quinoa et légumes",
        "category": "lunch",
        "calories": 520,
        "protein": 18,
        "carbs": 62,
        "fat": 22,
        "prep_time": "15 min",
        "cook_time": "20 min",
        "servings": 2,
        "difficulty": "facile",
        "cost": "moyen",
        "ingredients": [
            {"item": "Quinoa", "quantity": "150g"},
            {"item": "Pois chiches (en conserve)", "quantity": "200g"},
            {"item": "Avocat", "quantity": "1"},
            {"item": "Concombre", "quantity": "1/2"},
            {"item": "Tomates cerises", "quantity": "10"},
            {"item": "Houmous", "quantity": "4 cuillères à soupe"},
            {"item": "Graines de sésame", "quantity": "1 cuillère à soupe"}
        ],
        "steps": [
            "Rincez le quinoa et faites-le cuire dans 300ml d'eau pendant 15 minutes.",
            "Égouttez et rincez les pois chiches.",
            "Coupez l'avocat en tranches, le concombre en rondelles et les tomates cerises en deux.",
            "Répartissez le quinoa dans deux bols.",
            "Disposez harmonieusement les légumes, les pois chiches et l'avocat autour du quinoa.",
            "Ajoutez une cuillère de houmous et saupoudrez de graines de sésame."
        ],
        "tips": "Faites rôtir les pois chiches au four avec des épices pour plus de croquant.",
        "nutri_score": "A"
    },
    {
        "id": "recipe_lunch_3",
        "name": "Wrap au thon et crudités",
        "category": "lunch",
        "calories": 380,
        "protein": 28,
        "carbs": 35,
        "fat": 14,
        "prep_time": "10 min",
        "cook_time": "0 min",
        "servings": 1,
        "difficulty": "facile",
        "cost": "économique",
        "ingredients": [
            {"item": "Tortilla de blé", "quantity": "1 grande"},
            {"item": "Thon en conserve (égoutté)", "quantity": "100g"},
            {"item": "Fromage frais", "quantity": "2 cuillères à soupe"},
            {"item": "Laitue", "quantity": "quelques feuilles"},
            {"item": "Tomate", "quantity": "1/2"},
            {"item": "Maïs", "quantity": "2 cuillères à soupe"}
        ],
        "steps": [
            "Étalez le fromage frais sur toute la surface de la tortilla.",
            "Émiettez le thon et répartissez-le au centre.",
            "Ajoutez les feuilles de laitue, la tomate coupée en dés et le maïs.",
            "Repliez les côtés de la tortilla vers le centre.",
            "Roulez fermement du bas vers le haut. Coupez en deux pour servir."
        ],
        "tips": "Faites chauffer légèrement la tortilla pour la rendre plus souple et facile à rouler.",
        "nutri_score": "A"
    },
    {
        "id": "recipe_lunch_4",
        "name": "Pâtes au pesto et tomates cerise",
        "category": "lunch",
        "calories": 480,
        "protein": 14,
        "carbs": 65,
        "fat": 18,
        "prep_time": "5 min",
        "cook_time": "12 min",
        "servings": 2,
        "difficulty": "facile",
        "cost": "économique",
        "ingredients": [
            {"item": "Pâtes (penne ou fusilli)", "quantity": "200g"},
            {"item": "Pesto vert", "quantity": "4 cuillères à soupe"},
            {"item": "Tomates cerises", "quantity": "150g"},
            {"item": "Parmesan râpé", "quantity": "30g"},
            {"item": "Pignons de pin", "quantity": "20g"},
            {"item": "Basilic frais", "quantity": "quelques feuilles"}
        ],
        "steps": [
            "Faites cuire les pâtes selon les instructions du paquet dans de l'eau salée.",
            "Coupez les tomates cerises en deux.",
            "Faites dorer les pignons de pin à sec dans une poêle.",
            "Égouttez les pâtes en réservant un peu d'eau de cuisson.",
            "Mélangez les pâtes chaudes avec le pesto et un peu d'eau de cuisson.",
            "Ajoutez les tomates cerises, le parmesan et les pignons. Décorez de basilic frais."
        ],
        "tips": "L'eau de cuisson des pâtes aide à lier la sauce grâce à son amidon.",
        "nutri_score": "B"
    },
    {
        "id": "recipe_lunch_5",
        "name": "Soupe de lentilles corail",
        "category": "lunch",
        "calories": 320,
        "protein": 18,
        "carbs": 45,
        "fat": 8,
        "prep_time": "10 min",
        "cook_time": "25 min",
        "servings": 4,
        "difficulty": "facile",
        "cost": "économique",
        "ingredients": [
            {"item": "Lentilles corail", "quantity": "200g"},
            {"item": "Oignon", "quantity": "1"},
            {"item": "Carottes", "quantity": "2"},
            {"item": "Lait de coco", "quantity": "200ml"},
            {"item": "Curry en poudre", "quantity": "1 cuillère à soupe"},
            {"item": "Bouillon de légumes", "quantity": "800ml"}
        ],
        "steps": [
            "Émincez l'oignon et coupez les carottes en rondelles.",
            "Faites revenir l'oignon dans un peu d'huile jusqu'à ce qu'il soit translucide.",
            "Ajoutez les carottes et le curry, faites revenir 2 minutes.",
            "Ajoutez les lentilles corail et le bouillon. Laissez mijoter 20 minutes.",
            "Ajoutez le lait de coco, mixez le tout et assaisonnez selon votre goût."
        ],
        "tips": "Les lentilles corail cuisent rapidement et n'ont pas besoin de trempage préalable.",
        "nutri_score": "A"
    },

    # ===== DÎNER =====
    {
        "id": "recipe_dinner_1",
        "name": "Saumon grillé aux légumes",
        "category": "dinner",
        "calories": 420,
        "protein": 32,
        "carbs": 22,
        "fat": 24,
        "prep_time": "15 min",
        "cook_time": "20 min",
        "servings": 2,
        "difficulty": "facile",
        "cost": "moyen",
        "ingredients": [
            {"item": "Pavés de saumon", "quantity": "2 (150g chacun)"},
            {"item": "Courgettes", "quantity": "2"},
            {"item": "Poivron rouge", "quantity": "1"},
            {"item": "Huile d'olive", "quantity": "2 cuillères à soupe"},
            {"item": "Citron", "quantity": "1"},
            {"item": "Herbes de Provence", "quantity": "1 cuillère à café"}
        ],
        "steps": [
            "Préchauffez le four à 200°C.",
            "Coupez les courgettes en rondelles et le poivron en lanières.",
            "Disposez les légumes sur une plaque, arrosez d'huile d'olive et d'herbes de Provence.",
            "Enfournez les légumes 10 minutes.",
            "Ajoutez les pavés de saumon assaisonnés sur les légumes, enfournez 10 minutes supplémentaires.",
            "Servez avec un quartier de citron."
        ],
        "tips": "Le saumon est cuit quand il se défait facilement à la fourchette.",
        "nutri_score": "A"
    },
    {
        "id": "recipe_dinner_2",
        "name": "Poulet rôti au citron et thym",
        "category": "dinner",
        "calories": 380,
        "protein": 42,
        "carbs": 8,
        "fat": 20,
        "prep_time": "10 min",
        "cook_time": "35 min",
        "servings": 2,
        "difficulty": "facile",
        "cost": "économique",
        "ingredients": [
            {"item": "Cuisses de poulet", "quantity": "4"},
            {"item": "Citron", "quantity": "1"},
            {"item": "Thym frais", "quantity": "4 branches"},
            {"item": "Ail", "quantity": "4 gousses"},
            {"item": "Huile d'olive", "quantity": "2 cuillères à soupe"},
            {"item": "Sel et poivre", "quantity": "à votre goût"}
        ],
        "steps": [
            "Préchauffez le four à 200°C.",
            "Disposez les cuisses de poulet dans un plat allant au four.",
            "Coupez le citron en quartiers et écrasez légèrement l'ail.",
            "Répartissez le citron, l'ail et le thym autour du poulet.",
            "Arrosez d'huile d'olive, assaisonnez de sel et poivre.",
            "Enfournez 35 minutes jusqu'à ce que la peau soit dorée et croustillante."
        ],
        "tips": "Arrosez le poulet avec son jus de cuisson à mi-cuisson pour plus de saveur.",
        "nutri_score": "A"
    },
    {
        "id": "recipe_dinner_3",
        "name": "Risotto aux champignons",
        "category": "dinner",
        "calories": 480,
        "protein": 12,
        "carbs": 65,
        "fat": 18,
        "prep_time": "10 min",
        "cook_time": "25 min",
        "servings": 2,
        "difficulty": "intermédiaire",
        "cost": "moyen",
        "ingredients": [
            {"item": "Riz arborio", "quantity": "200g"},
            {"item": "Champignons de Paris", "quantity": "200g"},
            {"item": "Oignon", "quantity": "1"},
            {"item": "Bouillon de légumes", "quantity": "800ml"},
            {"item": "Parmesan râpé", "quantity": "50g"},
            {"item": "Vin blanc", "quantity": "100ml"},
            {"item": "Beurre", "quantity": "30g"}
        ],
        "steps": [
            "Maintenez le bouillon chaud dans une casserole.",
            "Faites revenir l'oignon émincé dans le beurre. Ajoutez les champignons tranchés.",
            "Ajoutez le riz et faites-le nacrer 2 minutes en remuant.",
            "Versez le vin blanc et laissez évaporer.",
            "Ajoutez le bouillon louche par louche en remuant, attendant que chaque louche soit absorbée.",
            "Terminez avec le parmesan et un peu de beurre. Servez crémeux."
        ],
        "tips": "Ne lavez jamais le riz à risotto, son amidon crée l'onctuosité.",
        "nutri_score": "B"
    },
    {
        "id": "recipe_dinner_4",
        "name": "Wok de légumes au tofu",
        "category": "dinner",
        "calories": 350,
        "protein": 18,
        "carbs": 32,
        "fat": 16,
        "prep_time": "15 min",
        "cook_time": "10 min",
        "servings": 2,
        "difficulty": "facile",
        "cost": "économique",
        "ingredients": [
            {"item": "Tofu ferme", "quantity": "200g"},
            {"item": "Brocoli", "quantity": "150g"},
            {"item": "Poivron", "quantity": "1"},
            {"item": "Carottes", "quantity": "2"},
            {"item": "Sauce soja", "quantity": "3 cuillères à soupe"},
            {"item": "Huile de sésame", "quantity": "1 cuillère à soupe"},
            {"item": "Gingembre frais", "quantity": "1 cm"}
        ],
        "steps": [
            "Coupez le tofu en cubes et faites-le dorer dans l'huile de sésame.",
            "Réservez le tofu et ajoutez le gingembre râpé.",
            "Ajoutez les carottes en julienne et le brocoli en fleurettes. Faites sauter 3-4 minutes.",
            "Ajoutez le poivron en lanières et poursuivez la cuisson 2 minutes.",
            "Remettez le tofu, versez la sauce soja et mélangez bien.",
            "Servez chaud, éventuellement sur du riz."
        ],
        "tips": "Pressez le tofu entre deux torchons pour enlever l'excès d'eau avant cuisson.",
        "nutri_score": "A"
    },
    {
        "id": "recipe_dinner_5",
        "name": "Gratin de courgettes",
        "category": "dinner",
        "calories": 320,
        "protein": 18,
        "carbs": 15,
        "fat": 22,
        "prep_time": "15 min",
        "cook_time": "30 min",
        "servings": 4,
        "difficulty": "facile",
        "cost": "économique",
        "ingredients": [
            {"item": "Courgettes", "quantity": "4"},
            {"item": "Crème fraîche", "quantity": "200ml"},
            {"item": "Gruyère râpé", "quantity": "100g"},
            {"item": "Œufs", "quantity": "2"},
            {"item": "Ail", "quantity": "2 gousses"},
            {"item": "Sel, poivre, muscade", "quantity": "à votre goût"}
        ],
        "steps": [
            "Préchauffez le four à 180°C.",
            "Coupez les courgettes en rondelles et faites-les revenir avec l'ail émincé.",
            "Dans un bol, mélangez la crème, les œufs, la moitié du gruyère et les épices.",
            "Disposez les courgettes dans un plat à gratin.",
            "Versez le mélange crémeux et parsemez du reste de gruyère.",
            "Enfournez 30 minutes jusqu'à ce que le dessus soit doré."
        ],
        "tips": "Faites dégorger les courgettes au sel pour éviter un gratin trop liquide.",
        "nutri_score": "B"
    },

    # ===== COLLATIONS =====
    {
        "id": "recipe_snack_1",
        "name": "Energy balls aux dattes",
        "category": "snack",
        "calories": 120,
        "protein": 4,
        "carbs": 18,
        "fat": 5,
        "prep_time": "15 min",
        "cook_time": "0 min",
        "servings": 10,
        "difficulty": "facile",
        "cost": "économique",
        "ingredients": [
            {"item": "Dattes dénoyautées", "quantity": "150g"},
            {"item": "Amandes", "quantity": "80g"},
            {"item": "Cacao en poudre", "quantity": "2 cuillères à soupe"},
            {"item": "Noix de coco râpée", "quantity": "30g"},
            {"item": "Extrait de vanille", "quantity": "1 cuillère à café"}
        ],
        "steps": [
            "Mixez les amandes jusqu'à obtenir une poudre grossière.",
            "Ajoutez les dattes et mixez jusqu'à ce que le mélange s'agglomère.",
            "Incorporez le cacao et la vanille, mixez encore.",
            "Formez des boules avec vos mains (environ 10 boules).",
            "Roulez-les dans la noix de coco râpée.",
            "Réfrigérez au moins 30 minutes avant de déguster."
        ],
        "tips": "Ces energy balls se conservent 2 semaines au réfrigérateur.",
        "nutri_score": "A"
    },
    {
        "id": "recipe_snack_2",
        "name": "Yaourt grec aux fruits et granola",
        "category": "snack",
        "calories": 220,
        "protein": 12,
        "carbs": 28,
        "fat": 7,
        "prep_time": "5 min",
        "cook_time": "0 min",
        "servings": 1,
        "difficulty": "facile",
        "cost": "économique",
        "ingredients": [
            {"item": "Yaourt grec nature", "quantity": "150g"},
            {"item": "Fruits frais de saison", "quantity": "80g"},
            {"item": "Granola", "quantity": "30g"},
            {"item": "Miel", "quantity": "1 cuillère à café"}
        ],
        "steps": [
            "Versez le yaourt grec dans un bol.",
            "Coupez les fruits en morceaux de taille appropriée.",
            "Disposez les fruits sur le yaourt.",
            "Ajoutez le granola pour le croquant.",
            "Terminez par un filet de miel."
        ],
        "tips": "Préparez votre propre granola maison pour contrôler le sucre ajouté.",
        "nutri_score": "A"
    },
    {
        "id": "recipe_snack_3",
        "name": "Houmous maison",
        "category": "snack",
        "calories": 180,
        "protein": 8,
        "carbs": 18,
        "fat": 10,
        "prep_time": "10 min",
        "cook_time": "0 min",
        "servings": 4,
        "difficulty": "facile",
        "cost": "économique",
        "ingredients": [
            {"item": "Pois chiches (en conserve)", "quantity": "400g"},
            {"item": "Tahini (purée de sésame)", "quantity": "3 cuillères à soupe"},
            {"item": "Jus de citron", "quantity": "2 cuillères à soupe"},
            {"item": "Ail", "quantity": "1 gousse"},
            {"item": "Huile d'olive", "quantity": "2 cuillères à soupe"},
            {"item": "Cumin", "quantity": "1 cuillère à café"}
        ],
        "steps": [
            "Égouttez et rincez les pois chiches, gardez un peu d'eau de la conserve.",
            "Mixez les pois chiches avec le tahini, le jus de citron et l'ail.",
            "Ajoutez l'huile d'olive et le cumin, mixez jusqu'à obtenir une texture lisse.",
            "Si trop épais, ajoutez un peu d'eau de la conserve.",
            "Servez avec un filet d'huile d'olive et du paprika."
        ],
        "tips": "Le secret d'un houmous crémeux : mixez longtemps et ajoutez de l'eau de cuisson glacée.",
        "nutri_score": "A"
    },
    {
        "id": "recipe_snack_4",
        "name": "Compote de pommes maison",
        "category": "snack",
        "calories": 90,
        "protein": 0,
        "carbs": 22,
        "fat": 0,
        "prep_time": "10 min",
        "cook_time": "20 min",
        "servings": 4,
        "difficulty": "facile",
        "cost": "économique",
        "ingredients": [
            {"item": "Pommes", "quantity": "4 (environ 600g)"},
            {"item": "Eau", "quantity": "50ml"},
            {"item": "Cannelle", "quantity": "1 cuillère à café"},
            {"item": "Vanille (optionnel)", "quantity": "1/2 gousse"}
        ],
        "steps": [
            "Épluchez et coupez les pommes en morceaux.",
            "Placez-les dans une casserole avec l'eau et la cannelle.",
            "Faites cuire à feu doux 15-20 minutes en remuant.",
            "Écrasez à la fourchette ou mixez selon la texture souhaitée.",
            "Laissez refroidir et conservez au réfrigérateur."
        ],
        "tips": "Mélangez différentes variétés de pommes pour un goût plus complexe.",
        "nutri_score": "A"
    },
    {
        "id": "recipe_snack_5",
        "name": "Toast à l'avocat",
        "category": "snack",
        "calories": 250,
        "protein": 6,
        "carbs": 22,
        "fat": 16,
        "prep_time": "5 min",
        "cook_time": "2 min",
        "servings": 1,
        "difficulty": "facile",
        "cost": "moyen",
        "ingredients": [
            {"item": "Pain complet", "quantity": "1 tranche"},
            {"item": "Avocat mûr", "quantity": "1/2"},
            {"item": "Jus de citron", "quantity": "quelques gouttes"},
            {"item": "Graines de sésame", "quantity": "1 pincée"},
            {"item": "Sel et poivre", "quantity": "à votre goût"}
        ],
        "steps": [
            "Faites griller le pain.",
            "Coupez l'avocat en deux, retirez le noyau.",
            "Écrasez la chair à la fourchette avec le jus de citron.",
            "Étalez l'avocat écrasé sur le toast.",
            "Assaisonnez de sel, poivre et graines de sésame."
        ],
        "tips": "Ajoutez des flocons de piment pour une version épicée.",
        "nutri_score": "A"
    },

    # ===== RECETTES SUPPLÉMENTAIRES =====
    {
        "id": "recipe_lunch_6",
        "name": "Taboulé libanais traditionnel",
        "category": "lunch",
        "calories": 280,
        "protein": 6,
        "carbs": 38,
        "fat": 12,
        "prep_time": "20 min",
        "cook_time": "0 min",
        "servings": 4,
        "difficulty": "facile",
        "cost": "économique",
        "ingredients": [
            {"item": "Boulgour fin", "quantity": "100g"},
            {"item": "Persil frais", "quantity": "2 gros bouquets"},
            {"item": "Menthe fraîche", "quantity": "1 bouquet"},
            {"item": "Tomates", "quantity": "3"},
            {"item": "Oignon", "quantity": "1 petit"},
            {"item": "Jus de citron", "quantity": "4 cuillères à soupe"},
            {"item": "Huile d'olive", "quantity": "4 cuillères à soupe"}
        ],
        "steps": [
            "Faites tremper le boulgour 15 minutes dans de l'eau tiède, puis égouttez bien.",
            "Hachez finement le persil et la menthe.",
            "Coupez les tomates en petits dés et émincez l'oignon.",
            "Mélangez tous les ingrédients dans un saladier.",
            "Assaisonnez avec le jus de citron, l'huile d'olive, sel et poivre.",
            "Réfrigérez 30 minutes avant de servir."
        ],
        "tips": "Dans le vrai taboulé libanais, le persil est l'ingrédient principal, pas le boulgour.",
        "nutri_score": "A"
    },
    {
        "id": "recipe_dinner_6",
        "name": "Omelette aux légumes",
        "category": "dinner",
        "calories": 320,
        "protein": 22,
        "carbs": 8,
        "fat": 24,
        "prep_time": "10 min",
        "cook_time": "10 min",
        "servings": 2,
        "difficulty": "facile",
        "cost": "économique",
        "ingredients": [
            {"item": "Œufs", "quantity": "4"},
            {"item": "Poivron", "quantity": "1/2"},
            {"item": "Tomate", "quantity": "1"},
            {"item": "Oignon", "quantity": "1/2"},
            {"item": "Fromage râpé", "quantity": "30g"},
            {"item": "Beurre", "quantity": "15g"},
            {"item": "Sel, poivre, fines herbes", "quantity": "à votre goût"}
        ],
        "steps": [
            "Coupez le poivron, la tomate et l'oignon en petits dés.",
            "Faites revenir les légumes dans une poêle avec un peu de beurre.",
            "Battez les œufs avec le sel, le poivre et les fines herbes.",
            "Ajoutez le reste du beurre dans la poêle et versez les œufs battus.",
            "Quand l'omelette commence à prendre, ajoutez le fromage.",
            "Pliez l'omelette en deux et servez immédiatement."
        ],
        "tips": "Pour une omelette moelleuse, ne la cuisez pas trop longtemps.",
        "nutri_score": "A"
    },
    {
        "id": "recipe_lunch_7",
        "name": "Bol de riz au saumon teriyaki",
        "category": "lunch",
        "calories": 520,
        "protein": 28,
        "carbs": 58,
        "fat": 18,
        "prep_time": "10 min",
        "cook_time": "20 min",
        "servings": 2,
        "difficulty": "intermédiaire",
        "cost": "moyen",
        "ingredients": [
            {"item": "Riz à sushi", "quantity": "200g"},
            {"item": "Pavé de saumon", "quantity": "200g"},
            {"item": "Sauce teriyaki", "quantity": "4 cuillères à soupe"},
            {"item": "Avocat", "quantity": "1"},
            {"item": "Concombre", "quantity": "1/2"},
            {"item": "Graines de sésame", "quantity": "1 cuillère à soupe"},
            {"item": "Algue nori", "quantity": "1 feuille"}
        ],
        "steps": [
            "Faites cuire le riz selon les instructions du paquet.",
            "Coupez le saumon en cubes et faites-le mariner dans 2 cuillères de sauce teriyaki.",
            "Faites griller le saumon à la poêle 2-3 minutes de chaque côté.",
            "Coupez l'avocat en tranches et le concombre en rondelles.",
            "Répartissez le riz dans des bols, ajoutez le saumon, l'avocat et le concombre.",
            "Arrosez du reste de sauce teriyaki, parsemez de sésame et de nori émietté."
        ],
        "tips": "Utilisez du saumon très frais si vous préférez le manger cru style poké bowl.",
        "nutri_score": "A"
    },
    {
        "id": "recipe_dinner_7",
        "name": "Curry de légumes",
        "category": "dinner",
        "calories": 380,
        "protein": 10,
        "carbs": 42,
        "fat": 20,
        "prep_time": "15 min",
        "cook_time": "25 min",
        "servings": 4,
        "difficulty": "facile",
        "cost": "économique",
        "ingredients": [
            {"item": "Pommes de terre", "quantity": "300g"},
            {"item": "Pois chiches", "quantity": "200g"},
            {"item": "Tomates concassées", "quantity": "400g"},
            {"item": "Lait de coco", "quantity": "200ml"},
            {"item": "Pâte de curry", "quantity": "2 cuillères à soupe"},
            {"item": "Épinards frais", "quantity": "100g"},
            {"item": "Oignon", "quantity": "1"}
        ],
        "steps": [
            "Coupez les pommes de terre en cubes et faites-les précuire 10 minutes à l'eau.",
            "Faites revenir l'oignon émincé, puis ajoutez la pâte de curry.",
            "Ajoutez les tomates concassées et le lait de coco.",
            "Incorporez les pommes de terre égouttées et les pois chiches.",
            "Laissez mijoter 15 minutes.",
            "Ajoutez les épinards en fin de cuisson et servez avec du riz."
        ],
        "tips": "Ajoutez du gingembre frais râpé pour plus de saveur.",
        "nutri_score": "A"
    },
    {
        "id": "recipe_breakfast_6",
        "name": "Pain perdu à la cannelle",
        "category": "breakfast",
        "calories": 380,
        "protein": 12,
        "carbs": 48,
        "fat": 16,
        "prep_time": "10 min",
        "cook_time": "10 min",
        "servings": 2,
        "difficulty": "facile",
        "cost": "économique",
        "ingredients": [
            {"item": "Pain de mie (rassis de préférence)", "quantity": "4 tranches"},
            {"item": "Œufs", "quantity": "2"},
            {"item": "Lait", "quantity": "100ml"},
            {"item": "Cannelle", "quantity": "1 cuillère à café"},
            {"item": "Sucre", "quantity": "2 cuillères à soupe"},
            {"item": "Beurre", "quantity": "20g"}
        ],
        "steps": [
            "Battez les œufs avec le lait, la cannelle et 1 cuillère de sucre.",
            "Trempez chaque tranche de pain dans le mélange des deux côtés.",
            "Faites fondre le beurre dans une poêle à feu moyen.",
            "Faites dorer chaque tranche 2-3 minutes de chaque côté.",
            "Saupoudrez du reste de sucre et servez chaud."
        ],
        "tips": "Le pain rassis absorbe mieux le mélange sans se défaire.",
        "nutri_score": "B"
    }
]

def get_verified_recipes(category: str = "all", count: int = 6) -> list:
    """Retourne des recettes vérifiées et cohérentes"""
    import random
    from datetime import datetime
    
    if category == "all":
        recipes = VERIFIED_RECIPES.copy()
    else:
        recipes = [r for r in VERIFIED_RECIPES if r["category"] == category]
    
    # Mélanger avec une seed basée sur le jour pour varier chaque jour
    day_seed = datetime.now().timetuple().tm_yday
    random.seed(day_seed)
    random.shuffle(recipes)
    
    return recipes[:count]

def search_recipes_by_name(query: str) -> list:
    """Recherche de recettes par nom"""
    query_lower = query.lower()
    return [r for r in VERIFIED_RECIPES if query_lower in r["name"].lower()]
