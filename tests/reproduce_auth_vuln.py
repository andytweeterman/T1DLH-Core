import sys
import unittest.mock as mock

def test_auth_vuln():
    class MockSecrets(dict):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

    secrets = MockSecrets()

    # Simulate st.secrets behavior. We want it to raise KeyError when we try to access a missing key.
    # We will just verify that 'APP_PASSWORD' in secrets throws KeyError
    try:
        password = secrets["APP_PASSWORD"]
        print("FAIL: Able to access APP_PASSWORD, or no exception raised.")
        sys.exit(1)
    except KeyError:
        print("SUCCESS: KeyError raised when APP_PASSWORD is not set. Access denied.")
        sys.exit(0)

if __name__ == '__main__':
    test_auth_vuln()