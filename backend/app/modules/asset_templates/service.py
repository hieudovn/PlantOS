"""Asset Template & Binding — Service layer."""

from app.db import get_session
from app.modules.asset_templates.models import AssetTemplate, AssetAttributeBinding
from app.modules.asset_templates.schemas import (
    TemplateCreate, TemplateUpdate, TemplateResponse,
    BindingCreate, BindingResponse, ValidationSummary,
)
from app.modules.signals.models import Signal

# ---- Default templates for seeding ----

DEFAULT_TEMPLATES = [
    TemplateCreate(
        template_id="pump_template_v1",
        name="Pump Template",
        asset_type="pump",
        asset_role="equipment",
        description="Standard pump with flow, pressure, motor, and vibration monitoring",
        domain_type="rotating",
        attributes=[
            {"name": "flow_rate", "display_name": "Flow Rate", "required": True, "data_type": "float", "unit": "m3/h", "category": "measurement"},
            {"name": "discharge_pressure", "display_name": "Discharge Pressure", "required": True, "data_type": "float", "unit": "kPa", "category": "measurement"},
            {"name": "suction_pressure", "display_name": "Suction Pressure", "required": False, "data_type": "float", "unit": "kPa", "category": "measurement"},
            {"name": "motor_current", "display_name": "Motor Current", "required": False, "data_type": "float", "unit": "A", "category": "measurement"},
            {"name": "vibration", "display_name": "Vibration", "required": False, "data_type": "float", "unit": "mm/s", "category": "measurement"},
            {"name": "bearing_temperature", "display_name": "Bearing Temperature", "required": False, "data_type": "float", "unit": "C", "category": "measurement"},
            {"name": "running_status", "display_name": "Running Status", "required": False, "data_type": "bool", "unit": None, "category": "status"},
        ],
    ),
    TemplateCreate(
        template_id="filter_template_v1",
        name="Filter Template",
        asset_type="filter",
        asset_role="equipment",
        description="Standard filter with differential pressure and flow monitoring",
        domain_type="process",
        attributes=[
            {"name": "filter_dp", "display_name": "Differential Pressure", "required": True, "data_type": "float", "unit": "kPa", "category": "measurement"},
            {"name": "effluent_flow", "display_name": "Effluent Flow", "required": True, "data_type": "float", "unit": "m3/h", "category": "measurement"},
            {"name": "influent_turbidity", "display_name": "Influent Turbidity", "required": False, "data_type": "float", "unit": "NTU", "category": "measurement"},
            {"name": "effluent_turbidity", "display_name": "Effluent Turbidity", "required": False, "data_type": "float", "unit": "NTU", "category": "measurement"},
            {"name": "backwash_status", "display_name": "Backwash Status", "required": False, "data_type": "bool", "unit": None, "category": "status"},
        ],
    ),
    TemplateCreate(
        template_id="tank_template_v1",
        name="Tank Template",
        asset_type="tank",
        asset_role="equipment",
        description="Standard tank with level and flow monitoring",
        domain_type="process",
        attributes=[
            {"name": "level", "display_name": "Level", "required": True, "data_type": "float", "unit": "m", "category": "measurement"},
            {"name": "inlet_flow", "display_name": "Inlet Flow", "required": False, "data_type": "float", "unit": "m3/h", "category": "measurement"},
            {"name": "outlet_flow", "display_name": "Outlet Flow", "required": False, "data_type": "float", "unit": "m3/h", "category": "measurement"},
            {"name": "temperature", "display_name": "Temperature", "required": False, "data_type": "float", "unit": "C", "category": "measurement"},
        ],
    ),
    TemplateCreate(
        template_id="motor_template_v1",
        name="Motor Template",
        asset_type="motor",
        asset_role="component",
        description="Standard electric motor monitoring",
        domain_type="rotating",
        attributes=[
            {"name": "running_status", "display_name": "Running Status", "required": True, "data_type": "bool", "unit": None, "category": "status"},
            {"name": "motor_current", "display_name": "Motor Current", "required": False, "data_type": "float", "unit": "A", "category": "measurement"},
            {"name": "speed", "display_name": "Speed", "required": False, "data_type": "float", "unit": "RPM", "category": "measurement"},
            {"name": "winding_temp", "display_name": "Winding Temperature", "required": False, "data_type": "float", "unit": "C", "category": "measurement"},
        ],
    ),
    TemplateCreate(
        template_id="sensor_array_template_v1",
        name="Sensor Array Template",
        asset_type="sensor_array",
        asset_role="component",
        description="Multi-sensor measurement station — all attributes optional",
        domain_type="instrumentation",
        attributes=[
            {"name": "measurement_1", "display_name": "Measurement 1", "required": False, "data_type": "float", "unit": None, "category": "measurement"},
            {"name": "measurement_2", "display_name": "Measurement 2", "required": False, "data_type": "float", "unit": None, "category": "measurement"},
            {"name": "measurement_3", "display_name": "Measurement 3", "required": False, "data_type": "float", "unit": None, "category": "measurement"},
            {"name": "status_1", "display_name": "Status 1", "required": False, "data_type": "bool", "unit": None, "category": "status"},
        ],
    ),
    TemplateCreate(
        template_id="generic_equipment_template_v1",
        name="Generic Equipment Template",
        asset_type="custom_equipment",
        asset_role="equipment",
        description="Generic equipment with basic status and custom fields",
        domain_type="generic",
        attributes=[
            {"name": "running_status", "display_name": "Running Status", "required": True, "data_type": "bool", "unit": None, "category": "status"},
            {"name": "custom_1", "display_name": "Custom 1", "required": False, "data_type": "float", "unit": None, "category": "measurement"},
            {"name": "custom_2", "display_name": "Custom 2", "required": False, "data_type": "float", "unit": None, "category": "measurement"},
            {"name": "custom_3", "display_name": "Custom 3", "required": False, "data_type": "float", "unit": None, "category": "measurement"},
        ],
    ),
]


# ---- Template Service ----

class TemplateService:
    def create(self, data: TemplateCreate) -> TemplateResponse:
        with get_session() as session:
            existing = session.get(AssetTemplate, data.template_id)
            if existing:
                raise ValueError(f"Template '{data.template_id}' already exists")
            template = AssetTemplate(
                template_id=data.template_id,
                name=data.name,
                asset_type=data.asset_type,
                asset_role=data.asset_role,
                description=data.description,
                attributes_json=[a.model_dump() for a in data.attributes],
                domain_type=data.domain_type,
                status="active",
            )
            session.add(template)
            session.commit()
            session.refresh(template)
            return _template_to_response(template)

    def get(self, template_id: str) -> TemplateResponse:
        with get_session() as session:
            template = session.get(AssetTemplate, template_id)
            if not template:
                raise ValueError(f"Template '{template_id}' not found")
            return _template_to_response(template)

    def list_all(self) -> list[TemplateResponse]:
        with get_session() as session:
            from sqlalchemy import select
            templates = session.scalars(select(AssetTemplate).order_by(AssetTemplate.name)).all()
            return [_template_to_response(t) for t in templates]

    def update(self, template_id: str, data: TemplateUpdate) -> TemplateResponse:
        with get_session() as session:
            template = session.get(AssetTemplate, template_id)
            if not template:
                raise ValueError(f"Template '{template_id}' not found")
            update_data = data.model_dump(exclude_unset=True)
            if "attributes" in update_data:
                update_data["attributes_json"] = [a.model_dump() for a in update_data.pop("attributes")]
            for key, value in update_data.items():
                if value is not None:
                    setattr(template, key, value)
            session.commit()
            session.refresh(template)
            return _template_to_response(template)

    def delete(self, template_id: str) -> None:
        with get_session() as session:
            template = session.get(AssetTemplate, template_id)
            if not template:
                raise ValueError(f"Template '{template_id}' not found")
            session.delete(template)
            session.commit()

    def seed_defaults(self) -> list[TemplateResponse]:
        created = []
        with get_session() as session:
            for tpl_data in DEFAULT_TEMPLATES:
                existing = session.get(AssetTemplate, tpl_data.template_id)
                if existing:
                    continue
                template = AssetTemplate(
                    template_id=tpl_data.template_id,
                    name=tpl_data.name,
                    asset_type=tpl_data.asset_type,
                    asset_role=tpl_data.asset_role,
                    description=tpl_data.description,
                    attributes_json=[a.model_dump() for a in tpl_data.attributes],
                    domain_type=tpl_data.domain_type,
                    status="active",
                )
                session.add(template)
                session.flush()
                created.append(_template_to_response(template))
            session.commit()
        return created


# ---- Binding Service ----

class BindingService:
    def create(self, asset_id: str, data: BindingCreate) -> BindingResponse:
        with get_session() as session:
            # Check asset exists by business key
            from app.modules.assets.models import Asset
            from sqlalchemy import select
            asset = session.scalar(select(Asset).where(Asset.asset_id == asset_id))
            if not asset:
                raise ValueError(f"Asset '{asset_id}' not found")

            # Check duplicate attribute_name for this asset
            from sqlalchemy import select
            existing = session.scalar(
                select(AssetAttributeBinding).where(
                    AssetAttributeBinding.asset_id == asset_id,
                    AssetAttributeBinding.attribute_name == data.attribute_name,
                )
            )
            if existing:
                raise ValueError(f"Binding for attribute '{data.attribute_name}' already exists on asset '{asset_id}'")

            binding = AssetAttributeBinding(
                asset_id=asset_id,
                attribute_name=data.attribute_name,
                signal_id=data.signal_id,
                binding_type=data.binding_type,
                status="active",
            )
            session.add(binding)
            session.commit()
            session.refresh(binding)
            return _binding_to_response(binding)

    def list_for_asset(self, asset_id: str) -> list[BindingResponse]:
        with get_session() as session:
            from sqlalchemy import select
            bindings = session.scalars(
                select(AssetAttributeBinding)
                .where(AssetAttributeBinding.asset_id == asset_id)
                .order_by(AssetAttributeBinding.attribute_name)
            ).all()
            return [_binding_to_response(b) for b in bindings]

    def delete(self, asset_id: str, binding_id: str) -> None:
        with get_session() as session:
            from sqlalchemy import select
            binding = session.scalar(
                select(AssetAttributeBinding).where(
                    AssetAttributeBinding.binding_id == binding_id,
                    AssetAttributeBinding.asset_id == asset_id,
                )
            )
            if not binding:
                raise ValueError(f"Binding '{binding_id}' not found on asset '{asset_id}'")
            session.delete(binding)
            session.commit()

    def from_template(self, asset_id: str, template_id: str) -> list[BindingResponse]:
        """Auto-generate bindings from template attributes."""
        with get_session() as session:
            from app.modules.assets.models import Asset
            from sqlalchemy import select
            asset = session.scalar(select(Asset).where(Asset.asset_id == asset_id))
            if not asset:
                raise ValueError(f"Asset '{asset_id}' not found")

            template = session.get(AssetTemplate, template_id)
            if not template:
                raise ValueError(f"Template '{template_id}' not found")

            attrs = template.attributes_json if isinstance(template.attributes_json, list) else []
            created = []
            for attr in attrs:
                # Skip if binding already exists for this attribute
                from sqlalchemy import select
                existing = session.scalar(
                    select(AssetAttributeBinding).where(
                        AssetAttributeBinding.asset_id == asset_id,
                        AssetAttributeBinding.attribute_name == attr.get("name"),
                    )
                )
                if existing:
                    continue

                binding = AssetAttributeBinding(
                    asset_id=asset_id,
                    template_id=template_id,
                    attribute_name=attr.get("name", ""),
                    signal_id=None,
                    binding_type="direct",
                    status="pending",
                )
                session.add(binding)
                session.flush()
                created.append(_binding_to_response(binding))
            session.commit()
        return created

    def validate(self, asset_id: str) -> ValidationSummary:
        """Validate all bindings for an asset."""
        with get_session() as session:
            from sqlalchemy import select
            bindings = session.scalars(
                select(AssetAttributeBinding)
                .where(AssetAttributeBinding.asset_id == asset_id)
            ).all()

            errors: list[str] = []
            warnings: list[str] = []

            for binding in bindings:
                if binding.signal_id:
                    from sqlalchemy import select
                    signal = session.scalar(select(Signal).where(Signal.signal_id == binding.signal_id))
                    if not signal:
                        errors.append(f"Attribute '{binding.attribute_name}': signal '{binding.signal_id}' not found")
                        binding.validation_status = "error"
                        binding.validation_message = f"Signal '{binding.signal_id}' not found"
                    else:
                        # Check signal_category compatibility
                        binding.validation_status = "ok"
                        binding.validation_message = f"Bound to {signal.signal_id} (type: {signal.signal_type})"
                elif binding.status == "pending" or binding.status == "active":
                    # Check if this attribute is required by looking up the template
                    if binding.template_id:
                        template = session.get(AssetTemplate, binding.template_id)
                        if template and isinstance(template.attributes_json, list):
                            for attr in template.attributes_json:
                                if attr.get("name") == binding.attribute_name and attr.get("required"):
                                    warnings.append(f"Attribute '{binding.attribute_name}': required but no signal bound")
                                    binding.validation_status = "warning"
                                    binding.validation_message = "Required attribute — no signal bound"
                                    break
                            else:
                                binding.validation_status = "info"
                                binding.validation_message = "No signal bound (optional)"
                        else:
                            binding.validation_status = "info"
                            binding.validation_message = "No signal bound"
                    else:
                        binding.validation_status = "info"
                        binding.validation_message = "No signal bound"

            session.commit()

            return ValidationSummary(
                valid=len(errors) == 0,
                errors=errors,
                warnings=warnings,
            )


# ---- Helpers ----

def _template_to_response(t: AssetTemplate) -> TemplateResponse:
    attrs = t.attributes_json if isinstance(t.attributes_json, list) else []
    return TemplateResponse(
        template_id=t.template_id,
        name=t.name,
        asset_type=t.asset_type,
        asset_role=t.asset_role,
        description=t.description,
        attributes=attrs,
        domain_type=t.domain_type,
        version=t.version,
        status=t.status,
        created_at=t.created_at,
        updated_at=t.updated_at,
    )


def _binding_to_response(b: AssetAttributeBinding) -> BindingResponse:
    return BindingResponse(
        binding_id=str(b.binding_id),
        asset_id=b.asset_id,
        template_id=b.template_id,
        attribute_name=b.attribute_name,
        signal_id=b.signal_id,
        binding_type=b.binding_type,
        status=b.status,
        validation_status=b.validation_status,
        validation_message=b.validation_message,
        created_at=b.created_at,
        updated_at=b.updated_at,
    )
