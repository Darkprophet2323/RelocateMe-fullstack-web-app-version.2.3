
import requests
import sys
import json
from datetime import datetime

class RelocateMeAPITester:
    def __init__(self, base_url):
        self.base_url = base_url
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def run_test(self, name, method, endpoint, expected_status, data=None, auth_required=False):
        """Run a single API test"""
        url = f"{self.base_url}/api/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        if auth_required and self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)

            success = response.status_code == expected_status
            
            result = {
                "name": name,
                "url": url,
                "method": method,
                "expected_status": expected_status,
                "actual_status": response.status_code,
                "success": success
            }
            
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                if response.status_code != 204:  # No content
                    try:
                        result["response"] = response.json()
                    except:
                        result["response"] = response.text
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    result["error"] = response.json()
                except:
                    result["error"] = response.text
            
            self.test_results.append(result)
            return success, response.json() if success and response.status_code != 204 else {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            self.test_results.append({
                "name": name,
                "url": url,
                "method": method,
                "success": False,
                "error": str(e)
            })
            return False, {}

    def test_login(self, username, password):
        """Test login and get token"""
        success, response = self.run_test(
            "Login",
            "POST",
            "auth/login",
            200,
            data={"username": username, "password": password}
        )
        if success and 'access_token' in response:
            self.token = response['access_token']
            return True
        return False

    def test_login_invalid(self, username, password):
        """Test login with invalid credentials"""
        success, _ = self.run_test(
            "Login with Invalid Credentials",
            "POST",
            "auth/login",
            401,
            data={"username": username, "password": password}
        )
        return success

    def test_password_reset_request(self, username):
        """Test password reset request"""
        success, response = self.run_test(
            "Password Reset Request",
            "POST",
            "auth/reset-password",
            200,
            data={"username": username}
        )
        return success, response.get('reset_code') if success else None

    def test_password_reset_complete(self, username, reset_code, new_password):
        """Test password reset completion"""
        success, _ = self.run_test(
            "Password Reset Completion",
            "POST",
            "auth/complete-password-reset",
            200,
            data={
                "username": username,
                "reset_code": reset_code,
                "new_password": new_password
            }
        )
        return success

    def test_get_user_info(self):
        """Test getting user info"""
        success, _ = self.run_test(
            "Get User Info",
            "GET",
            "auth/me",
            200,
            auth_required=True
        )
        return success

    def test_get_phoenix_data(self):
        """Test getting Phoenix location data"""
        success, _ = self.run_test(
            "Get Phoenix Data",
            "GET",
            "locations/phoenix",
            200
        )
        return success

    def test_get_peak_district_data(self):
        """Test getting Peak District location data"""
        success, _ = self.run_test(
            "Get Peak District Data",
            "GET",
            "locations/peak-district",
            200
        )
        return success

    def test_get_relocation_comparison(self):
        """Test getting relocation comparison data"""
        success, _ = self.run_test(
            "Get Relocation Comparison",
            "GET",
            "comparison/phoenix-to-peak-district",
            200,
            auth_required=True
        )
        return success

    def test_get_phoenix_housing(self):
        """Test getting Phoenix housing data"""
        success, _ = self.run_test(
            "Get Phoenix Housing Data",
            "GET",
            "housing/phoenix",
            200
        )
        return success

    def test_get_peak_district_housing(self):
        """Test getting Peak District housing data"""
        success, _ = self.run_test(
            "Get Peak District Housing Data",
            "GET",
            "housing/peak-district",
            200
        )
        return success

    def test_get_job_opportunities(self):
        """Test getting job opportunities"""
        success, _ = self.run_test(
            "Get Job Opportunities",
            "GET",
            "jobs/opportunities",
            200,
            auth_required=True
        )
        return success
    
    def test_get_job_listings(self, category=None, job_type=None):
        """Test getting job listings with optional filters"""
        endpoint = "jobs/listings"
        if category or job_type:
            params = []
            if category:
                params.append(f"category={category}")
            if job_type:
                params.append(f"job_type={job_type}")
            endpoint += f"?{'&'.join(params)}"
        
        success, response = self.run_test(
            f"Get Job Listings{' (Filtered)' if category or job_type else ''}",
            "GET",
            endpoint,
            200
        )
        return success, response
    
    def test_get_featured_jobs(self):
        """Test getting featured jobs"""
        success, response = self.run_test(
            "Get Featured Jobs",
            "GET",
            "jobs/featured",
            200
        )
        return success, response
    
    def test_get_job_categories(self):
        """Test getting job categories"""
        success, response = self.run_test(
            "Get Job Categories",
            "GET",
            "jobs/categories",
            200
        )
        return success, response
    
    def test_get_visa_requirements(self):
        """Test getting visa requirements"""
        success, response = self.run_test(
            "Get Visa Requirements",
            "GET",
            "visa/requirements",
            200
        )
        return success, response
    
    def test_get_visa_requirement_details(self, visa_type):
        """Test getting specific visa requirement details"""
        success, response = self.run_test(
            f"Get Visa Details for {visa_type}",
            "GET",
            f"visa/requirements/{visa_type}",
            200
        )
        return success, response
    
    def test_get_visa_checklist(self):
        """Test getting visa checklist"""
        success, response = self.run_test(
            "Get Visa Checklist",
            "GET",
            "visa/checklist",
            200
        )
        return success, response

    def test_get_chrome_extensions(self):
        """Test getting Chrome extensions"""
        success, response = self.run_test(
            "Get Chrome Extensions",
            "GET",
            "chrome-extensions",
            200
        )
        return success, response

    def test_download_relocate_helper(self):
        """Test downloading Relocate Helper extension"""
        success, _ = self.run_test(
            "Download Relocate Helper Extension",
            "GET",
            "download/relocate-helper.zip",
            200
        )
        return success

    def test_download_property_finder(self):
        """Test downloading Property Finder extension"""
        success, _ = self.run_test(
            "Download Property Finder Extension",
            "GET",
            "download/property-finder.zip",
            200
        )
        return success

    def test_get_dashboard_overview(self):
        """Test getting dashboard overview"""
        success, _ = self.run_test(
            "Get Dashboard Overview",
            "GET",
            "dashboard/overview",
            200,
            auth_required=True
        )
        return success
    
    def test_get_timeline_full(self):
        """Test getting full timeline"""
        success, response = self.run_test(
            "Get Full Timeline",
            "GET",
            "timeline/full",
            200,
            auth_required=True
        )
        return success, response
    
    def test_get_timeline_by_category(self):
        """Test getting timeline by category"""
        success, response = self.run_test(
            "Get Timeline By Category",
            "GET",
            "timeline/by-category",
            200,
            auth_required=True
        )
        return success, response
    
    def test_get_resources(self):
        """Test getting resources"""
        success, response = self.run_test(
            "Get Resources",
            "GET",
            "resources/all",
            200
        )
        return success, response

    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*50)
        print(f"📊 Test Summary: {self.tests_passed}/{self.tests_run} tests passed")
        print("="*50)
        
        if self.tests_passed < self.tests_run:
            print("\nFailed Tests:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"- {result['name']} ({result['method']} {result['url']})")
                    if "error" in result:
                        print(f"  Error: {result['error']}")
                    print()
        
        return self.tests_passed == self.tests_run

def main():
    # Get the backend URL from the frontend .env file
    backend_url = "https://1052d882-4c38-4389-9c98-60c715911d5c.preview.emergentagent.com"
    
    print(f"Testing Relocate Me API at: {backend_url}")
    
    # Setup tester
    tester = RelocateMeAPITester(backend_url)
    
    # Test authentication
    print("\n=== Testing Authentication ===")
    
    # Test login with valid credentials
    if not tester.test_login("relocate_user", "SecurePass2025!"):
        print("❌ Login failed, stopping tests")
        return 1
    
    # Test login with invalid credentials
    tester.test_login_invalid("relocate_user", "WrongPassword123")
    
    # Test password reset
    reset_success, reset_code = tester.test_password_reset_request("relocate_user")
    if reset_success and reset_code:
        # Test password reset completion with the provided code
        tester.test_password_reset_complete("relocate_user", "RESET2025", "NewPassword123!")
        
        # Login with the new password to verify reset worked
        if tester.test_login("relocate_user", "NewPassword123!"):
            print("✅ Password reset flow works correctly")
        else:
            print("❌ Could not login with new password after reset")
            
        # Reset back to original password for other tests
        tester.test_password_reset_request("relocate_user")
        tester.test_password_reset_complete("relocate_user", "RESET2025", "SecurePass2025!")
        tester.test_login("relocate_user", "SecurePass2025!")
    
    # Test user info endpoint
    tester.test_get_user_info()
    
    # Test location data endpoints
    print("\n=== Testing Location Data ===")
    tester.test_get_phoenix_data()
    tester.test_get_peak_district_data()
    tester.test_get_relocation_comparison()
    
    # Test housing data endpoints
    print("\n=== Testing Housing Data ===")
    tester.test_get_phoenix_housing()
    tester.test_get_peak_district_housing()
    
    # Test job data endpoints
    print("\n=== Testing Job Data ===")
    tester.test_get_job_opportunities()
    
    # Test new job listings endpoints
    job_listings_success, job_listings = tester.test_get_job_listings()
    if job_listings_success:
        print(f"✅ Found {job_listings.get('total', 0)} job listings")
        
        # Test job filtering
        if job_listings.get('categories'):
            category = job_listings['categories'][0]
            tester.test_get_job_listings(category=category)
            
        if job_listings.get('job_types'):
            job_type = job_listings['job_types'][0]
            tester.test_get_job_listings(job_type=job_type)
    
    tester.test_get_featured_jobs()
    tester.test_get_job_categories()
    
    # Test visa data endpoints
    print("\n=== Testing Visa Data ===")
    visa_success, visa_data = tester.test_get_visa_requirements()
    if visa_success and 'visa_types' in visa_data:
        print(f"✅ Found {len(visa_data['visa_types'])} visa types")
        
        # Test specific visa type details
        if visa_data['visa_types']:
            visa_type = visa_data['visa_types'][0]['visa_type'].lower().replace(" ", "-")
            tester.test_get_visa_requirement_details(visa_type)
    
    tester.test_get_visa_checklist()
    
    # Test timeline endpoints
    print("\n=== Testing Timeline Data ===")
    tester.test_get_timeline_full()
    tester.test_get_timeline_by_category()
    
    # Test resources endpoint
    print("\n=== Testing Resources ===")
    tester.test_get_resources()
    
    # Test Chrome extensions endpoints
    print("\n=== Testing Chrome Extensions ===")
    extensions_success, extensions = tester.test_get_chrome_extensions()
    if extensions_success:
        tester.test_download_relocate_helper()
        tester.test_download_property_finder()
    
    # Test dashboard overview endpoint
    print("\n=== Testing Dashboard ===")
    tester.test_get_dashboard_overview()
    
    # Print summary
    all_passed = tester.print_summary()
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
