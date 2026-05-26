"""
Benchmark de desempenho do motor de inferência — N=200 pacientes.
Mede latência por consulta (média, mediana, p95, p99) e throughput estimado.
Executa o motor de forma isolada (sem HTTP, sem banco de dados).
"""
import random
import statistics
import time

from helpers import birth_date_ago, run_engine

random.seed(0)
N = 200


def test_motor_latencia():
    """Latência média < 500 ms/consulta; reporta distribuição completa."""
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
