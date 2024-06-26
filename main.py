from fastapi import FastAPI, HTTPException
from celery.result import AsyncResult, GroupResult
from pydantic import BaseModel
from tasks import perform_complete_analysis
import celery.states as states

app = FastAPI()

class AnalysisRequest(BaseModel):
    user_id: str

@app.post("/trigger-analysis")
async def trigger_analysis(request: AnalysisRequest):
    """
    Endpoint to trigger the analysis.
    """
    task = perform_complete_analysis.apply_async(args=[request.user_id])
    url = "http://localhost:8000/task-status/{}".format(task.id)
    return {"task_id": task.id, "Analysis started, please check the url: ": url}


@app.get("/task-status/{task_id}")
async def get_task_status(task_id: str):
    """
    Endpoint to check the status of a task.
    """
    task_result = AsyncResult(task_id)
    
    if task_result.state == states.SUCCESS:
        try:
            result = task_result.result
            return {"task_id": task_id, "status": "Completed", "result": result}
        
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    if task_result.state == states.FAILURE:
        return {"task_id": task_id, "status": "Failed", "result": str(task_result.info)}

    return {"task_id": task_id, "status": "Not Completed"}


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)
