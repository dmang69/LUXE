"""
/api/design – approved design assets.
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional
import shutil, os

from ..database import get_db
from ..auth import require_role
from .. import models

router = APIRouter(prefix="/api/design", tags=["design"])
ASSET_DIR = os.getenv("LOCAL_ASSET_DIR", "assets")
os.makedirs(ASSET_DIR, exist_ok=True)


@router.get("/approved")
def list_approved_assets(
    asset_type: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    _user=Depends(require_role("boss", "admin", "viewer")),
):
    q = db.query(models.DesignAsset).filter(models.DesignAsset.is_approved == True)
    if asset_type:
        q = q.filter(models.DesignAsset.asset_type == asset_type)
    assets = q.order_by(models.DesignAsset.created_at.desc()).limit(limit).all()
    return [_asset_dict(a) for a in assets]


@router.get("/assets/{asset_id}")
def get_asset(
    asset_id: int,
    db: Session = Depends(get_db),
    _user=Depends(require_role("boss", "admin", "viewer")),
):
    asset = db.query(models.DesignAsset).filter(models.DesignAsset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return _asset_dict(asset)


@router.post("/assets", status_code=201)
def create_asset(
    name: str = Form(...),
    asset_type: str = Form("other"),
    description: str = Form(""),
    agent_id: str = Form("manual"),
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    _admin=Depends(require_role("boss", "admin")),
):
    file_url = None
    if file:
        dest = os.path.join(ASSET_DIR, file.filename)
        with open(dest, "wb") as f:
            shutil.copyfileobj(file.file, f)
        file_url = f"/static/assets/{file.filename}"

    asset = models.DesignAsset(
        agent_id=agent_id,
        asset_type=asset_type,
        name=name,
        description=description,
        file_url=file_url,
        is_approved=True,
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return _asset_dict(asset)


@router.delete("/assets/{asset_id}", status_code=204)
def delete_asset(
    asset_id: int,
    db: Session = Depends(get_db),
    _admin=Depends(require_role("boss", "admin")),
):
    asset = db.query(models.DesignAsset).filter(models.DesignAsset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    db.delete(asset)
    db.commit()


def _asset_dict(a: models.DesignAsset) -> dict:
    return {
        "id": a.id,
        "task_id": a.task_id,
        "agent_id": a.agent_id,
        "asset_type": a.asset_type,
        "name": a.name,
        "description": a.description,
        "file_url": a.file_url,
        "thumbnail_url": a.thumbnail_url,
        "metadata": a.metadata_,
        "is_approved": a.is_approved,
        "created_at": a.created_at.isoformat() if a.created_at else None,
    }
