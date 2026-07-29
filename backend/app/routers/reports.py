"""
Quarterly market report endpoints for MOG division KPI.
Generates Word documents with price statistics, product trends, and market developments.
"""
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db import get_db
from app.auth import get_current_user, get_current_admin
from app.report_generator import (
    generate_quarterly_report,
    save_quarterly_report,
    list_generated_reports,
    get_benchmark_stats,
    get_product_stats,
)
from app.config import QUARTER_MONTHS

router = APIRouter(prefix="/api/reports", tags=["reports"], dependencies=[Depends(get_current_user)])


class ReportPreviewRequest(BaseModel):
    year: int
    quarter: str


class ReportPreviewResponse(BaseModel):
    year: int
    quarter: str
    benchmarks: List[dict]
    products: List[dict]


class ReportGenerateRequest(BaseModel):
    year: int
    quarter: str
    outlook_notes: str = ""
    generated_by: str = "MOG Analyst"


@router.post("/preview", response_model=ReportPreviewResponse)
def preview_quarterly_report(req: ReportPreviewRequest, db: Session = Depends(get_db)):
    """Preview benchmark and product stats for a quarterly report (no file generated)."""
    if req.quarter not in QUARTER_MONTHS:
        raise HTTPException(status_code=400, detail=f"Invalid quarter: {req.quarter}")
    
    b_stats = get_benchmark_stats(db, req.year, req.quarter)
    p_stats = get_product_stats(db, req.year, req.quarter)
    
    return ReportPreviewResponse(
        year=req.year,
        quarter=req.quarter,
        benchmarks=b_stats,
        products=p_stats,
    )


@router.post("/generate", dependencies=[Depends(get_current_admin)])
def generate_and_save_report(req: ReportGenerateRequest, db: Session = Depends(get_db)):
    """Generate and save a quarterly report to disk."""
    if req.quarter not in QUARTER_MONTHS:
        raise HTTPException(status_code=400, detail=f"Invalid quarter: {req.quarter}")
    
    try:
        filepath = save_quarterly_report(
            db,
            year=req.year,
            quarter=req.quarter,
            outlook_notes=req.outlook_notes,
            generated_by=req.generated_by,
        )
        return {
            "status": "success",
            "filename": filepath.name,
            "path": str(filepath),
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as ex:
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(ex)}")


@router.get("/list")
def list_reports():
    """List all generated quarterly reports."""
    reports = list_generated_reports()
    return {
        "reports": [
            {
                "filename": r.name,
                "size": r.stat().st_size,
                "created": datetime.fromtimestamp(r.stat().st_mtime).isoformat(),
            }
            for r in reports
        ]
    }


@router.get("/download/{filename}", dependencies=[Depends(get_current_admin)])
def download_report(filename: str):
    """Download a generated quarterly report."""
    try:
        filepath = None
        for report in list_generated_reports():
            if report.name == filename:
                filepath = report
                break
        
        if not filepath or not filepath.exists():
            raise HTTPException(status_code=404, detail=f"Report not found: {filename}")
        
        return FileResponse(
            filepath,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            filename=filename,
        )
    except HTTPException:
        raise
    except Exception as ex:
        raise HTTPException(status_code=500, detail=f"Failed to download report: {str(ex)}")
