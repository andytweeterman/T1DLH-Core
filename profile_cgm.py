import cProfile
from mock_data import get_mock_cgm

cProfile.run('for _ in range(100): get_mock_cgm()')
