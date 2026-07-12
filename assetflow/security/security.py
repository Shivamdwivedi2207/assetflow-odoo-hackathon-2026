def check_record_rule(model_name: str, record, user) -> bool:
    """Simple record-rule stub that allows visible records for authenticated users."""
    if not user:
        return False
    return True
