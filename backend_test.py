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
        
        # Test onboarding completion
        onboarding_data = {
            "age": 25,
            "height": 175.0,
            "weight": 70.0,
            "target_weight": 65.0,
            "goal": "lose_weight",
            "activity_level": "moderate",
            "fitness_level": "intermediate",
            "dietary_preferences": ["vegetarian"],
            "allergies": ["nuts"]
        }
        
        success, response, details = self.test_endpoint(
            'POST', 'profile/onboarding', 200,
            data=onboarding_data
        )
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
        
        # Test generate meal plan
        success, response, details = self.test_endpoint('POST', 'meals/generate', 200)
        self.log_test("Generate Meal Plan", success, details)
        
        # Test get meal plans
        success, response, details = self.test_endpoint('GET', 'meals/plans', 200)
        self.log_test("Get Meal Plans", success, details)

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