import inspect
from dataclasses import dataclass


@dataclass
class EventDefinition:
    name: str
    category: str
    description: str = ""


from .users import *


# Auto-collect all event constants
ALL_EVENTS = set()
ALL_EVENT_DEFINITIONS = {}
for module in [users]:

    for name, value in inspect.getmembers(module):
        if isinstance(value, EventDefinition) and not name.startswith("_"):
            ALL_EVENTS.add(value.name)  # Add the event name string
            ALL_EVENT_DEFINITIONS[value.name] = value  # Store the full definition
