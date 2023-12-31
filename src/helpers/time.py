from fastapi import Request, HTTPException
from datetime import datetime
import time
import random

import helpers.config as config

async def anti_timing_att(request: Request, call_next):
    config_ = config.get_settings()
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    if config_.time_attack:
        if config_.time_attack.method == "stall":
            # if stall is used slow fast callbacks 
            # to a minimum response time defined by magnitude
            if process_time < config_.time_attack.magnitude:
                time.sleep(config_.time_attack.magnitude - process_time)
        elif config_.time_attack.method == "jitter":
            # if jitter is used it just adds some time 
            # between 0 and magnitude secs
            time.sleep(config_.time_attack.magnitude*random.uniform(0, 1))
            
    return response
