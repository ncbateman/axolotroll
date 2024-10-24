import httpx
import asyncio
from loguru import logger
from fastapi import APIRouter, HTTPException

from models.training_request import TrainingRequest
from models.miner_task_request import MinerTaskRequest
from models.miner_task_response import MinerTaskResponse

router = APIRouter()

REAL_MINER_CURRENT_TASK_URL = "http://94.156.8.195:9002/current_training_task/"

REAL_MINER_URL = "http://94.156.8.195:9002"

async def check_real_miner_task():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(REAL_MINER_CURRENT_TASK_URL, headers={"accept": "application/json"})
            if response.status_code == 200:
                return response.json().get("current_task_id")
            else:
                logger.error(f"Error fetching task from REAL_MINER: {response.status_code}")
                return None
    except Exception as e:
        logger.error(f"Failed to connect to REAL_MINER: {str(e)}")
        return None

@router.post("/start_training/")
async def start_training(request: TrainingRequest):
    await asyncio.sleep(3)
    return {"status": "success", "message": "Training started in the background"}

@router.post("/task_offer/")
async def task_offer(request: MinerTaskRequest) -> MinerTaskResponse:
    await asyncio.sleep(3)
    real_miner_task_id = await check_real_miner_task()

    if real_miner_task_id is not None:
        if real_miner_task_id == request.task_id:
            logger.info(f"Task {request.task_id} accepted as REAL_MINER is working on the same task.")
            return MinerTaskResponse(message="Yes", accepted=True)
        else:
            logger.info(f"Task {request.task_id} rejected because REAL_MINER is working on task {real_miner_task_id}.")
            return MinerTaskResponse(message="At capacity", accepted=False)
    else:
        logger.error("Unable to determine REAL_MINER's task.")
        return MinerTaskResponse(message="At capacity", accepted=False)

@router.get("/get_latest_model_submission/{task_id}")
async def get_latest_model_submission(task_id: str) -> str:
    await asyncio.sleep(3)
    logger.info(f"Proxying request to REAL_MINER for task {task_id}")
    
    real_miner_url = f"{REAL_MINER_URL}/get_latest_model_submission/{task_id}"

    logger.info(real_miner_url)
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(real_miner_url)
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"REAL_MINER returned an error: {response.status_code}")
                raise HTTPException(status_code=response.status_code, detail="No model lol")
    
    except Exception as e:
        logger.error(f"Error connecting to REAL_MINER: {str(e)}")
        raise HTTPException(status_code=response.status_code, detail="No model lol")