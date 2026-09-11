from app.db.session import Base, engine

from app.models.user import User
from app.models.site import Site
from app.models.work_order import WorkOrder
from app.models.report import Report
from app.models.inspection_template import InspectionTemplate
from app.models.defect import Defect
from app.models.email_log import EmailLog


def init_db():
    Base.metadata.create_all(bind=engine)