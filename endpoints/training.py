import httpx
import asyncio
from loguru import logger
from fastapi import APIRouter

from models.training_request import TrainingRequest
from models.miner_task_request import MinerTaskRequest
from models.miner_task_response import MinerTaskResponse

router = APIRouter()

MINER_1_CURRENT_TASK_URL = "http://94.156.8.195:9002/current_training_task/"
MINER_2_CURRENT_TASK_URL = "http://94.156.8.247:9002/current_training_task/"
MINER_1_URL = "http://94.156.8.195:9002"
MINER_2_URL = "http://94.156.8.247:9002"


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

@router.post("/start_training/")
async def start_training(request: TrainingRequest):
    await asyncio.sleep(3)
    return {"status": "success", "message": "Training started in the background"}

@router.post("/task_offer/")
async def task_offer(request: MinerTaskRequest) -> MinerTaskResponse:
    await asyncio.sleep(3)
    
    miner_1_task_id = await check_miner_task(MINER_1_CURRENT_TASK_URL)
    miner_2_task_id = await check_miner_task(MINER_2_CURRENT_TASK_URL)

    if miner_1_task_id == request.task_id:
        logger.info(f"Task {request.task_id} accepted as Miner 1 is working on it.")
        return MinerTaskResponse(message="Yes", accepted=True)

    elif miner_2_task_id == request.task_id:
        logger.info(f"Task {request.task_id} accepted as Miner 2 is working on it.")
        return MinerTaskResponse(message="Yes", accepted=True)

    else:
        logger.info(f"Task {request.task_id} rejected as neither miner is working on it.")
        return MinerTaskResponse(message="At capacity", accepted=False)

@router.get("/get_latest_model_submission/{task_id}")
async def get_latest_model_submission(task_id: str) -> str:
    await asyncio.sleep(3)
    return f"ncbateman/tuning-miner-testbed-{task_id}"