from sqlalchemy import Table

EXCLUDED_SCHEMAS = {"auth", "storage", "realtime", "extensions"}


def include_object(object, name, type_, reflected, compare_to):
    # Only tables have schemas
    if isinstance(object, Table):
        if object.schema in EXCLUDED_SCHEMAS:
            return False

    return True
