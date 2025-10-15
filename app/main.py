from fastapi import FastAPI, HTTPException, Path, Query, UploadFile, File
from .models import UploadResponse, SummaryResponse, ClearResponse
from .storage import Database

app = FastAPI()

db = Database()

@app.get("/")
async def root():
     # Provide comprehensive API summary to those hitting the root endpoint
     return {
        "status": "healthy",
        "service": "Transaction Processing API",
        "version": "1.0.0",
        "endpoints": {
            "upload": "/upload",
            "summary": "/summary/{user_id}",
            "docs": "/docs",
            "clear": "/clear"
        }
    }

@app.post("/upload", response_model=UploadResponse)
async def upload(file: UploadFile = File(...)):
    # Ensure inputted file is a csv file before attempting upload
    if not file.filename.endswith('.csv'):
        raise HTTPException(400, f"File must be CSV. Got: {file.filename}")

    # Attempt file upload
    try:
        return await db.upload_csv(file)
    
    # Catch client side error
    except ValueError as e: 
        raise HTTPException(400, detail=f"Invalid columns. {str(e)}")
    
    # Catch server side error
    except Exception as e:
        raise HTTPException(500, detail=f"Server error: {str(e)}")

@app.get("/summary/{user_id}", response_model=SummaryResponse)
async def summary(user_id: int = Path(..., ge=1, description="User ID (positive integer)"),
                start_date: str = Query(..., pattern=r'^\d{4}-\d{2}-\d{2}$', description="Start date (YYYY-MM-DD) Example: 2024-01-31"),
                end_date: str = Query(..., pattern=r'^\d{4}-\d{2}-\d{2}$', description="End date (YYYY-MM-DD) Example: 2025-12-31")):
    
    # Ensure date range has been inputted correctly - String comparison works with ISO formatting
    if start_date > end_date:
        raise HTTPException(400, f"start date ({start_date}) cannot be after end date ({end_date})")
    
    # Attempt to get summary
    try:
        return db.get_summary(user_id, start_date, end_date)
    
    # Catch transactions not found error
    except ValueError as e:
        raise HTTPException(404, detail=str(e))
    
    # Catch server side error
    except Exception as e:
        raise HTTPException(500, detail=f"Server Error: {str(e)}")
    
@app.delete("/clear", response_model=ClearResponse, description="Used for testing - Executing this endpoint will clear your database")
async def clear():
    # Ensure there is data to clear before clearing
    if not db:
        return {"success": False,
                "message": "No data to clear"}
    else:
        return db.clear()