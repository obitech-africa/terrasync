from fastapi import APIRouter

from app.api.v1.routers import configuration, assets, auth, defects, demo, devices, health, operations, reports, sites, sync, templates, work_orders

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(sites.router)
api_router.include_router(work_orders.router)
api_router.include_router(templates.router)
api_router.include_router(reports.router)
api_router.include_router(assets.router)
api_router.include_router(defects.router)
api_router.include_router(sync.router)
api_router.include_router(demo.router)

api_router.include_router(auth.router)
api_router.include_router(devices.router)
api_router.include_router(operations.router)

api_router.include_router(configuration.router)
