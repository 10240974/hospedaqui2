def validate_entry(entry):
    # Implement validation logic for the data entry
    if not entry.get("name") or not entry.get("value"):
        raise ValueError("Entry must have a name and a value.")
    return True

def format_entry(entry):
    # Format the entry for display or storage
    return {
        "name": entry["name"].strip().title(),
        "value": str(entry["value"]).strip()
    }