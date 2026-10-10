import re

with open("tests/test_logic.py", "r") as f:
    content = f.read()

# Fix duplicated imports
content = content.replace("from freezegun import freeze_time\nfrom freezegun import freeze_time", "from freezegun import freeze_time")
content = content.replace("is_weekend_window,\n    is_weekend_window,", "is_weekend_window,")

# Remove duplicated test block
test_block_pattern = r"# --- TEST IS_WEEKEND_WINDOW ---\n@pytest\.mark\.parametrize\(\"mock_time, expected\", \[\n    \(\"2023-10-13 16:59:59\", False\),  # Friday 4:59 PM\n    \(\"2023-10-13 17:00:00\", True\),   # Friday 5:00 PM\n    \(\"2023-10-14 12:00:00\", True\),   # Saturday Noon\n    \(\"2023-10-15 12:00:00\", True\),   # Sunday Noon\n    \(\"2023-10-16 07:59:59\", True\),   # Monday 7:59 AM\n    \(\"2023-10-16 08:00:00\", False\),  # Monday 8:00 AM\n    \(\"2023-10-18 12:00:00\", False\),  # Wednesday Noon\n\]\)\ndef test_is_weekend_window\(mock_time, expected\):\n    with freeze_time\(mock_time\):\n        assert is_weekend_window\(\) == expected\n\n\n# --- TEST IS_WEEKEND_WINDOW ---\n@pytest\.mark\.parametrize\(\"mock_time, expected\", \[\n    \(\"2023-10-13 16:59:59\", False\),  # Friday 4:59 PM\n    \(\"2023-10-13 17:00:00\", True\),   # Friday 5:00 PM\n    \(\"2023-10-14 12:00:00\", True\),   # Saturday Noon\n    \(\"2023-10-15 12:00:00\", True\),   # Sunday Noon\n    \(\"2023-10-16 07:59:59\", True\),   # Monday 7:59 AM\n    \(\"2023-10-16 08:00:00\", False\),  # Monday 8:00 AM\n    \(\"2023-10-18 12:00:00\", False\),  # Wednesday Noon\n\]\)\ndef test_is_weekend_window\(mock_time, expected\):\n    with freeze_time\(mock_time\):\n        assert is_weekend_window\(\) == expected"

replacement = """# --- TEST IS_WEEKEND_WINDOW ---
@pytest.mark.parametrize("mock_time, expected", [
    ("2023-10-13 16:59:59", False),  # Friday 4:59 PM
    ("2023-10-13 17:00:00", True),   # Friday 5:00 PM
    ("2023-10-14 12:00:00", True),   # Saturday Noon
    ("2023-10-15 12:00:00", True),   # Sunday Noon
    ("2023-10-16 07:59:59", True),   # Monday 7:59 AM
    ("2023-10-16 08:00:00", False),  # Monday 8:00 AM
    ("2023-10-18 12:00:00", False),  # Wednesday Noon
])
def test_is_weekend_window(mock_time, expected):
    with freeze_time(mock_time):
        assert is_weekend_window() == expected"""

content = re.sub(test_block_pattern, replacement, content)

with open("tests/test_logic.py", "w") as f:
    f.write(content)
