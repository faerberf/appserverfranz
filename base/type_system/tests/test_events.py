# Unit tests for events module.
import unittest
from type_system.core.events import register_event_handler, trigger_event

class TestEvents(unittest.TestCase):
    def test_event_handling(self):
        test_events = []

        def test_handler(payload):
            test_events.append(payload)

        register_event_handler("test_event", test_handler)
        trigger_event("test_event", {"data": "test_data"})

        self.assertEqual(len(test_events), 1)
        self.assertEqual(test_events[0]["data"], "test_data")