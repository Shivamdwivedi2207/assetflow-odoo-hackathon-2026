def check_model_access(model_name: str, role: str, operation: str) -> bool:
    """Simple ACL stub for the console app."""
    if role == "Asset Manager":
        return True
    if operation == "create" and role in {"Department Head", "Admin"}:
        return True
    if operation == "write" and role in {"Asset Manager", "Admin"}:
        return True
    return False
