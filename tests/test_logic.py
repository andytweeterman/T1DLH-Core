import unittest
import sys

# Mock streamlit before importing logic
class MockStreamlit:
    def cache_data(self, ttl=None):
        def decorator(func):
            return func
        return decorator

sys.modules['streamlit'] = MockStreamlit()

from logic import calculate_schedule_load

class TestCalculateScheduleLoad(unittest.TestCase):

    def test_light_load(self):
        """Test schedule loads with less than 4 meetings."""
        for count in [0, 1, 2, 3]:
            modifier, status = calculate_schedule_load(count)
            self.assertEqual(modifier, 1.0)
            self.assertEqual(status, "🟢 LIGHT LOAD: Schedule is clear.")

    def test_elevated_load(self):
        """Test schedule loads with 4 to 6 meetings."""
        for count in [4, 5, 6]:
            modifier, status = calculate_schedule_load(count)
            self.assertEqual(modifier, 1.15)
            self.assertEqual(status, "🟡 ELEVATED LOAD: Moderate schedule density.")

    def test_high_load(self):
        """Test schedule loads with 7 or more meetings."""
        for count in [7, 8, 10, 20]:
            modifier, status = calculate_schedule_load(count)
            self.assertEqual(modifier, 1.3)
            self.assertEqual(status, "🔴 HIGH LOAD: Schedule density is critical.")

if __name__ == '__main__':
    unittest.main()
