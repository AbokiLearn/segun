# utils.py
#
# Utility functions for bot.

from telegram import Bot, File
import requests
import aiohttp
import asyncio

from typing import Dict, Tuple
import time

from settings import config, TMP_DIR
from main import logger


def create_tmpfile(file: File) -> str:
    """Construct temporary file path"""
    uid = file.file_unique_id
    ext = file.file_path.split('.')[-1]
    return f"{TMP_DIR}/{uid}.{ext}"


async def submit_transcription_job(file_path: str) -> str:
    """Submit a transcription job to the Inference server asynchronously
    
    @param file_path: Path to the audio file to transcribe
    @return: The call_id of the transcription job
    """
    
    url = f"{config.INFERENCE_URL}/transcribe"
    headers = {"Authorization": f"Bearer {config.ACCESS_TOKEN}"}
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, data={'file': open(file_path, 'rb')}) as response:
            response_json = await response.json()
            return response_json['call_id']


async def check_job_status(
    call_id: str, chat_id: int, message_id: int, bot: Bot
) -> bool | Tuple[str, Dict]:
    """Check the status of a job running on the Inference server asynchronously
    
    @param call_id: The call_id of the job to check
    @return: If the job is running, return False. If the job is complete, return the transcript and timestamps
    """

    url = f"{config.INFERENCE_URL}/status/{call_id}"
    async with aiohttp.ClientSession() as session:
        while True:
            async with session.get(url) as response:
                response_json = await response.json()
                if response_json['status'] == 'running':
                    await asyncio.sleep(1)  # Wait for a second before polling again
                elif response_json['status'] == 'complete':
                    transcript = response_json['transcript']
                    logger.info(f"Received results for call_id {call_id}") 
                    await bot.send_message(
                        chat_id=chat_id,
                        reply_to_message_id=message_id,
                        text=f"Here's what I heard:\n\n{transcript}"
                    )
                    return
                else:
                    raise ValueError("Unexpected status received")
