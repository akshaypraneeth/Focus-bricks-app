from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime, timedelta
from enum import Enum

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Enums
class TaskCategory(str, Enum):
    HEALTH = "health"
    PRODUCTIVITY = "productivity"
    WELLNESS = "wellness"
    LEARNING = "learning"
    FITNESS = "fitness"
    CUSTOM = "custom"

class TaskStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    SKIPPED = "skipped"

# Models
class Task(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = "default_user"  # For MVP, using single user
    title: str
    description: Optional[str] = ""
    category: TaskCategory
    is_recurring: bool = False
    target_count: int = 1  # For tasks like "drink 8 glasses of water"
    current_count: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    due_date: Optional[datetime] = None

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = ""
    category: TaskCategory
    is_recurring: bool = False
    target_count: int = 1
    due_date: Optional[datetime] = None

class TaskBundle(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    category: TaskCategory
    tasks: List[str]  # Task titles
    icon: str
    color: str

class Progress(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = "default_user"
    task_id: str
    completed_at: datetime = Field(default_factory=datetime.utcnow)
    week_start: datetime  # Monday of the week
    brick_position: dict  # {"x": 0, "y": 0, "z": 0} for 3D positioning

class WeeklyStats(BaseModel):
    week_start: datetime
    total_tasks: int
    completed_tasks: int
    completion_rate: float
    bricks_earned: int

# Initialize suggested task bundles
SUGGESTED_BUNDLES = [
    TaskBundle(
        name="💧 Hydration Hero",
        description="Stay hydrated throughout the day",
        category=TaskCategory.HEALTH,
        tasks=[
            "Drink water upon waking",
            "Have water with lunch", 
            "Afternoon hydration break",
            "Evening water intake"
        ],
        icon="💧",
        color="from-blue-400 to-cyan-500"
    ),
    TaskBundle(
        name="🧘 Mindful Moments",
        description="Daily meditation and mindfulness practice",
        category=TaskCategory.WELLNESS,
        tasks=[
            "5-minute morning meditation",
            "Mindful breathing break",
            "Evening gratitude practice"
        ],
        icon="🧘",
        color="from-purple-400 to-pink-500"
    ),
    TaskBundle(
        name="💪 Fitness Focus",
        description="Keep your body moving and strong",
        category=TaskCategory.FITNESS,
        tasks=[
            "Morning stretch routine",
            "30-minute workout",
            "Evening walk",
            "Strength training"
        ],
        icon="💪",
        color="from-orange-400 to-red-500"
    ),
    TaskBundle(
        name="😴 Sleep Schedule",
        description="Optimize your sleep for better health",
        category=TaskCategory.HEALTH,
        tasks=[
            "Set bedtime routine",
            "No screens 1 hour before bed",
            "Read before sleep",
            "Wake up without snoozing"
        ],
        icon="😴",
        color="from-indigo-400 to-purple-500"
    )
]

# Routes
@api_router.get("/")
async def root():
    return {"message": "Focus Bricks API - Build your productivity one brick at a time!"}

# Task Bundles Endpoints
@api_router.get("/task-bundles", response_model=List[TaskBundle])
async def get_task_bundles():
    return SUGGESTED_BUNDLES

@api_router.post("/task-bundles/{bundle_id}/activate")
async def activate_task_bundle(bundle_id: str):
    bundle = next((b for b in SUGGESTED_BUNDLES if b.id == bundle_id), None)
    if not bundle:
        raise HTTPException(status_code=404, detail="Bundle not found")
    
    # Create tasks from bundle
    created_tasks = []
    for task_title in bundle.tasks:
        task = Task(
            title=task_title,
            category=bundle.category,
            is_recurring=True,
            due_date=datetime.utcnow() + timedelta(days=1)
        )
        await db.tasks.insert_one(task.dict())
        created_tasks.append(task)
    
    return {"message": f"Activated {bundle.name}", "tasks_created": len(created_tasks)}

# Tasks Endpoints
@api_router.post("/tasks", response_model=Task)
async def create_task(task_data: TaskCreate):
    task = Task(**task_data.dict())
    await db.tasks.insert_one(task.dict())
    return task

@api_router.get("/tasks", response_model=List[Task])
async def get_tasks(category: Optional[TaskCategory] = None):
    query = {"user_id": "default_user"}
    if category:
        query["category"] = category
    
    tasks = await db.tasks.find(query).to_list(1000)
    return [Task(**task) for task in tasks]

@api_router.get("/tasks/today", response_model=List[Task])
async def get_today_tasks():
    today = datetime.utcnow().date()
    tomorrow = today + timedelta(days=1)
    
    query = {
        "user_id": "default_user",
        "$or": [
            {"due_date": {"$gte": datetime.combine(today, datetime.min.time()),
                         "$lt": datetime.combine(tomorrow, datetime.min.time())}},
            {"is_recurring": True}
        ]
    }
    
    tasks = await db.tasks.find(query).to_list(1000)
    return [Task(**task) for task in tasks]

@api_router.put("/tasks/{task_id}/complete")
async def complete_task(task_id: str):
    # Find task
    task_doc = await db.tasks.find_one({"id": task_id})
    if not task_doc:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = Task(**task_doc)
    
    # Update task progress
    task.current_count = min(task.current_count + 1, task.target_count)
    await db.tasks.update_one(
        {"id": task_id},
        {"$set": {"current_count": task.current_count}}
    )
    
    # Create progress entry for brick
    if task.current_count >= task.target_count:
        week_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = week_start - timedelta(days=week_start.weekday())  # Monday
        
        # Calculate brick position based on existing progress
        existing_progress = await db.progress.count_documents({
            "user_id": "default_user",
            "week_start": week_start
        })
        
        # Improved 3D positioning: proper building stacking
        # Create a foundation-first building pattern
        bricks_per_row = 7
        bricks_per_layer = bricks_per_row * 2  # 2 rows per layer
        brick_width = 60
        brick_height = 35
        brick_depth = 40
        
        layer = existing_progress // bricks_per_layer
        position_in_layer = existing_progress % bricks_per_layer
        row_in_layer = position_in_layer // bricks_per_row
        col_in_row = position_in_layer % bricks_per_row
        
        # Calculate position with proper stacking
        brick_position = {
            "x": (col_in_row * brick_width) - (bricks_per_row * brick_width / 2) + (brick_width / 2),  # Center the building
            "y": -(layer * brick_height),  # Stack upward (negative Y goes up in CSS)
            "z": (row_in_layer * brick_depth) - brick_depth  # Two rows deep per layer
        }
        
        progress = Progress(
            task_id=task_id,
            week_start=week_start,
            brick_position=brick_position
        )
        await db.progress.insert_one(progress.dict())
    
    return {"message": "Task completed!", "task": task}

@api_router.put("/tasks/{task_id}/increment")
async def increment_task(task_id: str):
    task_doc = await db.tasks.find_one({"id": task_id})
    if not task_doc:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = Task(**task_doc)
    if task.current_count < task.target_count:
        task.current_count += 1
        await db.tasks.update_one(
            {"id": task_id},
            {"$set": {"current_count": task.current_count}}
        )
    
    return {"task": task}

@api_router.delete("/tasks/{task_id}")
async def delete_task(task_id: str):
    result = await db.tasks.delete_one({"id": task_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Also delete related progress
    await db.progress.delete_many({"task_id": task_id})
    return {"message": "Task deleted"}

# Progress and Structure Endpoints
@api_router.get("/structure/current-week")
async def get_current_week_structure():
    week_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = week_start - timedelta(days=week_start.weekday())
    
    progress_entries = await db.progress.find({
        "user_id": "default_user",
        "week_start": week_start
    }).to_list(1000)
    
    # Get task details for each brick
    bricks = []
    for progress in progress_entries:
        task_doc = await db.tasks.find_one({"id": progress["task_id"]})
        if task_doc:
            task = Task(**task_doc)
            bricks.append({
                "id": progress["id"],
                "task_title": task.title,
                "category": task.category,
                "position": progress["brick_position"],
                "completed_at": progress["completed_at"]
            })
    
    return {"bricks": bricks, "week_start": week_start}

@api_router.get("/stats/weekly", response_model=WeeklyStats)
async def get_weekly_stats():
    week_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = week_start - timedelta(days=week_start.weekday())
    week_end = week_start + timedelta(days=7)
    
    # Count total tasks for this week
    total_tasks = await db.tasks.count_documents({
        "user_id": "default_user",
        "$or": [
            {"due_date": {"$gte": week_start, "$lt": week_end}},
            {"is_recurring": True}
        ]
    })
    
    # Count completed tasks (bricks earned)
    bricks_earned = await db.progress.count_documents({
        "user_id": "default_user",
        "week_start": week_start
    })
    
    completion_rate = (bricks_earned / total_tasks * 100) if total_tasks > 0 else 0
    
    return WeeklyStats(
        week_start=week_start,
        total_tasks=total_tasks,
        completed_tasks=bricks_earned,
        completion_rate=round(completion_rate, 1),
        bricks_earned=bricks_earned
    )

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
