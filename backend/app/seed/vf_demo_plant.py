"""Seed data for Virtual Factory Compressor Train plant assets and signals."""

VF_PLANT = {
    "plant_id": "VF-DEMO",
    "plant_code": "VF-DEMO",
    "name": "Virtual Factory Demo Plant",
    "description": "Compressor Train Analytics Benchmark",
}

VF_AREA = {
    "area_id": "COMPRESSOR-AREA",
    "area_code": "COMPRESSOR-AREA",
    "name": "Compressor Area",
    "plant_id": "VF-DEMO",
}

VF_ASSETS = [
    {"asset_id": "COMP01", "asset_code": "COMP01", "name": "Compressor Train A",
     "asset_type": "compressor_train", "parent_asset_id": None,
     "plant_id": "VF-DEMO", "area_id": "COMPRESSOR-AREA", "criticality": "critical"},
    {"asset_id": "COMP01-MOTOR", "asset_code": "COMP01-MOTOR", "name": "Drive Motor",
     "asset_type": "motor", "parent_asset_id": "COMP01",
     "plant_id": "VF-DEMO", "area_id": "COMPRESSOR-AREA", "criticality": "critical"},
    {"asset_id": "COMP01-CORE", "asset_code": "COMP01-CORE", "name": "Compressor Core",
     "asset_type": "compressor", "parent_asset_id": "COMP01",
     "plant_id": "VF-DEMO", "area_id": "COMPRESSOR-AREA", "criticality": "critical"},
    {"asset_id": "COMP01-BEARINGS", "asset_code": "COMP01-BEARINGS", "name": "Bearings Assembly",
     "asset_type": "bearing_assembly", "parent_asset_id": "COMP01",
     "plant_id": "VF-DEMO", "area_id": "COMPRESSOR-AREA", "criticality": "high"},
    {"asset_id": "COMP01-LUBE", "asset_code": "COMP01-LUBE", "name": "Lube Oil System",
     "asset_type": "lubrication_system", "parent_asset_id": "COMP01",
     "plant_id": "VF-DEMO", "area_id": "COMPRESSOR-AREA", "criticality": "high"},
    {"asset_id": "COMP01-COOLING", "asset_code": "COMP01-COOLING", "name": "Cooling Water System",
     "asset_type": "cooling_system", "parent_asset_id": "COMP01",
     "plant_id": "VF-DEMO", "area_id": "COMPRESSOR-AREA", "criticality": "medium"},
    {"asset_id": "COMP01-SEAL", "asset_code": "COMP01-SEAL", "name": "Seal Gas System",
     "asset_type": "seal_system", "parent_asset_id": "COMP01",
     "plant_id": "VF-DEMO", "area_id": "COMPRESSOR-AREA", "criticality": "high"},
]

VF_SIGNALS = [
    # Compressor Core (7)
    {"signal_id": "COMP01-CORE.suction_pressure", "asset_id": "COMP01-CORE",
     "signal_name": "suction_pressure", "display_name": "Suction Pressure",
     "signal_type": "measurement", "data_type": "float", "engineering_unit": "kPa",
     "source": {"source_type": "opcua", "source_ref": "ns=2;s=COMP01_SUCTION_PRESSURE"}},
    {"signal_id": "COMP01-CORE.discharge_pressure", "asset_id": "COMP01-CORE",
     "signal_name": "discharge_pressure", "display_name": "Discharge Pressure",
     "signal_type": "measurement", "data_type": "float", "engineering_unit": "kPa",
     "source": {"source_type": "opcua", "source_ref": "ns=2;s=COMP01_DISCHARGE_PRESSURE"}},
    {"signal_id": "COMP01-CORE.flow_rate", "asset_id": "COMP01-CORE",
     "signal_name": "flow_rate", "display_name": "Flow Rate",
     "signal_type": "measurement", "data_type": "float", "engineering_unit": "m3/h",
     "source": {"source_type": "opcua", "source_ref": "ns=2;s=COMP01_FLOW"}},
    {"signal_id": "COMP01-CORE.suction_temp", "asset_id": "COMP01-CORE",
     "signal_name": "suction_temp", "display_name": "Suction Temperature",
     "signal_type": "measurement", "data_type": "float", "engineering_unit": "degC",
     "source": {"source_type": "opcua", "source_ref": "ns=2;s=COMP01_SUCTION_TEMP"}},
    {"signal_id": "COMP01-CORE.discharge_temp", "asset_id": "COMP01-CORE",
     "signal_name": "discharge_temp", "display_name": "Discharge Temperature",
     "signal_type": "measurement", "data_type": "float", "engineering_unit": "degC",
     "source": {"source_type": "opcua", "source_ref": "ns=2;s=COMP01_DISCHARGE_TEMP"}},
    {"signal_id": "COMP01-CORE.speed", "asset_id": "COMP01-CORE",
     "signal_name": "speed", "display_name": "Rotational Speed",
     "signal_type": "measurement", "data_type": "float", "engineering_unit": "RPM",
     "source": {"source_type": "opcua", "source_ref": "ns=2;s=COMP01_SPEED"}},
    {"signal_id": "COMP01-CORE.power", "asset_id": "COMP01-CORE",
     "signal_name": "power", "display_name": "Power Consumption",
     "signal_type": "measurement", "data_type": "float", "engineering_unit": "kW",
     "source": {"source_type": "opcua", "source_ref": "ns=2;s=COMP01_POWER"}},
    # Motor (7)
    {"signal_id": "COMP01-MOTOR.current", "asset_id": "COMP01-MOTOR",
     "signal_name": "current", "display_name": "Motor Current",
     "signal_type": "measurement", "data_type": "float", "engineering_unit": "A",
     "source": {"source_type": "opcua", "source_ref": "ns=2;s=COMP01_MOTOR_CURRENT"}},
    {"signal_id": "COMP01-MOTOR.power", "asset_id": "COMP01-MOTOR",
     "signal_name": "power", "display_name": "Motor Power",
     "signal_type": "measurement", "data_type": "float", "engineering_unit": "kW",
     "source": {"source_type": "opcua", "source_ref": "ns=2;s=COMP01_MOTOR_POWER"}},
    {"signal_id": "COMP01-MOTOR.winding_temp", "asset_id": "COMP01-MOTOR",
     "signal_name": "winding_temp", "display_name": "Winding Temperature",
     "signal_type": "measurement", "data_type": "float", "engineering_unit": "degC",
     "source": {"source_type": "opcua", "source_ref": "ns=2;s=COMP01_MOTOR_WINDING_TEMP"}},
    {"signal_id": "COMP01-MOTOR.bearing_de_temp", "asset_id": "COMP01-MOTOR",
     "signal_name": "bearing_de_temp", "display_name": "Motor DE Bearing Temp",
     "signal_type": "measurement", "data_type": "float", "engineering_unit": "degC",
     "source": {"source_type": "opcua", "source_ref": "ns=2;s=COMP01_MOTOR_BRG_DE_TEMP"}},
    {"signal_id": "COMP01-MOTOR.bearing_nde_temp", "asset_id": "COMP01-MOTOR",
     "signal_name": "bearing_nde_temp", "display_name": "Motor NDE Bearing Temp",
     "signal_type": "measurement", "data_type": "float", "engineering_unit": "degC",
     "source": {"source_type": "opcua", "source_ref": "ns=2;s=COMP01_MOTOR_BRG_NDE_TEMP"}},
    {"signal_id": "COMP01-MOTOR.vibration_de", "asset_id": "COMP01-MOTOR",
     "signal_name": "vibration_de", "display_name": "Motor DE Vibration",
     "signal_type": "measurement", "data_type": "float", "engineering_unit": "mm/s",
     "source": {"source_type": "opcua", "source_ref": "ns=2;s=COMP01_MOTOR_VIB_DE"}},
    {"signal_id": "COMP01-MOTOR.vibration_nde", "asset_id": "COMP01-MOTOR",
     "signal_name": "vibration_nde", "display_name": "Motor NDE Vibration",
     "signal_type": "measurement", "data_type": "float", "engineering_unit": "mm/s",
     "source": {"source_type": "opcua", "source_ref": "ns=2;s=COMP01_MOTOR_VIB_NDE"}},
    # Bearings (6)
    {"signal_id": "COMP01-BEARINGS.de_temp", "asset_id": "COMP01-BEARINGS",
     "signal_name": "de_temp", "display_name": "DE Bearing Temperature",
     "signal_type": "measurement", "data_type": "float", "engineering_unit": "degC",
     "source": {"source_type": "opcua", "source_ref": "ns=2;s=COMP01_BRG_DE_TEMP"}},
    {"signal_id": "COMP01-BEARINGS.nde_temp", "asset_id": "COMP01-BEARINGS",
     "signal_name": "nde_temp", "display_name": "NDE Bearing Temperature",
     "signal_type": "measurement", "data_type": "float", "engineering_unit": "degC",
     "source": {"source_type": "opcua", "source_ref": "ns=2;s=COMP01_BRG_NDE_TEMP"}},
    {"signal_id": "COMP01-BEARINGS.thrust_temp", "asset_id": "COMP01-BEARINGS",
     "signal_name": "thrust_temp", "display_name": "Thrust Bearing Temperature",
     "signal_type": "measurement", "data_type": "float", "engineering_unit": "degC",
     "source": {"source_type": "opcua", "source_ref": "ns=2;s=COMP01_BRG_THRUST_TEMP"}},
    {"signal_id": "COMP01-BEARINGS.vibration_de", "asset_id": "COMP01-BEARINGS",
     "signal_name": "vibration_de", "display_name": "DE Vibration",
     "signal_type": "measurement", "data_type": "float", "engineering_unit": "mm/s",
     "source": {"source_type": "opcua", "source_ref": "ns=2;s=COMP01_VIB_DE"}},
    {"signal_id": "COMP01-BEARINGS.vibration_nde", "asset_id": "COMP01-BEARINGS",
     "signal_name": "vibration_nde", "display_name": "NDE Vibration",
     "signal_type": "measurement", "data_type": "float", "engineering_unit": "mm/s",
     "source": {"source_type": "opcua", "source_ref": "ns=2;s=COMP01_VIB_NDE"}},
    {"signal_id": "COMP01-BEARINGS.vibration_axial", "asset_id": "COMP01-BEARINGS",
     "signal_name": "vibration_axial", "display_name": "Axial Vibration",
     "signal_type": "measurement", "data_type": "float", "engineering_unit": "mm/s",
     "source": {"source_type": "opcua", "source_ref": "ns=2;s=COMP01_VIB_AXIAL"}},
    # Lube Oil (3)
    {"signal_id": "COMP01-LUBE.pressure", "asset_id": "COMP01-LUBE",
     "signal_name": "pressure", "display_name": "Lube Oil Pressure",
     "signal_type": "measurement", "data_type": "float", "engineering_unit": "kPa",
     "source": {"source_type": "opcua", "source_ref": "ns=2;s=COMP01_LO_PRESS"}},
    {"signal_id": "COMP01-LUBE.temperature", "asset_id": "COMP01-LUBE",
     "signal_name": "temperature", "display_name": "Lube Oil Temperature",
     "signal_type": "measurement", "data_type": "float", "engineering_unit": "degC",
     "source": {"source_type": "opcua", "source_ref": "ns=2;s=COMP01_LO_TEMP"}},
    {"signal_id": "COMP01-LUBE.filter_dp", "asset_id": "COMP01-LUBE",
     "signal_name": "filter_dp", "display_name": "Filter Differential Pressure",
     "signal_type": "measurement", "data_type": "float", "engineering_unit": "kPa",
     "source": {"source_type": "opcua", "source_ref": "ns=2;s=COMP01_LO_FILTER_DP"}},
    # Cooling (2)
    {"signal_id": "COMP01-COOLING.supply_temp", "asset_id": "COMP01-COOLING",
     "signal_name": "supply_temp", "display_name": "Cooling Water Supply Temp",
     "signal_type": "measurement", "data_type": "float", "engineering_unit": "degC",
     "source": {"source_type": "opcua", "source_ref": "ns=2;s=COMP01_CW_SUPPLY_TEMP"}},
    {"signal_id": "COMP01-COOLING.return_temp", "asset_id": "COMP01-COOLING",
     "signal_name": "return_temp", "display_name": "Cooling Water Return Temp",
     "signal_type": "measurement", "data_type": "float", "engineering_unit": "degC",
     "source": {"source_type": "opcua", "source_ref": "ns=2;s=COMP01_CW_RETURN_TEMP"}},
    # Seal Gas (1)
    {"signal_id": "COMP01-SEAL.flow_rate", "asset_id": "COMP01-SEAL",
     "signal_name": "flow_rate", "display_name": "Seal Gas Flow",
     "signal_type": "measurement", "data_type": "float", "engineering_unit": "Nm3/h",
     "source": {"source_type": "opcua", "source_ref": "ns=2;s=COMP01_SEAL_FLOW"}},
]


def seed_vf_demo_plant():
    """Seed Virtual Factory Compressor Train demo plant.

    Uses PlantService, AreaService, AssetService, SignalService directly.
    Idempotent — skips entities that already exist.
    """
    from app.modules.assets.schemas import PlantCreate, AreaCreate, AssetCreate, Location
    from app.modules.assets.service import PlantService, AreaService, AssetService
    from app.modules.signals.schemas import SignalCreate, SourceInfo
    from app.modules.signals.service import SignalService

    plant_svc = PlantService()
    area_svc = AreaService()
    asset_svc = AssetService()
    signal_svc = SignalService()

    results = {"plants": 0, "areas": 0, "assets": 0, "signals": 0, "skipped": 0}

    # Plant
    try:
        plant_svc.create_plant(PlantCreate(
            plant_id=VF_PLANT["plant_id"],
            name=VF_PLANT["name"],
            timezone="UTC",
            status="active",
        ))
        results["plants"] += 1
    except ValueError:
        results["skipped"] += 1

    # Area
    try:
        area_svc.create_area(AreaCreate(
            area_id=VF_AREA["area_id"],
            plant_id=VF_AREA["plant_id"],
            name=VF_AREA["name"],
            area_type=None,
            status="active",
        ))
        results["areas"] += 1
    except ValueError:
        results["skipped"] += 1

    # Assets
    for a in VF_ASSETS:
        try:
            loc = Location(lat=a.get("location", {}).get("lat"), lng=a.get("location", {}).get("lng")) if a.get("location") else None
            asset_svc.create_asset(AssetCreate(
                asset_id=a["asset_id"],
                asset_code=a["asset_code"],
                name=a["name"],
                asset_type=a["asset_type"],
                parent_asset_id=a.get("parent_asset_id"),
                plant_id=a.get("plant_id"),
                area_id=a.get("area_id"),
                criticality=a.get("criticality", "medium"),
                location=loc,
            ))
            results["assets"] += 1
        except ValueError:
            results["skipped"] += 1

    # Signals
    for s in VF_SIGNALS:
        try:
            src = s.get("source")
            source = SourceInfo(
                source_type=src["source_type"],
                source_ref=src["source_ref"],
            ) if src else None
            signal_svc.create_signal(SignalCreate(
                signal_id=s["signal_id"],
                asset_id=s["asset_id"],
                signal_name=s["signal_name"],
                display_name=s.get("display_name"),
                signal_type=s.get("signal_type", "measurement"),
                data_type=s.get("data_type", "float"),
                engineering_unit=s.get("engineering_unit"),
                source=source,
            ))
            results["signals"] += 1
        except ValueError:
            results["skipped"] += 1

    return results
