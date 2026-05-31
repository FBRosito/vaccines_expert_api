"""
Inference engine performance benchmark — N=200 patients.
Measures per-query latency (mean, median, p95, p99) and estimated throughput.
Runs the engine in isolation (no HTTP, no database).
"""
import random
import statistics
import time

from helpers import birth_date_ago, run_engine

random.seed(0)
N = 200


def test_motor_latencia():
    """Mean latency < 500 ms/query; reports full distribution."""
    tempos_ms = []
    for _ in range(N):
        anos = random.randint(0, 80)
        dn = birth_date_ago(years=anos)
        t0 = time.perf_counter()
        run_engine(dn)
        tempos_ms.append((time.perf_counter() - t0) * 1000)

    tempos_ord = sorted(tempos_ms)
    media      = statistics.mean(tempos_ms)
    mediana    = statistics.median(tempos_ms)
    p95        = tempos_ord[int(0.95 * N) - 1]
    p99        = tempos_ord[int(0.99 * N) - 1]
    throughput = 1000.0 / media

    print(f"\nBenchmark do motor de inferência (N={N} pacientes):")
    print(f"  Média:      {media:.1f} ms")
    print(f"  Mediana:    {mediana:.1f} ms")
    print(f"  p95:        {p95:.1f} ms")
    print(f"  p99:        {p99:.1f} ms")
    print(f"  Throughput: {throughput:.1f} consultas/s (motor isolado)")

    assert media < 500, f"Motor acima de 500 ms/consulta: {media:.1f} ms"
