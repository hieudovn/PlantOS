"""Validate WTP contract against Pydantic and custom rules."""
import sys

import yaml

sys.path.insert(0, "backend")

from app.modules.contracts.schemas import ContractV2
from app.modules.contracts.validator import validate_contract

with open("examples/contracts/wtp-demo-01.contract.yaml") as f:
    data = yaml.safe_load(f)

# Layer 1: Pydantic
try:
    contract = ContractV2(**data)
    print("PASS Pydantic validation PASSED")
except Exception as e:
    print(f"FAIL Pydantic validation FAILED: {e}")
    sys.exit(1)

# Layer 2: Custom rules
result = validate_contract(data)

print(f"Errors: {len(result.errors)}")
for e in result.errors:
    print(f"  ERROR {e['path']}: {e['message']}")

print(f"Warnings: {len(result.warnings)}")

if result.valid:
    print("PASS Custom validation PASSED")
else:
    print("FAIL Custom validation FAILED")
    sys.exit(1)

# Summary
areas = len(data["areas"])
assets = len(data["assets"])
signals = len(data["signals"])
print(f"Summary: {areas} areas, {assets} assets, {signals} signals")

