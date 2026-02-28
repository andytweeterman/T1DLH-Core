import timeit
from mock_data import get_mock_cgm

def benchmark():
    num_runs = 1000
    time_taken = timeit.timeit("get_mock_cgm()", globals=globals(), number=num_runs)
    print(f"Time for {num_runs} runs: {time_taken:.4f} seconds")
    print(f"Average time per run: {time_taken/num_runs * 1000:.4f} ms")

if __name__ == "__main__":
    benchmark()
