#!/usr/bin/env python3
"""
Focus Bricks Backend API Testing Suite
Tests all backend endpoints for the productivity app
"""

import requests
import json
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Get backend URL from environment
BACKEND_URL = "https://08509ef4-ee99-40a7-bca2-9d774acaba5f.preview.emergentagent.com/api"

class FocusBricksAPITester:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.session = requests.Session()
        self.created_tasks = []  # Track created tasks for cleanup
        self.test_results = {
            "passed": 0,
            "failed": 0,
            "errors": []
        }
    
    def log_result(self, test_name: str, success: bool, message: str = ""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
        if message:
            print(f"   {message}")
        
        if success:
            self.test_results["passed"] += 1
        else:
            self.test_results["failed"] += 1
            self.test_results["errors"].append(f"{test_name}: {message}")
    
    def test_api_root(self):
        """Test API root endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/")
            if response.status_code == 200:
                data = response.json()
                if "Focus Bricks API" in data.get("message", ""):
                    self.log_result("API Root Endpoint", True, f"Response: {data['message']}")
                else:
                    self.log_result("API Root Endpoint", False, f"Unexpected message: {data}")
            else:
                self.log_result("API Root Endpoint", False, f"Status: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.log_result("API Root Endpoint", False, f"Exception: {str(e)}")
    
    def test_task_bundles_list(self):
        """Test getting task bundles"""
        try:
            response = self.session.get(f"{self.base_url}/task-bundles")
            if response.status_code == 200:
                bundles = response.json()
                if isinstance(bundles, list) and len(bundles) > 0:
                    # Check if bundles have expected structure
                    bundle = bundles[0]
                    required_fields = ["id", "name", "description", "category", "tasks", "icon", "color"]
                    if all(field in bundle for field in required_fields):
                        self.log_result("Task Bundles List", True, f"Found {len(bundles)} bundles")
                        return bundles
                    else:
                        self.log_result("Task Bundles List", False, f"Missing required fields in bundle: {bundle}")
                else:
                    self.log_result("Task Bundles List", False, "No bundles returned or invalid format")
            else:
                self.log_result("Task Bundles List", False, f"Status: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.log_result("Task Bundles List", False, f"Exception: {str(e)}")
        return []
    
    def test_activate_task_bundle(self, bundle_id: str):
        """Test activating a task bundle"""
        try:
            response = self.session.post(f"{self.base_url}/task-bundles/{bundle_id}/activate")
            if response.status_code == 200:
                data = response.json()
                if "tasks_created" in data and data["tasks_created"] > 0:
                    self.log_result("Activate Task Bundle", True, f"Created {data['tasks_created']} tasks from bundle")
                    return True
                else:
                    self.log_result("Activate Task Bundle", False, f"No tasks created: {data}")
            else:
                self.log_result("Activate Task Bundle", False, f"Status: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.log_result("Activate Task Bundle", False, f"Exception: {str(e)}")
        return False
    
    def test_create_task(self):
        """Test creating a new task"""
        task_data = {
            "title": "Complete morning workout routine",
            "description": "30-minute full body workout to start the day strong",
            "category": "fitness",
            "is_recurring": False,
            "target_count": 1,
            "due_date": (datetime.utcnow() + timedelta(days=1)).isoformat()
        }
        
        try:
            response = self.session.post(f"{self.base_url}/tasks", json=task_data)
            if response.status_code == 200:
                task = response.json()
                if "id" in task and task["title"] == task_data["title"]:
                    self.created_tasks.append(task["id"])
                    self.log_result("Create Task", True, f"Created task: {task['title']}")
                    return task
                else:
                    self.log_result("Create Task", False, f"Invalid task response: {task}")
            else:
                self.log_result("Create Task", False, f"Status: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.log_result("Create Task", False, f"Exception: {str(e)}")
        return None
    
    def test_get_all_tasks(self):
        """Test getting all tasks"""
        try:
            response = self.session.get(f"{self.base_url}/tasks")
            if response.status_code == 200:
                tasks = response.json()
                if isinstance(tasks, list):
                    self.log_result("Get All Tasks", True, f"Retrieved {len(tasks)} tasks")
                    return tasks
                else:
                    self.log_result("Get All Tasks", False, f"Invalid response format: {tasks}")
            else:
                self.log_result("Get All Tasks", False, f"Status: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.log_result("Get All Tasks", False, f"Exception: {str(e)}")
        return []
    
    def test_get_today_tasks(self):
        """Test getting today's tasks"""
        try:
            response = self.session.get(f"{self.base_url}/tasks/today")
            if response.status_code == 200:
                tasks = response.json()
                if isinstance(tasks, list):
                    self.log_result("Get Today's Tasks", True, f"Retrieved {len(tasks)} today's tasks")
                    return tasks
                else:
                    self.log_result("Get Today's Tasks", False, f"Invalid response format: {tasks}")
            else:
                self.log_result("Get Today's Tasks", False, f"Status: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.log_result("Get Today's Tasks", False, f"Exception: {str(e)}")
        return []
    
    def test_complete_task(self, task_id: str):
        """Test completing a task"""
        try:
            response = self.session.put(f"{self.base_url}/tasks/{task_id}/complete")
            if response.status_code == 200:
                data = response.json()
                if "message" in data and "task" in data:
                    self.log_result("Complete Task", True, f"Task completed: {data['message']}")
                    return True
                else:
                    self.log_result("Complete Task", False, f"Invalid response: {data}")
            else:
                self.log_result("Complete Task", False, f"Status: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.log_result("Complete Task", False, f"Exception: {str(e)}")
        return False
    
    def test_increment_task(self, task_id: str):
        """Test incrementing task progress"""
        try:
            response = self.session.put(f"{self.base_url}/tasks/{task_id}/increment")
            if response.status_code == 200:
                data = response.json()
                if "task" in data:
                    self.log_result("Increment Task", True, f"Task incremented successfully")
                    return True
                else:
                    self.log_result("Increment Task", False, f"Invalid response: {data}")
            else:
                self.log_result("Increment Task", False, f"Status: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.log_result("Increment Task", False, f"Exception: {str(e)}")
        return False
    
    def test_weekly_structure(self):
        """Test getting current week structure (3D brick positioning)"""
        try:
            response = self.session.get(f"{self.base_url}/structure/current-week")
            if response.status_code == 200:
                data = response.json()
                if "bricks" in data and "week_start" in data:
                    bricks = data["bricks"]
                    self.log_result("Weekly Structure", True, f"Retrieved structure with {len(bricks)} bricks")
                    
                    # Verify brick structure if any bricks exist
                    if bricks:
                        brick = bricks[0]
                        required_fields = ["id", "task_title", "category", "position", "completed_at"]
                        if all(field in brick for field in required_fields):
                            position = brick["position"]
                            if "x" in position and "y" in position and "z" in position:
                                self.log_result("Brick 3D Positioning", True, f"Brick position: {position}")
                            else:
                                self.log_result("Brick 3D Positioning", False, f"Invalid position format: {position}")
                        else:
                            self.log_result("Brick Structure", False, f"Missing required fields in brick: {brick}")
                    
                    return data
                else:
                    self.log_result("Weekly Structure", False, f"Invalid response format: {data}")
            else:
                self.log_result("Weekly Structure", False, f"Status: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.log_result("Weekly Structure", False, f"Exception: {str(e)}")
        return None
    
    def test_weekly_stats(self):
        """Test getting weekly statistics"""
        try:
            response = self.session.get(f"{self.base_url}/stats/weekly")
            if response.status_code == 200:
                stats = response.json()
                required_fields = ["week_start", "total_tasks", "completed_tasks", "completion_rate", "bricks_earned"]
                if all(field in stats for field in required_fields):
                    self.log_result("Weekly Statistics", True, 
                                  f"Stats: {stats['completed_tasks']}/{stats['total_tasks']} tasks, "
                                  f"{stats['completion_rate']}% completion, {stats['bricks_earned']} bricks")
                    return stats
                else:
                    self.log_result("Weekly Statistics", False, f"Missing required fields: {stats}")
            else:
                self.log_result("Weekly Statistics", False, f"Status: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.log_result("Weekly Statistics", False, f"Exception: {str(e)}")
        return None
    
    def test_delete_task(self, task_id: str):
        """Test deleting a task"""
        try:
            response = self.session.delete(f"{self.base_url}/tasks/{task_id}")
            if response.status_code == 200:
                data = response.json()
                if "message" in data:
                    self.log_result("Delete Task", True, f"Task deleted: {data['message']}")
                    return True
                else:
                    self.log_result("Delete Task", False, f"Invalid response: {data}")
            else:
                self.log_result("Delete Task", False, f"Status: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.log_result("Delete Task", False, f"Exception: {str(e)}")
        return False
    
    def cleanup_created_tasks(self):
        """Clean up tasks created during testing"""
        print("\n🧹 Cleaning up created tasks...")
        for task_id in self.created_tasks:
            try:
                self.session.delete(f"{self.base_url}/tasks/{task_id}")
            except:
                pass  # Ignore cleanup errors
    
    def test_brick_positioning_fix(self):
        """CRITICAL TEST: Test the brick positioning fix for proper stacking"""
        print("\n🧱 CRITICAL BRICK POSITIONING TEST")
        print("=" * 50)
        
        # Create multiple tasks in different categories
        test_tasks = [
            {"title": "Morning hydration boost", "category": "health", "description": "Drink a large glass of water"},
            {"title": "Quick meditation session", "category": "wellness", "description": "5-minute mindfulness practice"},
            {"title": "Strength training workout", "category": "fitness", "description": "30-minute weight lifting"},
            {"title": "Learn new programming concept", "category": "learning", "description": "Study for 45 minutes"},
            {"title": "Organize workspace", "category": "productivity", "description": "Clean and organize desk area"},
            {"title": "Evening walk", "category": "fitness", "description": "20-minute outdoor walk"},
            {"title": "Read before bed", "category": "learning", "description": "Read 20 pages of current book"},
            {"title": "Prepare healthy lunch", "category": "health", "description": "Cook nutritious meal"}
        ]
        
        created_task_ids = []
        
        # Step 1: Create all tasks
        print("📝 Creating test tasks...")
        for i, task_data in enumerate(test_tasks):
            task_payload = {
                "title": task_data["title"],
                "description": task_data["description"],
                "category": task_data["category"],
                "is_recurring": False,
                "target_count": 1,
                "due_date": (datetime.utcnow() + timedelta(days=1)).isoformat()
            }
            
            try:
                response = self.session.post(f"{self.base_url}/tasks", json=task_payload)
                if response.status_code == 200:
                    task = response.json()
                    created_task_ids.append(task["id"])
                    self.created_tasks.append(task["id"])  # For cleanup
                    print(f"   ✅ Created task {i+1}: {task['title']}")
                else:
                    self.log_result(f"Create Test Task {i+1}", False, f"Failed to create task: {response.text}")
                    return False
            except Exception as e:
                self.log_result(f"Create Test Task {i+1}", False, f"Exception: {str(e)}")
                return False
        
        # Step 2: Complete tasks one by one and verify brick positioning
        print(f"\n🎯 Completing tasks and testing brick positioning...")
        all_positions = []
        
        for i, task_id in enumerate(created_task_ids):
            print(f"\n--- Completing Task {i+1} ---")
            
            # Complete the task
            try:
                response = self.session.put(f"{self.base_url}/tasks/{task_id}/complete")
                if response.status_code == 200:
                    print(f"   ✅ Task {i+1} completed successfully")
                else:
                    self.log_result(f"Complete Task {i+1}", False, f"Failed to complete: {response.text}")
                    continue
            except Exception as e:
                self.log_result(f"Complete Task {i+1}", False, f"Exception: {str(e)}")
                continue
            
            # Get current week structure
            try:
                response = self.session.get(f"{self.base_url}/structure/current-week")
                if response.status_code == 200:
                    structure = response.json()
                    bricks = structure.get("bricks", [])
                    
                    if len(bricks) == i + 1:  # Should have i+1 bricks now
                        latest_brick = bricks[-1]  # Get the latest brick
                        position = latest_brick["position"]
                        all_positions.append(position)
                        
                        print(f"   🧱 Brick {i+1} position: x={position['x']}, y={position['y']}, z={position['z']}")
                        print(f"   📋 Task: {latest_brick['task_title']} ({latest_brick['category']})")
                        
                        # Verify position has all coordinates
                        if "x" in position and "y" in position and "z" in position:
                            self.log_result(f"Brick {i+1} Position Format", True, f"Valid 3D coordinates")
                        else:
                            self.log_result(f"Brick {i+1} Position Format", False, f"Missing coordinates: {position}")
                    else:
                        self.log_result(f"Brick {i+1} Creation", False, f"Expected {i+1} bricks, got {len(bricks)}")
                else:
                    self.log_result(f"Get Structure After Task {i+1}", False, f"Status: {response.status_code}")
            except Exception as e:
                self.log_result(f"Get Structure After Task {i+1}", False, f"Exception: {str(e)}")
        
        # Step 3: Verify brick positioning rules
        print(f"\n🔍 ANALYZING BRICK POSITIONING...")
        
        if len(all_positions) > 0:
            # Test 1: Check for unique positions (no overlapping)
            unique_positions = []
            overlapping_found = False
            
            for i, pos in enumerate(all_positions):
                pos_tuple = (pos['x'], pos['y'], pos['z'])
                if pos_tuple in unique_positions:
                    overlapping_found = True
                    self.log_result("Unique Brick Positions", False, f"Brick {i+1} overlaps with previous brick at {pos_tuple}")
                else:
                    unique_positions.append(pos_tuple)
            
            if not overlapping_found:
                self.log_result("Unique Brick Positions", True, f"All {len(all_positions)} bricks have unique positions")
            
            # Test 2: Verify stacking pattern (first 7 bricks should be bottom row)
            if len(all_positions) >= 7:
                bottom_row_y = all_positions[0]['y']  # Y coordinate of first brick
                bottom_row_correct = True
                
                for i in range(min(7, len(all_positions))):
                    if all_positions[i]['y'] != bottom_row_y:
                        bottom_row_correct = False
                        break
                
                if bottom_row_correct:
                    self.log_result("Bottom Row Formation", True, f"First 7 bricks form bottom row at y={bottom_row_y}")
                else:
                    self.log_result("Bottom Row Formation", False, f"First 7 bricks don't form consistent bottom row")
            
            # Test 3: Verify layer stacking (Y coordinates should decrease for higher layers)
            if len(all_positions) >= 15:  # Need at least 15 bricks to test second layer
                first_layer_y = all_positions[0]['y']
                second_layer_y = all_positions[14]['y']  # 15th brick should be in second layer
                
                if second_layer_y < first_layer_y:  # Negative Y = higher
                    self.log_result("Layer Stacking", True, f"Second layer (y={second_layer_y}) is higher than first layer (y={first_layer_y})")
                else:
                    self.log_result("Layer Stacking", False, f"Second layer (y={second_layer_y}) is not higher than first layer (y={first_layer_y})")
            
            # Test 4: Verify building pattern structure
            print(f"\n📊 BUILDING PATTERN ANALYSIS:")
            layer_analysis = {}
            
            for i, pos in enumerate(all_positions):
                y_coord = pos['y']
                if y_coord not in layer_analysis:
                    layer_analysis[y_coord] = []
                layer_analysis[y_coord].append(i + 1)
            
            for y_coord in sorted(layer_analysis.keys(), reverse=True):  # Sort by Y (highest first)
                bricks_in_layer = layer_analysis[y_coord]
                print(f"   Layer y={y_coord}: {len(bricks_in_layer)} bricks (brick numbers: {bricks_in_layer})")
            
            # Test 5: Verify expected building dimensions
            if len(all_positions) > 0:
                x_coords = [pos['x'] for pos in all_positions]
                z_coords = [pos['z'] for pos in all_positions]
                
                x_range = max(x_coords) - min(x_coords)
                z_range = max(z_coords) - min(z_coords)
                
                print(f"   Building dimensions: X-range={x_range:.1f}, Z-range={z_range:.1f}")
                
                if x_range > 0 and z_range >= 0:  # Should have some spread in X, Z can be 0 for single row
                    self.log_result("Building Dimensions", True, f"Building has proper dimensions")
                else:
                    self.log_result("Building Dimensions", False, f"Building dimensions seem incorrect")
        
        return len(all_positions) > 0

    def run_comprehensive_test(self):
        """Run all tests in sequence"""
        print("🚀 Starting Focus Bricks Backend API Tests")
        print(f"🔗 Testing API at: {self.base_url}")
        print("=" * 60)
        
        # Test 1: API Root
        self.test_api_root()
        
        # Test 2: Task Bundles
        bundles = self.test_task_bundles_list()
        
        # Test 3: Activate Bundle (if bundles exist)
        if bundles:
            bundle_activated = self.test_activate_task_bundle(bundles[0]["id"])
        
        # Test 4: Create Task
        created_task = self.test_create_task()
        
        # Test 5: Get All Tasks
        all_tasks = self.test_get_all_tasks()
        
        # Test 6: Get Today's Tasks
        today_tasks = self.test_get_today_tasks()
        
        # Test 7: Task Operations (if we have a task)
        if created_task:
            task_id = created_task["id"]
            
            # Test increment
            self.test_increment_task(task_id)
            
            # Test complete (this should create a brick)
            self.test_complete_task(task_id)
        
        # Test 8: Weekly Structure (should show bricks if tasks completed)
        self.test_weekly_structure()
        
        # Test 9: Weekly Statistics
        self.test_weekly_stats()
        
        # CRITICAL TEST: Brick Positioning Fix
        print("\n" + "🔥" * 60)
        print("CRITICAL BRICK POSITIONING FIX TEST")
        print("🔥" * 60)
        self.test_brick_positioning_fix()
        
        # Test 10: Delete Task (if we created one)
        if created_task:
            self.test_delete_task(created_task["id"])
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        print(f"✅ Passed: {self.test_results['passed']}")
        print(f"❌ Failed: {self.test_results['failed']}")
        
        if self.test_results['errors']:
            print("\n🚨 FAILED TESTS:")
            for error in self.test_results['errors']:
                print(f"   • {error}")
        
        success_rate = (self.test_results['passed'] / (self.test_results['passed'] + self.test_results['failed'])) * 100
        print(f"\n📈 Success Rate: {success_rate:.1f}%")
        
        return self.test_results['failed'] == 0

def main():
    """Main test execution"""
    tester = FocusBricksAPITester()
    
    try:
        success = tester.run_comprehensive_test()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {str(e)}")
        sys.exit(1)
    finally:
        tester.cleanup_created_tasks()

if __name__ == "__main__":
    main()
