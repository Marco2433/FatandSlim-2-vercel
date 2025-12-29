# Fat and Slim - Product Requirements Document v2

## Overview
Application intelligente de coaching sportif et nutritionnel utilisant l'IA pour personnaliser l'expérience utilisateur.

## Tech Stack
- **Frontend**: React + Tailwind CSS + Shadcn/UI + Recharts
- **Backend**: FastAPI (Python)
- **Database**: MongoDB
- **AI**: OpenAI GPT-4o Vision (via Emergent LLM Key)
- **Auth**: JWT + Google OAuth (Emergent Auth)

## Core Features Implemented ✅

### 1. Authentication
- ✅ Email/password registration & login
- ✅ Google OAuth via Emergent Auth
- ✅ JWT session management
- ✅ Cookie-based auth with secure cookies

### 2. Onboarding Questionnaire (8 étapes)
- ✅ Étape 1: Genre (Homme/Femme)
- ✅ Étape 2: Mensurations (âge, taille, poids) avec calcul IMC temps réel
- ✅ Étape 3: Objectif + poids cible
- ✅ Étape 4: Niveau d'activité + niveau sportif
- ✅ Étape 5: Conditions de santé (diabète, apnée, thyroïde, bypass, sleeve, hypertension, cholestérol, etc.)
- ✅ Étape 6: Goûts alimentaires (J'aime / Je n'aime pas)
- ✅ Étape 7: Régimes alimentaires + Allergies
- ✅ Étape 8: Contraintes (temps cuisine, budget, niveau cuisine)

### 3. Calcul IMC Corrigé
- ✅ Formule: Poids (kg) / Taille (m)²
- ✅ Ex: 180cm, 75kg = 23.1 (correct)
- ✅ Calcul IMC idéal (22.0)
- ✅ Poids idéal calculé
- ✅ Plage de poids sain

### 4. Dashboard
- ✅ Résumé calories quotidien
- ✅ Suivi macros (protéines, glucides, lipides)
- ✅ Actions rapides (Scanner, Nutrition)
- ✅ Suivi objectif poids
- ✅ Défis quotidiens
- ✅ Statistiques hebdomadaires

### 5. Scanner IA (GPT-4o Vision)
- ✅ Interface caméra
- ✅ Upload d'images
- ✅ Reconnaissance d'aliments réelle
- ✅ Analyse nutritionnelle (calories, macros)
- ✅ Nutri-Score (A-E)
- ✅ Conseils santé personnalisés
- ✅ Avertissements selon conditions de santé (ex: diabète)

### 6. Suivi Nutrition
- ✅ Journal alimentaire quotidien
- ✅ Ajout manuel d'aliments
- ✅ Catégorisation par repas
- ✅ Suivi macros temps réel
- ✅ **NOUVEAU**: Agenda alimentaire par mois
- ✅ **NOUVEAU**: Notes sur les repas
- ✅ **NOUVEAU**: Recommandations IA alternatives plus saines
- ✅ Suppression d'entrées

### 7. Page Progrès avec Onglets
- ✅ **Onglet Poids**: Graphique évolution, objectif, poids idéal
- ✅ **Onglet IMC**: 
  - IMC actuel avec catégorie colorée
  - Échelle visuelle IMC (16-40)
  - IMC idéal et poids idéal
  - Graphique évolution IMC
  - Légende catégories IMC
- ✅ **Onglet Badges**: Badges gagnés et à débloquer

### 8. PWA Configuration
- ✅ manifest.json avec display: fullscreen
- ✅ Service Worker
- ✅ Icônes toutes tailles
- ✅ Meta tags PWA complets
- ✅ **Watermark "Made with Emergent" supprimé**

## API Endpoints

### Auth
- POST /api/auth/register
- POST /api/auth/login
- POST /api/auth/session
- GET /api/auth/me
- POST /api/auth/logout

### Profile
- GET /api/profile
- POST /api/profile/onboarding (avec données enrichies)
- PUT /api/profile

### Food & Nutrition
- POST /api/food/analyze (AI Vision GPT-4o)
- POST /api/food/log
- GET /api/food/logs
- GET /api/food/daily-summary
- GET /api/food/diary (agenda par mois)
- PUT /api/food/log/{entry_id}/note
- DELETE /api/food/log/{entry_id}
- POST /api/food/recommend-alternatives (recommandations IA)

### Progress
- POST /api/progress/weight
- GET /api/progress/weight
- GET /api/progress/bmi (nouveau)
- GET /api/progress/stats

## Données Profil Utilisateur (Mémorisées)

```json
{
  "gender": "male/female",
  "age": 30,
  "height": 180,
  "weight": 75,
  "target_weight": 70,
  "bmi": 23.1,
  "ideal_bmi": 22.0,
  "ideal_weight": 71.3,
  "goal": "lose_weight",
  "activity_level": "moderate",
  "fitness_level": "intermediate",
  "health_conditions": ["diabetes", "hypertension"],
  "food_likes": ["vegetables", "fish", "rice"],
  "food_dislikes": ["spicy", "sweet"],
  "dietary_preferences": ["halal"],
  "allergies": ["nuts"],
  "time_constraint": "moderate",
  "budget": "medium",
  "cooking_skill": "intermediate"
}
```

## PWABuilder Infos

| Champ | Valeur |
|-------|--------|
| App Name | Fat & Slim |
| Package ID | com.fatandslim.app |
| Display Mode | fullscreen |
| Theme Color | #F472B6 |
| Background | #000000 |

## Implementation Dates
- MVP Initial: December 29, 2024
- Iteration 2 (Améliorations): December 29, 2024

## Bugs Corrigés
- ✅ IMC incorrect (26 au lieu de 23.1 pour 180cm/75kg)
- ✅ Scanner IA ne fonctionnait pas (FileContent vs ImageContent)
- ✅ Watermark Emergent visible

## Next Steps (P1)
- [ ] Intégrer Google Billing API pour Premium
- [ ] Scanner code-barres produits
- [ ] Notifications push rappels
- [ ] Export données utilisateur
