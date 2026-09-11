from .telecom_tower_pm import TELECOM_TOWER_PM_TEMPLATE
from .telecom_tower_routine import TELECOM_TOWER_ROUTINE_TEMPLATE
from app.data.templates.telecom_tower_fault import TELECOM_TOWER_FAULT_TEMPLATE
from app.data.templates.telecom_rms_alarm import TELECOM_RMS_ALARM_TEMPLATE
from app.data.templates.solar_site_pm import SOLAR_SITE_PM_TEMPLATE


def get_default_templates() -> list[dict]:
    return [
        TELECOM_TOWER_PM_TEMPLATE,
        TELECOM_TOWER_ROUTINE_TEMPLATE,
        TELECOM_TOWER_FAULT_TEMPLATE,
        TELECOM_RMS_ALARM_TEMPLATE,
        SOLAR_SITE_PM_TEMPLATE,
    ]