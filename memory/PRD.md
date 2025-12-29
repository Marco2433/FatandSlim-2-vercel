# Fat and Slim - Product Requirements Document

## Overview
Application intelligente de coaching sportif et nutritionnel utilisant l'IA pour personnaliser l'expérience utilisateur.

## Problem Statement
Créer une plateforme complète pour aider les utilisateurs à:
- Perdre du poids
- Mieux manger  
- Améliorer leur forme physique
- Suivre un programme adapté à leur mode de vie

## Tech Stack
- **Frontend**: React + Tailwind CSS + Shadcn/UI
- **Backend**: FastAPI (Python)
- **Database**: MongoDB
- **AI**: OpenAI GPT-5.2 (via Emergent LLM Key)
- **Auth**: JWT + Google OAuth (Emergent Auth)

## Core Features Implemented ✅

### 1. Authentication
- ✅ Email/password registration & login
- ✅ Google OAuth via Emergent Auth
- ✅ JWT session management
- ✅ Cookie-based auth with secure cookies

### 2. Onboarding Questionnaire
- ✅ 5-step intelligent questionnaire
- ✅ Collects: age, height, weight, target weight
- ✅ Goals: lose weight, gain muscle, maintain, improve health
- ✅ Activity level assessment
- ✅ Fitness level evaluation
- ✅ Dietary preferences & allergies
- ✅ Auto-calculates BMI, TDEE, daily targets

### 3. Dashboard
- ✅ Daily calories summary with progress bar
- ✅ Macro tracking (protein, carbs, fat)
- ✅ Quick actions (Scanner, Nutrition)
- ✅ Weight goal tracking
- ✅ Daily challenges
- ✅ Weekly statistics

### 4. AI Food Scanner
- ✅ Camera capture interface
- ✅ Image upload support
- ✅ AI vision analysis (GPT-5.2)
- ✅ Nutritional breakdown (calories, macros)
- ✅ Nutri-Score (A-E)
- ✅ Health tips & recommendations

### 5. Nutrition Tracking
- ✅ Daily food log
- ✅ Manual food entry
- ✅ Meal type categorization
- ✅ Real-time macro tracking
- ✅ Delete entries

### 6. AI Meal Plans
- ✅ AI-generated weekly meal plans
- ✅ Personalized to user profile
- ✅ Day-by-day breakdown
- ✅ Recipes included
- ✅ Shopping list generation
- ✅ Nutritional tips

### 7. AI Workout Programs
- ✅ Personalized workout generation
- ✅ Exercise library with instructions
- ✅ Sets, reps, rest times
- ✅ Warmup & cooldown
- ✅ Workout logging
- ✅ Equipment recommendations

### 8. Progress Tracking
- ✅ Weight history chart (Recharts)
- ✅ BMI tracking
- ✅ Streak tracking
- ✅ Weekly statistics
- ✅ Visual progress graphs

### 9. Gamification
- ✅ Badge system
- ✅ Daily challenges
- ✅ XP rewards
- ✅ Activity streaks

### 10. Profile & Settings
- ✅ User profile display
- ✅ Dark/Light theme toggle (auto-detection)
- ✅ Logout functionality
- ✅ Premium upsell banner

## User Personas
1. **Weight Loss Seeker**: Wants to track calories, scan food, follow meal plans
2. **Fitness Enthusiast**: Uses workout programs, tracks progress, earns badges
3. **Health Improver**: Follows AI recommendations, monitors nutrition quality

## API Endpoints

### Auth
- POST /api/auth/register
- POST /api/auth/login
- POST /api/auth/session (Google OAuth)
- GET /api/auth/me
- POST /api/auth/logout

### Profile
- GET /api/profile
- POST /api/profile/onboarding
- PUT /api/profile

### Food & Nutrition
- POST /api/food/analyze (AI vision)
- POST /api/food/log
- GET /api/food/logs
- GET /api/food/daily-summary
- DELETE /api/food/log/{entry_id}

### Meals
- POST /api/meals/generate (AI)
- GET /api/meals/plans

### Workouts
- POST /api/workouts/generate (AI)
- GET /api/workouts/programs
- POST /api/workouts/log
- GET /api/workouts/logs

### Progress
- POST /api/progress/weight
- GET /api/progress/weight
- GET /api/progress/stats

### Gamification
- GET /api/badges
- GET /api/challenges

## Prioritized Backlog

### P0 - Critical (Done)
- ✅ Core auth flow
- ✅ Onboarding
- ✅ Food tracking
- ✅ AI scanner

### P1 - High Priority (Future)
- [ ] Barcode scanner integration
- [ ] Push notifications
- [ ] Offline mode
- [ ] Data export

### P2 - Medium Priority (Future)
- [ ] Social features / Community
- [ ] Premium subscription (Google Billing)
- [ ] Weekly reports
- [ ] Coach chat AI

### P3 - Low Priority (Future)
- [ ] Multi-language support
- [ ] Apple Health / Google Fit sync
- [ ] Recipe sharing
- [ ] Meal photos gallery

## Implementation Date
- Initial MVP: December 29, 2024

## Next Steps
1. Integrate Google Billing API for Premium subscriptions
2. Add barcode scanner for packaged foods
3. Implement community features
4. Add push notifications for reminders
