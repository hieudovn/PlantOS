"""Contract validation, preview and apply API."""

from fastapi import APIRouter, HTTPException
from .schemas import ContractV2
from .validator import validate_contract, generate_uns_path
from .preview import preview_contract
from .apply import apply_contract

router = APIRouter()


@router.post("/contracts/validate")
async def validate_contract_endpoint(payload: dict):
    """Validate a PlantOS Integration Contract. Does NOT write to database."""
    try:
        # Parse and validate structure via Pydantic
        contract = ContractV2(**payload)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Contract structure invalid: {e}")

    # Cross-reference validation
    contract_dict = contract.model_dump()
    result = validate_contract(contract_dict)

    # Generate UNS paths for each signal
    asset_map = {a["asset_id"]: a for a in contract_dict["assets"]}
    area_map = {a["area_id"]: a for a in contract_dict["areas"]}
    uns_paths = {}
    for sig in contract_dict["signals"]:
        asset = asset_map.get(sig["asset_id"])
        if asset:
            area = area_map.get(asset["area_id"])
            if area:
                path = generate_uns_path(
                    sig, area, asset,
                    contract_dict["plant"],
                    contract_dict["uns"]
                )
                uns_paths[sig["signal_id"]] = path

    return {
        "valid": result.valid,
        "errors": result.errors,
        "warnings": result.warnings,
        "summary": {
            "plants": 1,
            "areas": len(contract_dict["areas"]),
            "assets": len(contract_dict["assets"]),
            "signals": len(contract_dict["signals"]),
        },
        "uns_paths": uns_paths,
    }


@router.post("/contracts/apply")
async def apply_contract_endpoint(payload: dict):
    """Apply contract import — writes to database.

    The import_policy MUST be provided in the request body (not from contract).
    Default policy is safest possible: on_conflict=fail, no deletes, no overwrites.
    """
    # 1. Parse contract
    contract_data = payload.get("contract", payload)
    try:
        contract = ContractV2(**contract_data)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Contract invalid: {e}")

    # 2. Parse import policy (from request, NOT contract)
    import_policy = payload.get("import_policy", {})
    mode = import_policy.get("mode", "")
    if mode != "apply":
        raise HTTPException(
            status_code=400,
            detail=(
                f"import_policy.mode must be 'apply' to execute import. Got: '{mode}'. "
                f"Use preview first to review changes."
            ),
        )

    contract_dict = contract.model_dump()

    # 3. Validate
    validation = validate_contract(contract_dict)
    if not validation.valid:
        return {
            "applied": False,
            "validation_errors": validation.errors,
            "result": None,
        }

    # 4. Apply
    result = apply_contract(contract_dict, import_policy)

    return {
        "applied": result.success,
        "errors": result.errors,
        "result": {
            "created": result.created,
            "updated": result.updated,
            "skipped": result.skipped,
            "orphaned": result.orphaned,
            "deactivated": result.deactivated,
        },
        "summary": {
            "total_created": sum(len(v) for v in result.created.values()),
            "total_updated": sum(len(v) for v in result.updated.values()),
            "total_skipped": sum(len(v) for v in result.skipped.values()),
            "total_orphaned": sum(len(v) for v in result.orphaned.values()),
        },
    }


@router.post("/contracts/preview")
async def preview_contract_endpoint(payload: dict):
    """Preview import — compare contract against DB. Does NOT write."""
    try:
        contract = ContractV2(**payload)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Contract structure invalid: {e}")

    contract_dict = contract.model_dump()

    # Run validator first (reuse 7-01 logic)
    validation = validate_contract(contract_dict)
    if not validation.valid:
        return {
            "valid": False,
            "validation_errors": validation.errors,
            "validation_warnings": validation.warnings,
            "changes": None,
        }

    # Run preview
    preview = preview_contract(contract_dict)

    return {
        "valid": True,
        "validation_warnings": validation.warnings,
        "changes": {
            "plants": {
                "create": preview.plants.creates,
                "update": preview.plants.updates,
                "conflict": preview.plants.conflicts,
                "orphan": preview.plants.orphans,
            },
            "areas": {
                "create": preview.areas.creates,
                "update": preview.areas.updates,
                "conflict": preview.areas.conflicts,
                "orphan": preview.areas.orphans,
            },
            "assets": {
                "create": preview.assets.creates,
                "update": preview.assets.updates,
                "conflict": preview.assets.conflicts,
                "orphan": preview.assets.orphans,
            },
            "signals": {
                "create": preview.signals.creates,
                "update": preview.signals.updates,
                "conflict": preview.signals.conflicts,
                "orphan": preview.signals.orphans,
            },
        },
        "summary": {
            "total_creates": (
                len(preview.plants.creates)
                + len(preview.areas.creates)
                + len(preview.assets.creates)
                + len(preview.signals.creates)
            ),
            "total_updates": (
                len(preview.plants.updates)
                + len(preview.areas.updates)
                + len(preview.assets.updates)
                + len(preview.signals.updates)
            ),
            "total_conflicts": (
                len(preview.plants.conflicts)
                + len(preview.areas.conflicts)
                + len(preview.assets.conflicts)
                + len(preview.signals.conflicts)
            ),
            "total_orphans": (
                len(preview.plants.orphans)
                + len(preview.areas.orphans)
                + len(preview.signals.orphans)
            ),
        },
    }
