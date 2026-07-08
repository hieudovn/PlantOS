"""Processing API routes — profile CRUD, preview, signal assignment."""

import logging
from datetime import datetime, timezone

from aiohttp import web

from agent.processing.profiles import (
    ProcessingProfile, ProcessingStep, MVP_STEP_TYPES,
)

logger = logging.getLogger(__name__)


def register_processing_routes(app: web.Application, engine, config):
    """Register all processing-related API routes."""

    # ---- 3.13 GET /api/processing/profiles — list all profiles --------------
    async def list_profiles(request: web.Request) -> web.Response:
        profiles = engine.list_profiles()
        return web.json_response([
            {
                "profile_id": p.profile_id,
                "name": p.name,
                "description": p.description,
                "step_count": len(p.steps),
                "steps": [
                    {"type": s.type, "params": s.params, "order": s.order, "enabled": s.enabled}
                    for s in p.steps
                ],
                "created_at": p.created_at.isoformat() if p.created_at else None,
                "updated_at": p.updated_at.isoformat() if p.updated_at else None,
            }
            for p in profiles
        ])

    # ---- 3.14 POST /api/processing/profiles — create profile -----------------
    async def create_profile(request: web.Request) -> web.Response:
        try:
            body = await request.json()
        except Exception:
            return web.json_response({"error": "Invalid JSON"}, status=400)

        profile_id = body.get("profile_id", "")
        if not profile_id:
            return web.json_response({"error": "Missing 'profile_id'"}, status=400)

        if engine.get_profile(profile_id):
            return web.json_response({"error": "Profile already exists"}, status=409)

        steps_data = body.get("steps", [])
        steps = []
        for i, s in enumerate(steps_data):
            step_type = s.get("type", "")
            if step_type not in MVP_STEP_TYPES:
                return web.json_response(
                    {"error": f"Unknown step type: '{step_type}'. Must be one of: {list(MVP_STEP_TYPES.keys())}"},
                    status=400,
                )
            steps.append(ProcessingStep(
                type=step_type,
                params=s.get("params", {}),
                order=s.get("order", i),
                enabled=s.get("enabled", True),
            ))

        now = datetime.now(timezone.utc)
        profile = ProcessingProfile(
            profile_id=profile_id,
            name=body.get("name", profile_id),
            description=body.get("description", ""),
            steps=steps,
            created_at=now,
            updated_at=now,
        )
        engine.add_profile(profile)
        return web.json_response({"status": "created", "profile_id": profile_id})

    # ---- 3.15 GET /api/processing/profiles/{id} — get profile detail ---------
    async def get_profile(request: web.Request) -> web.Response:
        profile_id = request.match_info.get("id", "")
        profile = engine.get_profile(profile_id)
        if not profile:
            return web.json_response({"error": "Profile not found"}, status=404)

        signals = engine.list_signals_for_profile(profile_id)
        return web.json_response({
            "profile_id": profile.profile_id,
            "name": profile.name,
            "description": profile.description,
            "steps": [
                {"type": s.type, "params": s.params, "order": s.order, "enabled": s.enabled}
                for s in profile.steps
            ],
            "assigned_signals": signals,
            "created_at": profile.created_at.isoformat() if profile.created_at else None,
            "updated_at": profile.updated_at.isoformat() if profile.updated_at else None,
        })

    # ---- 3.16 PUT /api/processing/profiles/{id} — update profile -------------
    async def update_profile(request: web.Request) -> web.Response:
        profile_id = request.match_info.get("id", "")
        profile = engine.get_profile(profile_id)
        if not profile:
            return web.json_response({"error": "Profile not found"}, status=404)

        try:
            body = await request.json()
        except Exception:
            return web.json_response({"error": "Invalid JSON"}, status=400)

        if "name" in body:
            profile.name = body["name"]
        if "description" in body:
            profile.description = body["description"]
        if "steps" in body:
            steps_data = body["steps"]
            new_steps = []
            for i, s in enumerate(steps_data):
                step_type = s.get("type", "")
                if step_type not in MVP_STEP_TYPES:
                    return web.json_response(
                        {"error": f"Unknown step type: '{step_type}'"},
                        status=400,
                    )
                new_steps.append(ProcessingStep(
                    type=step_type,
                    params=s.get("params", {}),
                    order=s.get("order", i),
                    enabled=s.get("enabled", True),
                ))
            profile.steps = new_steps

        engine.add_profile(profile)  # triggers updated_at refresh
        return web.json_response({"status": "updated", "profile_id": profile_id})

    # ---- 3.17 DELETE /api/processing/profiles/{id} — delete profile ----------
    async def delete_profile(request: web.Request) -> web.Response:
        profile_id = request.match_info.get("id", "")
        signals = engine.list_signals_for_profile(profile_id)
        if signals:
            return web.json_response({
                "error": "Cannot delete profile: signals are assigned",
                "assigned_signals": signals,
            }, status=409)

        if engine.delete_profile(profile_id):
            return web.json_response({"status": "deleted"})
        return web.json_response({"error": "Profile not found"}, status=404)

    # ---- 3.18 POST /api/processing/profiles/{id}/preview — preview -----------
    async def preview_profile(request: web.Request) -> web.Response:
        profile_id = request.match_info.get("id", "")
        profile = engine.get_profile(profile_id)
        if not profile:
            return web.json_response({"error": "Profile not found"}, status=404)

        try:
            body = await request.json()
        except Exception:
            return web.json_response({"error": "Invalid JSON"}, status=400)

        raw_samples = body.get("raw_samples", [])
        if not raw_samples:
            return web.json_response({"error": "Missing 'raw_samples' (list of floats)"}, status=400)

        result = engine.preview(raw_samples, profile)
        return web.json_response(result)

    # ---- 3.19 GET /api/processing/profiles/{id}/signals — list assigned sigs --
    async def list_profile_signals(request: web.Request) -> web.Response:
        profile_id = request.match_info.get("id", "")
        signals = engine.list_signals_for_profile(profile_id)
        return web.json_response(signals)

    # ---- Step type metadata --------------------------------------------------
    async def list_step_types(request: web.Request) -> web.Response:
        """Return available step types (7 MVP + 8 Coming Soon)."""
        from agent.processing.profiles import COMING_SOON_STEPS
        mvp = [
            {"type": k, "name": v["name"], "description": v["description"],
             "params": v["params"], "available": True}
            for k, v in MVP_STEP_TYPES.items()
        ]
        coming_soon = [
            {"type": s, "name": s.replace("_", " ").title(), "available": False}
            for s in COMING_SOON_STEPS
        ]
        return web.json_response({"mvp": mvp, "coming_soon": coming_soon})

    # ---- Assign profile to signal (via config) --------------------------------
    async def assign_profile(request: web.Request) -> web.Response:
        try:
            body = await request.json()
        except Exception:
            return web.json_response({"error": "Invalid JSON"}, status=400)

        signal_id = body.get("signal_id", "")
        profile_id = body.get("profile_id", "")

        if not signal_id:
            return web.json_response({"error": "Missing 'signal_id'"}, status=400)

        if profile_id and not engine.get_profile(profile_id):
            return web.json_response({"error": "Profile not found"}, status=404)

        engine.assign_profile(signal_id, profile_id or None)

        # Also save assignment in config
        assignments = config._data.setdefault("processing_assignments", {})
        if profile_id:
            assignments[signal_id] = profile_id
        else:
            assignments.pop(signal_id, None)
        config._save()

        return web.json_response({"status": "assigned", "signal_id": signal_id, "profile_id": profile_id})

    # ---- Get assignment for a signal -----------------------------------------
    async def get_assignment(request: web.Request) -> web.Response:
        signal_id = request.query.get("signal_id", "")
        if not signal_id:
            return web.json_response({"error": "Missing 'signal_id' query param"}, status=400)
        profile_id = engine._signal_profiles.get(signal_id)
        return web.json_response({"signal_id": signal_id, "profile_id": profile_id})

    # Register routes
    app.router.add_get("/api/processing/profiles", list_profiles)
    app.router.add_post("/api/processing/profiles", create_profile)
    app.router.add_get("/api/processing/profiles/{id}", get_profile)
    app.router.add_put("/api/processing/profiles/{id}", update_profile)
    app.router.add_delete("/api/processing/profiles/{id}", delete_profile)
    app.router.add_post("/api/processing/profiles/{id}/preview", preview_profile)
    app.router.add_get("/api/processing/profiles/{id}/signals", list_profile_signals)
    app.router.add_get("/api/processing/step-types", list_step_types)
    app.router.add_post("/api/processing/assign", assign_profile)
    app.router.add_get("/api/processing/assign", get_assignment)
