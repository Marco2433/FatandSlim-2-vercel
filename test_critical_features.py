#!/usr/bin/env python3

import requests
import json
import base64
from datetime import datetime
import time

class CriticalFeatureTester:
    def __init__(self):
        self.base_url = "https://sportcoach-2.preview.emergentagent.com/api"
        self.session = requests.Session()
        self.user_id = None
        self.token = None
        self.test_results = []

    def log_result(self, test_name, success, details="", data=None):
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}")
        if details:
            print(f"    Details: {details}")
        if not success and data:
            print(f"    Response: {json.dumps(data, indent=2)[:200]}...")

    def setup_test_user(self):
        """Create and authenticate test user"""
        print("\n🔐 Setting up test user...")
        
        test_email = f"test.user.{int(time.time())}@example.com"
        test_password = "TestPass123!"
        
        # Register user
        try:
            response = self.session.post(f"{self.base_url}/auth/register", json={
                "email": test_email,
                "password": test_password,
                "name": "Test User"
            })
            
            if response.status_code == 200:
                data = response.json()
                self.user_id = data.get('user_id')
                self.token = data.get('token')
                
                # Set authorization header
                self.session.headers.update({'Authorization': f'Bearer {self.token}'})
                
                self.log_result("User Registration & Auth", True, f"User ID: {self.user_id}")
                return True
            else:
                self.log_result("User Registration & Auth", False, f"Status: {response.status_code}", response.json())
                return False
                
        except Exception as e:
            self.log_result("User Registration & Auth", False, f"Error: {str(e)}")
            return False

    def test_calorie_calculation(self):
        """CRITICAL TEST: Test calorie calculation with Mifflin-St Jeor algorithm"""
        print("\n🔥 CRITICAL TEST: Calorie Calculation")
        
        # Test profile from review request
        profile_data = {
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
        
        try:
            response = self.session.post(f"{self.base_url}/profile/onboarding", json=profile_data)
            
            if response.status_code == 200:
                data = response.json()
                profile = data.get('profile', {})
                calorie_debug = profile.get('calorie_debug', {})
                
                # Expected values from review request
                expected_bmr = 2063
                expected_tdee = 2475
                expected_target = 2104
                
                actual_bmr = calorie_debug.get('bmr', 0)
                actual_tdee = calorie_debug.get('tdee_maintenance', 0)
                actual_target = calorie_debug.get('final_target', 0)
                
                # Check if values are within acceptable range (±5%)
                bmr_ok = abs(actual_bmr - expected_bmr) / expected_bmr < 0.05
                tdee_ok = abs(actual_tdee - expected_tdee) / expected_tdee < 0.05
                target_ok = abs(actual_target - expected_target) / expected_target < 0.05
                
                all_ok = bmr_ok and tdee_ok and target_ok
                
                details = f"BMR: {actual_bmr} (expected ~{expected_bmr}), TDEE: {actual_tdee} (expected ~{expected_tdee}), Target: {actual_target} (expected ~{expected_target})"
                
                self.log_result("Calorie Calculation Accuracy", all_ok, details, calorie_debug)
                
                # Check debug fields presence
                required_fields = ['bmr', 'activity_factor', 'tdee_maintenance', 'final_target']
                debug_complete = all(field in calorie_debug for field in required_fields)
                
                self.log_result("Calorie Debug Fields", debug_complete, f"Fields: {list(calorie_debug.keys())}")
                
                return all_ok and debug_complete
            else:
                self.log_result("Calorie Calculation", False, f"Status: {response.status_code}", response.json())
                return False
                
        except Exception as e:
            self.log_result("Calorie Calculation", False, f"Error: {str(e)}")
            return False

    def test_agenda_notes(self):
        """Test agenda notes API"""
        print("\n📅 Testing Agenda Notes...")
        
        note_data = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "content": "Test nutrition planning note",
            "type": "general"
        }
        
        try:
            # Create note
            response = self.session.post(f"{self.base_url}/agenda/notes", json=note_data)
            create_success = response.status_code == 200
            
            note_id = None
            if create_success:
                data = response.json()
                note_id = data.get('note', {}).get('note_id')
            
            self.log_result("Create Agenda Note", create_success, f"Note ID: {note_id}")
            
            # Get notes
            response = self.session.get(f"{self.base_url}/agenda/notes")
            get_success = response.status_code == 200
            self.log_result("Get Agenda Notes", get_success)
            
            # Delete note
            if note_id:
                response = self.session.delete(f"{self.base_url}/agenda/notes/{note_id}")
                delete_success = response.status_code == 200
                self.log_result("Delete Agenda Note", delete_success)
                return create_success and get_success and delete_success
            
            return create_success and get_success
            
        except Exception as e:
            self.log_result("Agenda Notes", False, f"Error: {str(e)}")
            return False

    def test_meal_generation(self):
        """Test AI meal generation"""
        print("\n🍽️ Testing AI Meal Generation...")
        
        try:
            # Test daily meal plan
            response = self.session.post(f"{self.base_url}/meals/generate", json={"type": "daily"})
            daily_success = response.status_code == 200
            
            daily_data = None
            if daily_success:
                daily_data = response.json()
                meal_plan = daily_data.get('meal_plan', {})
                days = meal_plan.get('days', [])
                
                # Check structure
                has_structure = False
                if days:
                    first_day = days[0]
                    meals = first_day.get('meals', {})
                    has_structure = all(meal in meals for meal in ['breakfast', 'lunch', 'dinner'])
                
                self.log_result("Daily Meal Plan Structure", has_structure, f"Meals: {list(meals.keys()) if days else 'None'}")
            
            self.log_result("Generate Daily Meal Plan", daily_success)
            
            # Test weekly meal plan
            response = self.session.post(f"{self.base_url}/meals/generate", json={"type": "weekly"})
            weekly_success = response.status_code == 200
            self.log_result("Generate Weekly Meal Plan", weekly_success)
            
            return daily_success and weekly_success
            
        except Exception as e:
            self.log_result("Meal Generation", False, f"Error: {str(e)}")
            return False

    def test_recipe_generation(self):
        """Test AI recipe generation and favorites"""
        print("\n🍳 Testing AI Recipe Generation...")
        
        try:
            # Generate recipes
            response = self.session.post(f"{self.base_url}/recipes/generate", json={"count": 5})
            generate_success = response.status_code == 200
            
            recipes_data = None
            if generate_success:
                recipes_data = response.json()
                recipes = recipes_data.get('recipes', [])
                
                # Check structure
                recipe_valid = False
                if recipes:
                    first_recipe = recipes[0]
                    required_fields = ['name', 'calories', 'ingredients', 'steps']
                    recipe_valid = all(field in first_recipe for field in required_fields)
                
                self.log_result("Recipe Structure Valid", recipe_valid, f"Fields: {list(first_recipe.keys()) if recipes else 'None'}")
            
            self.log_result("Generate Recipes", generate_success)
            
            # Test favorites if recipes generated
            if generate_success and recipes_data and recipes_data.get('recipes'):
                test_recipe = recipes_data['recipes'][0]
                
                # Add to favorites
                response = self.session.post(f"{self.base_url}/recipes/favorites", json={"recipe": test_recipe})
                add_fav_success = response.status_code == 200
                
                favorite_id = None
                if add_fav_success:
                    fav_data = response.json()
                    favorite_id = fav_data.get('favorite_id')
                
                self.log_result("Add Recipe to Favorites", add_fav_success, f"Favorite ID: {favorite_id}")
                
                # Get favorites
                response = self.session.get(f"{self.base_url}/recipes/favorites")
                get_fav_success = response.status_code == 200
                self.log_result("Get Favorite Recipes", get_fav_success)
                
                # Remove favorite
                if favorite_id:
                    response = self.session.delete(f"{self.base_url}/recipes/favorites/{favorite_id}")
                    remove_fav_success = response.status_code == 200
                    self.log_result("Remove Favorite Recipe", remove_fav_success)
                
                return generate_success and add_fav_success and get_fav_success
            
            return generate_success
            
        except Exception as e:
            self.log_result("Recipe Generation", False, f"Error: {str(e)}")
            return False

    def test_profile_picture(self):
        """Test profile picture upload/delete"""
        print("\n📸 Testing Profile Picture...")
        
        try:
            # Create test image
            test_image_data = base64.b64decode(
                'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChAGAWA0ddgAAAABJRU5ErkJggg=='
            )
            
            files = {'file': ('test.png', test_image_data, 'image/png')}
            
            # Upload picture
            response = self.session.post(f"{self.base_url}/profile/picture", files=files)
            upload_success = response.status_code == 200
            
            has_picture_data = False
            if upload_success:
                data = response.json()
                picture = data.get('picture', '')
                has_picture_data = picture.startswith('data:image')
            
            self.log_result("Upload Profile Picture", upload_success)
            self.log_result("Picture Data Format", has_picture_data)
            
            # Delete picture
            if upload_success:
                response = self.session.delete(f"{self.base_url}/profile/picture")
                delete_success = response.status_code == 200
                self.log_result("Delete Profile Picture", delete_success)
                return upload_success and delete_success
            
            return upload_success
            
        except Exception as e:
            self.log_result("Profile Picture", False, f"Error: {str(e)}")
            return False

    def test_add_meal_to_diary(self):
        """Test adding AI meal to diary"""
        print("\n📝 Testing Add Meal to Diary...")
        
        try:
            test_meal = {
                "name": "Salade quinoa aux légumes",
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
            
            response = self.session.post(f"{self.base_url}/meals/add-to-diary", json=meal_data)
            success = response.status_code == 200
            
            entry_id = None
            if success:
                data = response.json()
                entry_id = data.get('entry_id')
            
            self.log_result("Add Meal to Diary", success, f"Entry ID: {entry_id}")
            return success
            
        except Exception as e:
            self.log_result("Add Meal to Diary", False, f"Error: {str(e)}")
            return False

    def run_critical_tests(self):
        """Run all critical tests"""
        print("🚀 Starting Critical Feature Tests for Fat & Slim App")
        print(f"Testing against: {self.base_url}")
        
        # Setup
        if not self.setup_test_user():
            print("❌ Failed to setup test user, aborting tests")
            return False
        
        # Run critical tests in priority order
        results = []
        results.append(self.test_calorie_calculation())  # CRITICAL - test first
        results.append(self.test_agenda_notes())
        results.append(self.test_meal_generation())
        results.append(self.test_recipe_generation())
        results.append(self.test_profile_picture())
        results.append(self.test_add_meal_to_diary())
        
        # Summary
        total_tests = len([r for r in self.test_results])
        passed_tests = len([r for r in self.test_results if r['success']])
        
        print(f"\n📊 Critical Tests Summary:")
        print(f"Total tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success rate: {(passed_tests/total_tests)*100:.1f}%")
        
        # Save results
        with open('/app/test_reports/critical_test_results.json', 'w') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "success_rate": (passed_tests/total_tests)*100 if total_tests > 0 else 0,
                "results": self.test_results
            }, f, indent=2)
        
        return all(results)

if __name__ == "__main__":
    tester = CriticalFeatureTester()
    success = tester.run_critical_tests()
    exit(0 if success else 1)