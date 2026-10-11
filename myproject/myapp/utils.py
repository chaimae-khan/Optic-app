# ============================================
# utils.py  (new file — place alongside views.py)
# ============================================
from django.forms.models import model_to_dict

# Fields to never expose in diffs (security / noise)
_SKIP_FIELDS = frozenset({
    "id", "pk", "password", "last_login",
    "created_at", "updated_at", "date_joined",
})

def capture_changes(instance, new_data: dict) -> dict:
    """
    Compare the current DB state of `instance` against `new_data`
    (a plain {field: new_value} dict) and return only the fields
    that actually changed.

    Returns:
        {
          "field_name": {"old": <old_value>, "new": <new_value>},
          ...
        }

    Usage (in any update view):
        old_state = model_to_dict(instance)
        # ... apply new values to instance ...
        changes = capture_changes_from_states(old_state, new_data)
    """
    old_state = model_to_dict(instance)
    changes = {}

    for field, new_value in new_data.items():
        if field in _SKIP_FIELDS:
            continue
        old_value = old_state.get(field)
        # Normalise to string so FK ids vs objects compare cleanly
        if str(old_value) != str(new_value):
            changes[field] = {"old": old_value, "new": new_value}

    return changes