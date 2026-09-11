FIELD_REPORT_PHOTO_RULE = """
All report photos must be captured by the assigned field engineer through the TerraSync mobile app camera during field reporting.

Photos must be compressed by the mobile app, uploaded as field evidence, and stored inside the corresponding report answer or defect item before report submission.

Coordinators and administrators may review, approve, reject, edit comments, or request changes, but they cannot attach, replace, or upload field evidence after submission.
"""


def get_report_photo_rule() -> dict:
    return {
        "rule_id": "RULE-FIELD-PHOTOS-001",
        "name": "Field Engineer Camera Evidence Rule",
        "description": FIELD_REPORT_PHOTO_RULE.strip(),
        "applies_to": [
            "field_reports",
            "report_answers",
            "report_defects",
            "photo_evidence",
            "coordinator_review",
        ],
        "allowed_photo_source": "mobile_app_camera_only",
        "coordinator_can": [
            "review_report",
            "approve_report",
            "edit_comment_in_report",
            "reject_report",
            "request_changes",
            "comment_on_report",
        ],
        "coordinator_cannot": [
            "attach_photos",
            "replace_photos",
            "upload_field_evidence",
            "modify_field_evidence",
        ],
    }