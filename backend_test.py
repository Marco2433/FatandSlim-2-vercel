#!/usr/bin/env python3

import requests
import sys
import json
import base64
from datetime import datetime
import time

class FatSlimAPITester:
    def __init__(self, base_url="https://nutri-tracker-73.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.session = requests.Session()
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
        else:
            print(f"❌ {name} - {details}")
        
        self.test_results.append({
            "test": name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })

    def test_endpoint(self, method, endpoint, expected_status, data=None, files=None):
        """Test a single API endpoint"""
        url = f"{self.base_url}/{endpoint}"
        
        try:
            if method == 'GET':
                response = self.session.get(url)
            elif method == 'POST':
                if files:
                    response = self.session.post(url, data=data, files=files)
                else:
                    response = self.session.post(url, json=data)
            elif method == 'PUT':
                response = self.session.put(url, json=data)
            elif method == 'DELETE':
                response = self.session.delete(url)
            
            success = response.status_code == expected_status
            details = f"Status: {response.status_code}, Expected: {expected_status}"
            
            if success and response.headers.get('content-type', '').startswith('application/json'):
                try:
                    response_data = response.json()
                    return success, response_data, details
                except:
                    return success, {}, details
            
            return success, {}, details
            
        except Exception as e:
            return False, {}, f"Error: {str(e)}"

    def test_auth_flow(self):
        """Test authentication endpoints"""
        print("\n🔐 Testing Authentication Flow...")
        
        # Test user registration
        test_email = f"test.user.{int(time.time())}@example.com"
        test_password = "TestPass123!"
        test_name = "Test User"
        
        success, response, details = self.test_endpoint(
            'POST', 'auth/register', 200,
            data={
                "email": test_email,
                "password": test_password,
                "name": test_name
            }
        )
        self.log_test("User Registration", success, details)
        
        if success and 'user_id' in response:
            self.user_id = response['user_id']
            
            # Test login
            success, response, details = self.test_endpoint(
                'POST', 'auth/login', 200,
                data={
                    "email": test_email,
                    "password": test_password
                }
            )
            self.log_test("User Login", success, details)
            
            # Test get current user
            success, response, details = self.test_endpoint('GET', 'auth/me', 200)
            self.log_test("Get Current User", success, details)
            
            return True
        
        return False

    def test_profile_endpoints(self):
        """Test profile management endpoints"""
        print("\n👤 Testing Profile Endpoints...")
        
        # Test get profile
        success, response, details = self.test_endpoint('GET', 'profile', 200)
        self.log_test("Get Profile", success, details)
        
        # Test onboarding completion with CRITICAL calorie calculation test
        print("\n🔥 CRITICAL TEST: Calorie Calculation with Mifflin-St Jeor")
        onboarding_data = {
            "gender": "female",
            "age": 45,
            "height": 155,
            "weight": 148,
            "target_weight": 70,
            "goal": "lose_weight",
            "activity_level": "sedentary",
            "dietary_preferences": [],
            "allergies": [],
            "fitness_level": "beginner",
            "health_conditions": [],
            "food_likes": [],
            "food_dislikes": []
        }
        
        success, response, details = self.test_endpoint(
            'POST', 'profile/onboarding', 200,
            data=onboarding_data
        )
        
        # Verify calorie calculation results
        if success and 'profile' in response:
            profile = response['profile']
            calorie_debug = profile.get('calorie_debug', {})
            
            expected_bmr = 2063  # Approximately
            expected_tdee = 2475  # Approximately (BMR * 1.2)
            expected_target = 2104  # Approximately (15% deficit for BMI > 35)
            
            actual_bmr = calorie_debug.get('bmr', 0)
            actual_tdee = calorie_debug.get('tdee_maintenance', 0)
            actual_target = calorie_debug.get('final_target', 0)
            
            bmr_ok = abs(actual_bmr - expected_bmr) < 100  # Allow 100 kcal tolerance
            tdee_ok = abs(actual_tdee - expected_tdee) < 100
            target_ok = abs(actual_target - expected_target) < 100
            
            calorie_test_success = bmr_ok and tdee_ok and target_ok
            
            calorie_details = f"BMR: {actual_bmr} (expected ~{expected_bmr}), TDEE: {actual_tdee} (expected ~{expected_tdee}), Target: {actual_target} (expected ~{expected_target})"
            
            self.log_test("CRITICAL: Calorie Calculation Accuracy", calorie_test_success, calorie_details)
            
            # Verify debug info is present
            debug_fields_present = all(field in calorie_debug for field in ['bmr', 'activity_factor', 'tdee_maintenance', 'final_target'])
            self.log_test("Calorie Debug Info Present", debug_fields_present, f"Debug fields: {list(calorie_debug.keys())}")
        else:
            self.log_test("CRITICAL: Calorie Calculation Accuracy", False, "No profile data returned")
        
        self.log_test("Complete Onboarding", success, details)
        
        # Test profile update
        success, response, details = self.test_endpoint(
            'PUT', 'profile', 200,
            data={"age": 26}
        )
        self.log_test("Update Profile", success, details)

    def test_food_endpoints(self):
        """Test food and nutrition endpoints"""
        print("\n🍎 Testing Food & Nutrition Endpoints...")
        
        # Test food logging
        food_entry = {
            "food_name": "Test Apple",
            "calories": 95.0,
            "protein": 0.5,
            "carbs": 25.0,
            "fat": 0.3,
            "quantity": 1.0,
            "meal_type": "snack"
        }
        
        success, response, details = self.test_endpoint(
            'POST', 'food/log', 200,
            data=food_entry
        )
        self.log_test("Log Food Entry", success, details)
        
        # Test get food logs
        success, response, details = self.test_endpoint('GET', 'food/logs', 200)
        self.log_test("Get Food Logs", success, details)
        
        # Test daily summary
        success, response, details = self.test_endpoint('GET', 'food/daily-summary', 200)
        self.log_test("Get Daily Summary", success, details)
        
        # Test food analysis (mock image)
        # Create a simple test image (1x1 pixel PNG)
        test_image_data = base64.b64decode(
            'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChAGAWA0ddgAAAABJRU5ErkJggg=='
        )
        
        files = {'file': ('test.png', test_image_data, 'image/png')}
        
        try:
            response = self.session.post(f"{self.base_url}/food/analyze", files=files)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            self.log_test("Food Image Analysis", success, details)
        except Exception as e:
            self.log_test("Food Image Analysis", False, f"Error: {str(e)}")

    def test_meal_plans_endpoints(self):
        """Test meal planning endpoints"""
        print("\n🍽️ Testing Meal Plans Endpoints...")
        
        # Test generate daily meal plan
        success, response, details = self.test_endpoint(
            'POST', 'meals/generate', 200,
            data={"type": "daily"}
        )
        
        # Verify response contains meals
        if success and response:
            meal_plan = response.get('meal_plan', {})
            days = meal_plan.get('days', [])
            has_meals = False
            if days:
                first_day = days[0]
                meals = first_day.get('meals', {})
                has_meals = all(meal in meals for meal in ['breakfast', 'lunch', 'dinner'])
            
            self.log_test("Generate Daily Meal Plan - Structure", has_meals, f"Meals present: {list(meals.keys()) if 'meals' in locals() else 'None'}")
        
        self.log_test("Generate Daily Meal Plan", success, details)
        
        # Test generate weekly meal plan
        success, response, details = self.test_endpoint(
            'POST', 'meals/generate', 200,
            data={"type": "weekly"}
        )
        self.log_test("Generate Weekly Meal Plan", success, details)
        
        # Test get meal plans
        success, response, details = self.test_endpoint('GET', 'meals/plans', 200)
        self.log_test("Get Meal Plans", success, details)

    def test_agenda_notes_endpoints(self):
        """Test agenda notes endpoints"""
        print("\n📅 Testing Agenda Notes Endpoints...")
        
        # Test create agenda note
        note_data = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "content": "Test agenda note for nutrition planning",
            "type": "general"
        }
        
        success, response, details = self.test_endpoint(
            'POST', 'agenda/notes', 200,
            data=note_data
        )
        self.log_test("Create Agenda Note", success, details)
        
        note_id = None
        if success and 'note' in response:
            note_id = response['note'].get('note_id')
        
        # Test get agenda notes
        success, response, details = self.test_endpoint('GET', 'agenda/notes', 200)
        self.log_test("Get Agenda Notes", success, details)
        
        # Test delete agenda note
        if note_id:
            success, response, details = self.test_endpoint('DELETE', f'agenda/notes/{note_id}', 200)
            self.log_test("Delete Agenda Note", success, details)

    def test_recipes_endpoints(self):
        """Test AI recipe generation and favorites"""
        print("\n🍳 Testing Recipes Endpoints...")
        
        # Test generate recipes
        success, response, details = self.test_endpoint(
            'POST', 'recipes/generate', 200,
            data={"count": 5}
        )
        
        # Verify response structure
        if success and response:
            recipes = response.get('recipes', [])
            recipe_valid = False
            if recipes:
                first_recipe = recipes[0]
                required_fields = ['name', 'calories', 'ingredients', 'steps']
                recipe_valid = all(field in first_recipe for field in required_fields)
            
            self.log_test("Generate Recipes - Structure", recipe_valid, f"Recipe fields: {list(first_recipe.keys()) if recipes else 'No recipes'}")
        
        self.log_test("Generate AI Recipes", success, details)
        
        # Test add recipe to favorites
        if success and response and response.get('recipes'):
            test_recipe = response['recipes'][0]
            
            success, response, details = self.test_endpoint(
                'POST', 'recipes/favorites', 200,
                data={"recipe": test_recipe}
            )
            self.log_test("Add Recipe to Favorites", success, details)
            
            favorite_id = None
            if success and 'favorite_id' in response:
                favorite_id = response['favorite_id']
            
            # Test get favorite recipes
            success, response, details = self.test_endpoint('GET', 'recipes/favorites', 200)
            self.log_test("Get Favorite Recipes", success, details)
            
            # Test remove favorite recipe
            if favorite_id:
                success, response, details = self.test_endpoint('DELETE', f'recipes/favorites/{favorite_id}', 200)
                self.log_test("Remove Favorite Recipe", success, details)

    def test_profile_picture_endpoints(self):
        """Test profile picture upload and delete"""
        print("\n📸 Testing Profile Picture Endpoints...")
        
        # Create a test image (1x1 pixel PNG)
        test_image_data = base64.b64decode(
            'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChAGAWA0ddgAAAABJRU5ErkJggg=='
        )
        
        files = {'file': ('test_profile.png', test_image_data, 'image/png')}
        
        try:
            response = self.session.post(f"{self.base_url}/profile/picture", files=files)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            # Verify response contains picture data
            if success:
                try:
                    response_data = response.json()
                    has_picture = 'picture' in response_data and response_data['picture'].startswith('data:image')
                    self.log_test("Upload Profile Picture - Data", has_picture, "Picture data format check")
                except:
                    pass
            
            self.log_test("Upload Profile Picture", success, details)
            
            # Test delete profile picture
            if success:
                success, response, details = self.test_endpoint('DELETE', 'profile/picture', 200)
                self.log_test("Delete Profile Picture", success, details)
                
        except Exception as e:
            self.log_test("Upload Profile Picture", False, f"Error: {str(e)}")

    def test_add_meal_to_diary_endpoint(self):
        """Test adding AI meal to diary"""
        print("\n📝 Testing Add Meal to Diary Endpoint...")
        
        # Test meal data
        test_meal = {
            "name": "Salade de quinoa aux légumes",
            "calories": 350,
            "protein": 15,
            "carbs": 45,
            "fat": 12
        }
        
        meal_data = {
            "meal": test_meal,
            "meal_type": "lunch",
            "date": datetime.now().strftime("%Y-%m-%d")
        }
        
        success, response, details = self.test_endpoint(
            'POST', 'meals/add-to-diary', 200,
            data=meal_data
        )
        self.log_test("Add AI Meal to Diary", success, details)

    def test_workout_endpoints(self):
        """Test workout endpoints"""
        print("\n💪 Testing Workout Endpoints...")
        
        # Test generate workout
        success, response, details = self.test_endpoint('POST', 'workouts/generate', 200)
        self.log_test("Generate Workout Program", success, details)
        
        # Test get workout programs
        success, response, details = self.test_endpoint('GET', 'workouts/programs', 200)
        self.log_test("Get Workout Programs", success, details)
        
        # Test log workout
        workout_log = {
            "workout_name": "Test Cardio",
            "duration_minutes": 30,
            "calories_burned": 250,
            "exercises": []
        }
        
        success, response, details = self.test_endpoint(
            'POST', 'workouts/log', 200,
            data=workout_log
        )
        self.log_test("Log Workout", success, details)
        
        # Test get workout logs
        success, response, details = self.test_endpoint('GET', 'workouts/logs', 200)
        self.log_test("Get Workout Logs", success, details)

    def test_progress_endpoints(self):
        """Test progress tracking endpoints"""
        print("\n📊 Testing Progress Endpoints...")
        
        # Test log weight
        weight_entry = {
            "weight": 69.5,
            "date": datetime.now().strftime("%Y-%m-%d")
        }
        
        success, response, details = self.test_endpoint(
            'POST', 'progress/weight', 200,
            data=weight_entry
        )
        self.log_test("Log Weight Entry", success, details)
        
        # Test get weight history
        success, response, details = self.test_endpoint('GET', 'progress/weight', 200)
        self.log_test("Get Weight History", success, details)
        
        # Test get stats
        success, response, details = self.test_endpoint('GET', 'progress/stats', 200)
        self.log_test("Get Progress Stats", success, details)

    def test_gamification_endpoints(self):
        """Test badges and challenges endpoints"""
        print("\n🏆 Testing Gamification Endpoints...")
        
        # Test get badges
        success, response, details = self.test_endpoint('GET', 'badges', 200)
        self.log_test("Get Badges", success, details)
        
        # Test get challenges
        success, response, details = self.test_endpoint('GET', 'challenges', 200)
        self.log_test("Get Challenges", success, details)

    def run_all_tests(self):
        """Run all API tests"""
        print("🚀 Starting Fat & Slim API Tests...")
        print(f"Testing against: {self.base_url}")
        
        # Test authentication first
        if not self.test_auth_flow():
            print("❌ Authentication failed, stopping tests")
            return False
        
        # Test all other endpoints
        self.test_profile_endpoints()
        self.test_food_endpoints()
        self.test_meal_plans_endpoints()
        self.test_workout_endpoints()
        self.test_progress_endpoints()
        self.test_gamification_endpoints()
        
        # Test logout
        success, response, details = self.test_endpoint('POST', 'auth/logout', 200)
        self.log_test("User Logout", success, details)
        
        # Print summary
        print(f"\n📊 Test Summary:")
        print(f"Tests run: {self.tests_run}")
        print(f"Tests passed: {self.tests_passed}")
        print(f"Success rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        return self.tests_passed == self.tests_run

def main():
    tester = FatSlimAPITester()
    success = tester.run_all_tests()
    
    # Save test results
    with open('/app/test_reports/backend_test_results.json', 'w') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "total_tests": tester.tests_run,
            "passed_tests": tester.tests_passed,
            "success_rate": (tester.tests_passed/tester.tests_run)*100 if tester.tests_run > 0 else 0,
            "results": tester.test_results
        }, f, indent=2)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())