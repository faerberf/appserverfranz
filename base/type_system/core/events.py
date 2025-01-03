# Event handling mechanism.
_event_callbacks = {
    "on_type_defined": [],
    "on_type_updated": [],
    "on_validation_success": [],
    "on_validation_failure": [],
}

def register_event_handler(event_name, callback):
    """Registers a callback function for an event."""
    if event_name not in _event_callbacks:
        raise ValueError(f"Invalid event name: {event_name}")
    _event_callbacks[event_name].append(callback)

def trigger_event(event_name, payload=None):
    """Triggers an event, calling all registered callbacks."""
    if event_name not in _event_callbacks:
        raise ValueError(f"Invalid event name: {event_name}")
    for callback in _event_callbacks[event_name]:
        callback(payload)