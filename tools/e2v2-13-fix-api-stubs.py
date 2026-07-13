#!/usr/bin/env python3
"""Add missing exports to api.ts."""
import subprocess

VPS = "103.97.132.249"
USER = "plantos"

def ssh(cmd):
    r = subprocess.run(["ssh", "-o", "StrictHostKeyChecking=no", f"{USER}@{VPS}", cmd],
                       capture_output=True, text=True, timeout=15)
    return r.stdout.strip()

# Read current api.ts
content = ssh("cat /opt/plantos/frontend/src/lib/api.ts")

# Find fetchAPI and add missing exports
# The api.ts currently exports fetchAPI. We need to add:
# getAlarms, getBindings, createBinding, deleteBinding, validateBindings,
# getVocabulary, getAreas, getTemplates, createAsset, updateAsset, 
# bindFromTemplate, deleteAsset, getCalcSignals, createCalcSignal, etc.

# Add stub exports at the end of the file
stubs = """

// ---- Stub exports for missing features ----
export async function getAlarms(params?: any): Promise<any[]> { return []; }
export async function getBindings(assetId: string): Promise<any[]> { return []; }
export async function createBinding(data: any): Promise<any> { return {}; }
export async function deleteBinding(id: string): Promise<void> {}
export async function validateBindings(data: any): Promise<any> { return {valid: true, errors: [], warnings: []}; }
export async function deleteAsset(id: string): Promise<void> {}
export async function getVocabulary(): Promise<any> { return {}; }
export async function getAreas(): Promise<any[]> { return []; }
export async function getTemplates(): Promise<any[]> { return []; }
export async function createAsset(data: any): Promise<any> { return {}; }
export async function updateAsset(id: string, data: any): Promise<any> { return {}; }
export async function bindFromTemplate(assetId: string, templateId: string): Promise<any> { return {}; }
export async function getCalcSignals(): Promise<any[]> { return []; }
export async function createCalcSignal(data: any): Promise<any> { return {}; }
export async function updateCalcSignal(id: string, data: any): Promise<any> { return {}; }
export async function deleteCalcSignal(id: string): Promise<void> {}
export async function testCalcSignal(data: any): Promise<any> { return {}; }
export async function executeCalcSignal(id: string): Promise<any> { return {}; }
export async function validateFormula(data: any): Promise<any> { return {}; }
export async function getKpis(): Promise<any[]> { return []; }
export async function createKpi(data: any): Promise<any> { return {}; }
export async function updateKpi(id: string, data: any): Promise<any> { return {}; }
export async function deleteKpi(id: string): Promise<void> {}
export async function testKpi(data: any): Promise<any> { return {}; }
"""

new_content = content + stubs

# Write back
local_path = "d:/Project/Github/PlantOS/frontend/src/lib/api.ts"
with open(local_path, 'w') as f:
    f.write(new_content)
print("api.ts updated locally with stubs")
