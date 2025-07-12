from fastapi import FastAPI
import uvicorn

app = FastAPI(
    title="Jules AI Agent PoC",
    description="Proof-of-Concept for the Jules AI IT Support Agent.",
    version="0.0.1",
)

@app.get("/")
async def root():
    """
    Root endpoint to confirm the application is running.
    """
    return {"message": "Jules AI Agent PoC is running!"}

@app.get("/poc/create_tenant_test")
async def create_tenant_test(tenant_name: str = "DefaultTestTenant"):
    """
    Simulates creating a tenant for the PoC.
    In a real app, this would be a POST and interact with a database.
    """
    print(f"PoC: Request to create tenant: {tenant_name}")
    tenant_id = f"tenant_{tenant_name.lower().replace(' ', '_')}_{abs(hash(tenant_name)) % 10000}"
    print(f"PoC: Simulated TenantID: {tenant_id} for Tenant: {tenant_name}")
    return {"tenant_id": tenant_id, "tenant_name": tenant_name, "status": "PoC tenant creation simulated"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
