#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime
import time

class FocusedAPITester:
    def __init__(self, base_url="https://coach-upgrade-1.preview.emergentagent.com/api"):
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

    def test_endpoint(self, method, endpoint, expected_status, data=None):
        """Test a single API endpoint"""
        url = f"{self.base_url}/{endpoint}"
        
        try:
            if method == 'GET':
                response = self.session.get(url)
            elif method == 'POST':
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

    def setup_auth(self):
        """Setup authentication"""
        print("🔐 Setting up authentication...")
        
        # Test user registration
        test_email = f"focused.test.{int(time.time())}@example.com"
        test_password = "TestPass123!"
        test_name = "Focused Test User"
        
        success, response, details = self.test_endpoint(
            'POST', 'auth/register', 200,
            data={
                "email": test_email,
                "password": test_password,
                "name": test_name
            }
        )
        
        if success and 'user_id' in response:
            self.user_id = response['user_id']
            print(f"✅ Authentication setup successful - User ID: {self.user_id}")
            return True
        else:
            print(f"❌ Authentication setup failed - {details}")
            return False

    def test_specific_endpoints(self):
        """Test the specific endpoints mentioned in the review request"""
        print("\n🎯 Testing Specific Review Request Endpoints...")
        
        # 1. Test Workouts Add to Agenda - POST /api/workouts/add-to-agenda
        print("\n📅 Testing Workouts Add to Agenda...")
        workout_agenda_data = {
            "video_data": {
                "id": "workout_123",
                "title": "HIIT Cardio Intense",
                "duration": "25:00",
                "calories_estimate": 300,
                "category_name": "Cardio"
            },
            "scheduled_date": "2024-01-15"
        }
        
        success, response, details = self.test_endpoint(
            'POST', 'workouts/add-to-agenda', 200,
            data=workout_agenda_data
        )
        
        # Verify response structure
        if success and response:
            has_message = 'message' in response
            has_appointment = 'appointment' in response
            appointment = response.get('appointment', {})
            
            # Check appointment structure
            required_fields = ['appointment_id', 'user_id', 'title', 'description', 'date', 'type', 'video_data']
            appointment_valid = all(field in appointment for field in required_fields)
            
            self.log_test("Add to Agenda - Response Structure", has_message and has_appointment, 
                         f"Has message: {has_message}, Has appointment: {has_appointment}")
            self.log_test("Add to Agenda - Appointment Fields", appointment_valid, 
                         f"Missing fields: {[f for f in required_fields if f not in appointment]}")
            
            # Verify appointment type is 'workout'
            is_workout_type = appointment.get('type') == 'workout'
            self.log_test("Add to Agenda - Workout Type", is_workout_type, 
                         f"Type: {appointment.get('type')}")
        
        self.log_test("Workouts Add to Agenda", success, details)
        
        # 2. Test Workouts Share - POST /api/workouts/share
        print("\n📢 Testing Workouts Share...")
        workout_share_data = {
            "video_data": {
                "id": "workout_456",
                "title": "Yoga Flow Débutant",
                "duration": "30:00",
                "calories_estimate": 150
            },
            "calories_burned": 180,
            "target_wall": "public"
        }
        
        success, response, details = self.test_endpoint(
            'POST', 'workouts/share', 200,
            data=workout_share_data
        )
        
        # Verify response structure
        if success and response:
            has_message = 'message' in response
            has_post = 'post' in response
            has_points = 'points_earned' in response
            post = response.get('post', {})
            
            # Check post structure
            required_fields = ['post_id', 'user_id', 'content', 'type', 'video_data', 'target_wall']
            post_valid = all(field in post for field in required_fields)
            
            self.log_test("Workout Share - Response Structure", has_message and has_post and has_points, 
                         f"Has message: {has_message}, Has post: {has_post}, Has points: {has_points}")
            self.log_test("Workout Share - Post Fields", post_valid, 
                         f"Missing fields: {[f for f in required_fields if f not in post]}")
            
            # Verify post type and target wall
            is_workout_share = post.get('type') == 'workout_share'
            correct_target = post.get('target_wall') == 'public'
            self.log_test("Workout Share - Post Type", is_workout_share, 
                         f"Type: {post.get('type')}")
            self.log_test("Workout Share - Target Wall", correct_target, 
                         f"Target: {post.get('target_wall')}")
        
        self.log_test("Workouts Share", success, details)
        
        # 3. Test User Groups - GET /api/social/user-groups
        print("\n👥 Testing User Groups...")
        success, response, details = self.test_endpoint('GET', 'social/user-groups', 200)
        
        # Verify response structure
        if success and response:
            has_groups = 'groups' in response
            groups = response.get('groups', [])
            is_list = isinstance(groups, list)
            
            self.log_test("User Groups - Response Structure", has_groups, 
                         f"Response keys: {list(response.keys())}")
            self.log_test("User Groups - Groups List", is_list, 
                         f"Groups type: {type(groups)}, Count: {len(groups) if is_list else 'N/A'}")
        
        self.log_test("User Groups", success, details)
        
        # 4. Test Share Achievement - POST /api/social/share-achievement
        print("\n🏆 Testing Share Achievement...")
        
        # Test with challenge achievement
        challenge_data = {
            "type": "challenge",
            "data": {
                "title": "Défi 7 jours cardio",
                "description": "Complété avec succès !"
            },
            "target_wall": "public"
        }
        
        success, response, details = self.test_endpoint(
            'POST', 'social/share-achievement', 200,
            data=challenge_data
        )
        
        # Verify response structure
        if success and response:
            has_message = 'message' in response
            has_post = 'post' in response
            has_points = 'points_earned' in response
            post = response.get('post', {})
            
            # Check post structure
            required_fields = ['post_id', 'user_id', 'content', 'type', 'achievement_data', 'target_wall']
            post_valid = all(field in post for field in required_fields)
            
            self.log_test("Share Achievement - Response Structure", has_message and has_post and has_points, 
                         f"Has message: {has_message}, Has post: {has_post}, Has points: {has_points}")
            self.log_test("Share Achievement - Post Fields", post_valid, 
                         f"Missing fields: {[f for f in required_fields if f not in post]}")
            
            # Verify post type for challenge
            is_challenge_share = post.get('type') == 'challenge_share'
            self.log_test("Share Achievement - Challenge Type", is_challenge_share, 
                         f"Type: {post.get('type')}")
        
        self.log_test("Share Achievement (Challenge)", success, details)
        
        # Test with badge achievement
        badge_data = {
            "type": "badge",
            "data": {
                "name": "Première semaine",
                "description": "7 jours d'activité consécutifs",
                "icon": "🌟"
            },
            "target_wall": "public"
        }
        
        success, response, details = self.test_endpoint(
            'POST', 'social/share-achievement', 200,
            data=badge_data
        )
        
        # Verify badge share type
        if success and response:
            post = response.get('post', {})
            is_badge_share = post.get('type') == 'badge_share'
            self.log_test("Share Achievement - Badge Type", is_badge_share, 
                         f"Type: {post.get('type')}")
        
        self.log_test("Share Achievement (Badge)", success, details)
        
        # 5. Test Articles - GET /api/articles
        print("\n📰 Testing Articles...")
        success, response, details = self.test_endpoint('GET', 'articles', 200)
        
        # Verify response structure
        if success and response:
            has_articles = 'articles' in response
            has_total = 'total' in response
            has_date = 'date' in response
            has_day_seed = 'day_seed' in response
            
            articles = response.get('articles', [])
            total = response.get('total', 0)
            
            # Check if we have 10 articles
            has_ten_articles = len(articles) == 10 and total == 10
            
            # Check article structure
            article_valid = True
            if articles:
                first_article = articles[0]
                required_fields = ['title', 'summary', 'category', 'source', 'read_time', 'content']
                article_valid = all(field in first_article for field in required_fields)
            
            self.log_test("Articles - Response Structure", has_articles and has_total and has_date and has_day_seed, 
                         f"Response keys: {list(response.keys())}")
            self.log_test("Articles - Count (10 articles)", has_ten_articles, 
                         f"Articles count: {len(articles)}, Total: {total}")
            self.log_test("Articles - Article Fields", article_valid, 
                         f"First article fields: {list(first_article.keys()) if articles else 'No articles'}")
            
            # Check categories are present
            if articles:
                categories = set(article.get('category') for article in articles)
                has_categories = len(categories) > 1
                self.log_test("Articles - Multiple Categories", has_categories, 
                             f"Categories found: {list(categories)}")
        
        self.log_test("Articles Endpoint", success, details)

    def run_focused_tests(self):
        """Run focused tests on specific endpoints"""
        print("🚀 Starting Focused Fat & Slim API Tests...")
        print(f"Testing against: {self.base_url}")
        
        # Setup authentication first
        if not self.setup_auth():
            print("❌ Authentication failed, stopping tests")
            return False
        
        # Test specific endpoints
        self.test_specific_endpoints()
        
        # Print summary
        print(f"\n📊 Test Summary:")
        print(f"Tests run: {self.tests_run}")
        print(f"Tests passed: {self.tests_passed}")
        print(f"Success rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        return self.tests_passed == self.tests_run

def main():
    tester = FocusedAPITester()
    success = tester.run_focused_tests()
    
    # Save test results
    with open('/app/test_reports/focused_test_results.json', 'w') as f:
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