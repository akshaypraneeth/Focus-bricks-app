#!/usr/bin/env python3
"""
CRITICAL BRICK POSITIONING FIX TEST
Tests the specific fix for brick overlapping issue
"""

import requests
import json
from datetime import datetime, timedelta

# Backend URL
BACKEND_URL = "https://08509ef4-ee99-40a7-bca2-9d774acaba5f.preview.emergentagent.com/api"

class BrickPositioningTester:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.session = requests.Session()
        self.created_tasks = []
        
    def create_and_complete_tasks(self, num_tasks=8):
        """Create and complete multiple tasks to test brick positioning"""
        
        # Test tasks in different categories
        test_tasks = [
            {"title": "Morning hydration boost", "category": "health"},
            {"title": "Quick meditation session", "category": "wellness"},
            {"title": "Strength training workout", "category": "fitness"},
            {"title": "Learn new programming concept", "category": "learning"},
            {"title": "Organize workspace", "category": "productivity"},
            {"title": "Evening walk", "category": "fitness"},
            {"title": "Read before bed", "category": "learning"},
            {"title": "Prepare healthy lunch", "category": "health"},
            {"title": "Practice guitar", "category": "learning"},
            {"title": "Call family member", "category": "wellness"},
            {"title": "Write in journal", "category": "wellness"},
            {"title": "Plan tomorrow's tasks", "category": "productivity"},
            {"title": "Stretch routine", "category": "fitness"},
            {"title": "Drink afternoon water", "category": "health"},
            {"title": "Review daily goals", "category": "productivity"}
        ]
        
        print(f"🎯 Creating and completing {num_tasks} tasks...")
        
        for i in range(min(num_tasks, len(test_tasks))):
            task_data = test_tasks[i]
            
            # Create task
            task_payload = {
                "title": task_data["title"],
                "description": f"Test task {i+1} for brick positioning",
                "category": task_data["category"],
                "is_recurring": False,
                "target_count": 1,
                "due_date": (datetime.utcnow() + timedelta(days=1)).isoformat()
            }
            
            try:
                # Create task
                response = self.session.post(f"{self.base_url}/tasks", json=task_payload)
                if response.status_code == 200:
                    task = response.json()
                    task_id = task["id"]
                    self.created_tasks.append(task_id)
                    print(f"   ✅ Created task {i+1}: {task['title']}")
                    
                    # Complete task immediately
                    complete_response = self.session.put(f"{self.base_url}/tasks/{task_id}/complete")
                    if complete_response.status_code == 200:
                        print(f"   🎉 Completed task {i+1}")
                        
                        # Get structure after each completion
                        structure_response = self.session.get(f"{self.base_url}/structure/current-week")
                        if structure_response.status_code == 200:
                            structure = structure_response.json()
                            bricks = structure.get("bricks", [])
                            
                            if len(bricks) == i + 1:
                                latest_brick = bricks[-1]
                                position = latest_brick["position"]
                                print(f"   🧱 Brick {i+1} position: x={position['x']}, y={position['y']}, z={position['z']}")
                            else:
                                print(f"   ❌ Expected {i+1} bricks, got {len(bricks)}")
                        else:
                            print(f"   ❌ Failed to get structure: {structure_response.status_code}")
                    else:
                        print(f"   ❌ Failed to complete task {i+1}: {complete_response.status_code}")
                else:
                    print(f"   ❌ Failed to create task {i+1}: {response.status_code}")
                    
            except Exception as e:
                print(f"   ❌ Error with task {i+1}: {str(e)}")
    
    def analyze_brick_positions(self):
        """Analyze the final brick positions for overlapping and proper stacking"""
        print(f"\n🔍 ANALYZING BRICK POSITIONING...")
        
        try:
            response = self.session.get(f"{self.base_url}/structure/current-week")
            if response.status_code != 200:
                print(f"❌ Failed to get structure: {response.status_code}")
                return False
                
            structure = response.json()
            bricks = structure.get("bricks", [])
            
            if not bricks:
                print("❌ No bricks found in structure")
                return False
                
            print(f"📊 Found {len(bricks)} bricks total")
            
            # Extract all positions
            positions = []
            for i, brick in enumerate(bricks):
                pos = brick["position"]
                positions.append(pos)
                print(f"   Brick {i+1}: x={pos['x']}, y={pos['y']}, z={pos['z']} - {brick['task_title']} ({brick['category']})")
            
            # Test 1: Check for unique positions (CRITICAL - no overlapping)
            print(f"\n🎯 TEST 1: UNIQUE POSITIONS (NO OVERLAPPING)")
            unique_positions = set()
            overlapping_bricks = []
            
            for i, pos in enumerate(positions):
                pos_tuple = (pos['x'], pos['y'], pos['z'])
                if pos_tuple in unique_positions:
                    overlapping_bricks.append(i + 1)
                    print(f"   ❌ Brick {i+1} OVERLAPS at position {pos_tuple}")
                else:
                    unique_positions.add(pos_tuple)
            
            if not overlapping_bricks:
                print(f"   ✅ SUCCESS: All {len(positions)} bricks have UNIQUE positions")
            else:
                print(f"   ❌ CRITICAL FAILURE: {len(overlapping_bricks)} bricks are overlapping!")
                return False
            
            # Test 2: Verify building pattern (first 7 bricks should form bottom row)
            print(f"\n🎯 TEST 2: BOTTOM ROW FORMATION")
            if len(positions) >= 7:
                bottom_y = positions[0]['y']
                bottom_row_bricks = []
                
                for i in range(min(7, len(positions))):
                    if positions[i]['y'] == bottom_y:
                        bottom_row_bricks.append(i + 1)
                
                if len(bottom_row_bricks) == 7:
                    print(f"   ✅ SUCCESS: First 7 bricks form bottom row at y={bottom_y}")
                else:
                    print(f"   ⚠️  WARNING: Only {len(bottom_row_bricks)} bricks in bottom row")
            
            # Test 3: Verify layer stacking (Y coordinates should decrease for higher layers)
            print(f"\n🎯 TEST 3: LAYER STACKING")
            if len(positions) >= 15:
                first_layer_y = positions[0]['y']
                second_layer_y = positions[14]['y']  # 15th brick should be in second layer
                
                if second_layer_y < first_layer_y:
                    print(f"   ✅ SUCCESS: Second layer (y={second_layer_y}) is higher than first layer (y={first_layer_y})")
                else:
                    print(f"   ❌ FAILURE: Second layer (y={second_layer_y}) is not higher than first layer (y={first_layer_y})")
            else:
                print(f"   ℹ️  INFO: Need 15+ bricks to test layer stacking (have {len(positions)})")
            
            # Test 4: Building pattern analysis
            print(f"\n🎯 TEST 4: BUILDING PATTERN ANALYSIS")
            layer_analysis = {}
            
            for i, pos in enumerate(positions):
                y_coord = pos['y']
                if y_coord not in layer_analysis:
                    layer_analysis[y_coord] = []
                layer_analysis[y_coord].append(i + 1)
            
            print(f"   Building has {len(layer_analysis)} layers:")
            for y_coord in sorted(layer_analysis.keys(), reverse=True):
                bricks_in_layer = layer_analysis[y_coord]
                print(f"   Layer y={y_coord}: {len(bricks_in_layer)} bricks (#{bricks_in_layer})")
            
            # Test 5: Verify building dimensions
            print(f"\n🎯 TEST 5: BUILDING DIMENSIONS")
            x_coords = [pos['x'] for pos in positions]
            z_coords = [pos['z'] for pos in positions]
            y_coords = [pos['y'] for pos in positions]
            
            x_range = max(x_coords) - min(x_coords)
            z_range = max(z_coords) - min(z_coords)
            y_range = max(y_coords) - min(y_coords)
            
            print(f"   X-range: {x_range:.1f} (width)")
            print(f"   Y-range: {y_range:.1f} (height)")
            print(f"   Z-range: {z_range:.1f} (depth)")
            
            if x_range > 0:
                print(f"   ✅ Building has proper width distribution")
            else:
                print(f"   ❌ Building has no width - all bricks in same X position")
                
            return len(overlapping_bricks) == 0
            
        except Exception as e:
            print(f"❌ Error analyzing positions: {str(e)}")
            return False
    
    def cleanup(self):
        """Clean up created tasks"""
        print(f"\n🧹 Cleaning up {len(self.created_tasks)} created tasks...")
        for task_id in self.created_tasks:
            try:
                self.session.delete(f"{self.base_url}/tasks/{task_id}")
            except:
                pass
    
    def run_test(self):
        """Run the complete brick positioning test"""
        print("🚀 CRITICAL BRICK POSITIONING FIX TEST")
        print("=" * 60)
        print("Testing fix for: 'Bricks are overlapping instead of stacking properly'")
        print("=" * 60)
        
        # Create and complete 8 tasks
        self.create_and_complete_tasks(8)
        
        # Analyze the results
        success = self.analyze_brick_positions()
        
        print(f"\n" + "=" * 60)
        if success:
            print("🎉 BRICK POSITIONING FIX: SUCCESS!")
            print("✅ All bricks have unique positions")
            print("✅ No overlapping detected")
            print("✅ Building structure is forming properly")
        else:
            print("❌ BRICK POSITIONING FIX: FAILED!")
            print("❌ Bricks are still overlapping or not positioned correctly")
        print("=" * 60)
        
        return success

def main():
    tester = BrickPositioningTester()
    try:
        success = tester.run_test()
        return success
    finally:
        tester.cleanup()

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
