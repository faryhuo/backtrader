"""
Strategy management routes.

Handles:
- Strategy CRUD operations
- Strategy template management
- Strategy version management
"""
import logging

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from src.service.backtest_engine import (
    get_user_strategy_code,
    save_user_strategy_code,
    list_strategies,
    StrategyLoadError,
    extract_strategy_params,
)
from src.db.storage.strategy_version import StrategyVersionStorage
from src.routes.common.dependencies import get_version_storage
from src.routes.common.auth_dependencies import get_optional_user_id
from src.service.version_service import compare_versions
from src.service.strategy_sandbox import execute_strategy_code, StrategySandboxError
from src.service.strategy_templates import (
    get_all_templates,
    get_template_by_id,
    get_categories,
    get_difficulty_levels,
)

logger = logging.getLogger(__name__)
router = APIRouter()


# ========== Pydantic Models ==========


class StrategyCode(BaseModel):
    name: str
    code: str


class StrategySaveRequest(BaseModel):
    name: str
    code: str
    commit_message: str | None = None


class StrategyValidateRequest(BaseModel):
    name: str | None = None
    code: str


class TemplateImportRequest(BaseModel):
    template_id: str
    name: str  # New strategy name


class VersionCreateRequest(BaseModel):
    commit_message: str | None = None


# ========== Strategy CRUD Endpoints ==========


@router.get("/strategies")
def get_strategy_list(user_id: str = Depends(get_optional_user_id)) -> dict:
    try:
        names = list_strategies()
        return {"strategies": names}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/strategy")
def get_strategy(
    name: str | None = None,
    user_id: str = Depends(get_optional_user_id),
) -> dict:
    try:
        if not name:
            names = list_strategies()
            if not names:
                raise HTTPException(status_code=404, detail="No strategies available")
            name = names[0]
        code = get_user_strategy_code(name)
        return {"code": code, "name": name}
    except StrategyLoadError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/strategy")
def save_strategy(
    request: StrategySaveRequest,
    user_id: str = Depends(get_optional_user_id),
) -> dict:
    try:
        # Save to file system
        save_user_strategy_code(request.name, request.code)

        # Create version record (non-blocking, errors logged)
        version_info = None
        try:
            storage = get_version_storage()
            version_info = storage.create_version(
                strategy_name=request.name,
                code=request.code,
                user_id=user_id,
                commit_message=request.commit_message
            )
        except Exception as e:
            logger.error(f"Failed to create version record: {e}", exc_info=True)
        
        response = {
            "status": "ok",
            "message": "Strategy saved",
            "name": request.name
        }
        
        if version_info:
            response["version"] = version_info
        
        return response
    except StrategyLoadError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/strategy/validate")
def validate_strategy(
    request: StrategyValidateRequest,
    user_id: str = Depends(get_optional_user_id),
) -> dict:
    """
    Validate strategy code without saving it.

    Checks:
    - Python syntax / sandbox compilation
    - Presence of UserStrategy class
    - UserStrategy inheritance from backtrader.Strategy
    """
    try:
        module_name = request.name or "unsaved_strategy"
        module_globals = execute_strategy_code(
            request.code,
            module_name=f"strategy_validate_{module_name}",
            filename=f"{module_name}.py",
        )
        strategy_cls = module_globals.get("UserStrategy")

        if strategy_cls is None:
            raise HTTPException(status_code=400, detail="UserStrategy class not found in strategy code")

        import backtrader as bt

        if not issubclass(strategy_cls, bt.Strategy):
            raise HTTPException(status_code=400, detail="UserStrategy must inherit from backtrader.Strategy")

        return {
            "status": "ok",
            "valid": True,
            "message": "Strategy compiled successfully",
            "strategy_class": strategy_cls.__name__,
        }
    except HTTPException:
        raise
    except StrategySandboxError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except SyntaxError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/strategy/{name}/params")
def get_strategy_params(
    name: str,
    user_id: str = Depends(get_optional_user_id),
) -> dict:
    """
    Get parameters defined in a strategy file.
    Returns a list of parameter objects with name, value, and type.
    If extraction fails, returns empty params array (no error).
    
    Example response:
    {
        "name": "grid_trading",
        "params": [
            {"name": "grid_count", "value": 10, "type": "int"},
            {"name": "upper_price", "value": 110.0, "type": "float"},
            {"name": "lower_price", "value": 90.0, "type": "float"},
            {"name": "total_investment", "value": 10000.0, "type": "float"}
        ]
    }
    """
    try:
        params = extract_strategy_params(name)
        return {"name": name, "params": params}
    except Exception as exc:
        # Log the error but return empty params instead of failing
        logger.warning(f"Failed to extract params for strategy '{name}': {exc}")
        return {"name": name, "params": []}


# ========== Strategy Template Endpoints ==========


@router.get("/templates")
def get_templates(user_id: str = Depends(get_optional_user_id)) -> dict:
    """Get all strategy templates with metadata."""
    try:
        templates = get_all_templates()
        categories = get_categories()
        difficulties = get_difficulty_levels()
        return {
            "templates": templates,
            "categories": categories,
            "difficulties": difficulties,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/templates/{template_id}")
def get_template_detail(
    template_id: str,
    user_id: str = Depends(get_optional_user_id),
) -> dict:
    """Get template detail including code."""
    try:
        template = get_template_by_id(template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        return template
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/templates/import")
def import_template(
    request: TemplateImportRequest,
    user_id: str = Depends(get_optional_user_id),
) -> dict:
    """Import a template as a new strategy."""
    try:
        # Get template
        template = get_template_by_id(request.template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        # Validate name
        if not request.name or not request.name.strip():
            raise HTTPException(status_code=400, detail="Strategy name is required")
        
        # Check if strategy already exists
        existing = list_strategies()
        if request.name in existing:
            raise HTTPException(status_code=400, detail=f"Strategy '{request.name}' already exists")
        
        # Save as new strategy
        code = template.get("code", "")
        if not code:
            raise HTTPException(status_code=500, detail="Template code is empty")
        
        save_user_strategy_code(request.name, code)
        
        return {
            "status": "ok",
            "message": f"Template imported as '{request.name}'",
            "name": request.name,
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ========== Strategy Version Management Endpoints ==========


@router.get("/strategy/{name}/versions")
def list_strategy_versions(
    name: str,
    limit: int = 50,
    offset: int = 0,
    user_id: str = Depends(get_optional_user_id),
) -> dict:
    """
    List all versions of a strategy.

    Returns version history sorted by version number descending (newest first).
    """
    storage = get_version_storage()

    return storage.list_versions(
        strategy_name=name,
        user_id=user_id,
        limit=limit,
        offset=offset
    )


@router.get("/strategy/{name}/versions/latest")
def get_latest_strategy_version(
    name: str,
    user_id: str = Depends(get_optional_user_id),
) -> dict:
    """
    Get the most recent version of a strategy.
    """
    storage = get_version_storage()

    version = storage.get_latest_version(name, user_id=user_id)

    if not version:
        raise HTTPException(status_code=404, detail="No versions found for this strategy")

    return version


@router.get("/strategy/{name}/versions/compare")
def compare_strategy_versions(
    name: str,
    from_version: int,
    to_version: int,
    user_id: str = Depends(get_optional_user_id),
) -> dict:
    """
    Compare two versions and return a unified diff.

    Args:
        name: Strategy name
        from_version: Older version number
        to_version: Newer version number

    Returns:
        Unified diff and change statistics
    """
    storage = get_version_storage()

    # Get both versions
    old_version = storage.get_version(name, from_version, user_id=user_id)
    new_version = storage.get_version(name, to_version, user_id=user_id)
    
    if not old_version:
        raise HTTPException(
            status_code=404,
            detail=f"Version {from_version} not found"
        )
    if not new_version:
        raise HTTPException(
            status_code=404,
            detail=f"Version {to_version} not found"
        )
    
    # Generate comparison
    return compare_versions(
        old_code=old_version["code"],
        new_code=new_version["code"],
        old_version=from_version,
        new_version=to_version
    )


@router.get("/strategy/{name}/versions/{version_number}")
def get_strategy_version(
    name: str,
    version_number: int,
    user_id: str = Depends(get_optional_user_id),
) -> dict:
    """
    Get a specific version of a strategy.

    Returns full version details including the code snapshot.
    """
    storage = get_version_storage()

    version = storage.get_version(name, version_number, user_id=user_id)

    if not version:
        raise HTTPException(status_code=404, detail="Version not found")

    return version


@router.post("/strategy/{name}/versions/{version_number}/rollback")
def rollback_to_version(
    name: str,
    version_number: int,
    request: VersionCreateRequest = None,
    user_id: str = Depends(get_optional_user_id),
) -> dict:
    """
    Rollback a strategy to a specific version.

    This creates a new version with the content from the specified version,
    preserving the full version history (audit trail).
    """
    storage = get_version_storage()

    # Get the target version
    target_version = storage.get_version(name, version_number, user_id=user_id)
    
    if not target_version:
        raise HTTPException(status_code=404, detail="Version not found")
    
    # Create a new version with the old code
    commit_message = (
        request.commit_message if request and request.commit_message
        else f"Rollback to version {version_number}"
    )
    
    # Save to file system
    save_user_strategy_code(name, target_version["code"])
    
    # Create new version record
    new_version = storage.create_version(
        strategy_name=name,
        code=target_version["code"],
        user_id=user_id,
        commit_message=commit_message
    )
    
    return {
        "status": "ok",
        "message": f"Rolled back to version {version_number}",
        "new_version": new_version
    }
