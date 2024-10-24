import httpx
import asyncio
import redis
from loguru import logger
from fastapi import APIRouter, HTTPException

from models.training_request import TrainingRequest
from models.miner_task_request import MinerTaskRequest
from models.miner_task_response import MinerTaskResponse

router = APIRouter()

# Redis setup
r = redis.Redis(host="redis", port=6379, db=0)

# Miners' URLs
MINER_1_CURRENT_TASK_URL = "http://94.156.8.195:9002/current_training_task/"
MINER_2_CURRENT_TASK_URL = "http://94.156.8.247:9002/current_training_task/"
MINER_1_URL = "http://94.156.8.195:9002"
MINER_2_URL = "http://94.156.8.247:9002"

# Task-to-Miner Redis Key Prefix
TASK_TO_MINER_KEY = "task_to_miner"

# Helper function to check current task for a miner
async def check_miner_task(miner_task_url):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(miner_task_url, headers={"accept": "application/json"})
            if response.status_code == 200:
                return response.json().get("current_task_id")
            else:
                logger.error(f"Error fetching task from miner: {response.status_code}")
                return None
    except Exception as e:
        logger.error(f"Failed to connect to miner: {str(e)}")
        return None

# Store the task-to-miner mapping in Redis
def store_task_to_miner(task_id: str, miner: str):
    r.set(f"{TASK_TO_MINER_KEY}:{task_id}", miner)

# Retrieve the miner for a given task from Redis
def get_miner_for_task(task_id: str):
    miner = r.get(f"{TASK_TO_MINER_KEY}:{task_id}")
    return miner.decode("utf-8") if miner else None

@router.post("/start_training/")
async def start_training(request: TrainingRequest):
    await asyncio.sleep(3)
    return {"status": "success", "message": "Training started in the background"}

@router.post("/task_offer/")
async def task_offer(request: MinerTaskRequest) -> MinerTaskResponse:
    await asyncio.sleep(3)
    
    # Check Miner 1 and Miner 2 tasks
    miner_1_task_id = await check_miner_task(MINER_1_CURRENT_TASK_URL)
    miner_2_task_id = await check_miner_task(MINER_2_CURRENT_TASK_URL)

    if miner_1_task_id == request.task_id:
        # If Miner 1 is already working on the task
        logger.info(f"Task {request.task_id} accepted as Miner 1 is working on it.")
        store_task_to_miner(request.task_id, "miner_1")
        return MinerTaskResponse(message="Yes", accepted=True)

    elif miner_2_task_id == request.task_id:
        # If Miner 2 is already working on the task
        logger.info(f"Task {request.task_id} accepted as Miner 2 is working on it.")
        store_task_to_miner(request.task_id, "miner_2")
        return MinerTaskResponse(message="Yes", accepted=True)

    else:
        # Reject if neither miner is working on the task
        logger.info(f"Task {request.task_id} rejected as neither miner is working on it.")
        return MinerTaskResponse(message="At capacity", accepted=False)

@router.get("/get_latest_model_submission/{task_id}")
async def get_latest_model_submission(task_id: str) -> str:
    await asyncio.sleep(3)

    # Retrieve the miner responsible for the task
    miner = get_miner_for_task(task_id)
    if not miner:
        raise HTTPException(status_code=404, detail="No miner found for the task.")

    # Proxy the request to the correct miner
    if miner == "miner_1":
        real_miner_url = f"{MINER_1_URL}/get_latest_model_submission/{task_id}"
    elif miner == "miner_2":
        real_miner_url = f"{MINER_2_URL}/get_latest_model_submission/{task_id}"
    else:
        raise HTTPException(status_code=500, detail="Unknown miner.")

    logger.info(f"Proxying request to {miner} for task {task_id}")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(real_miner_url)
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"{miner} returned an error: {response.status_code}")
                raise HTTPException(status_code=response.status_code, detail="Error from miner.")
    
    except Exception as e:
        logger.error(f"Error connecting to {miner}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to connect to miner.")