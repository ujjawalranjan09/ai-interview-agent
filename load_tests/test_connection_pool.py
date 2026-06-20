"""Connection pooling load test."""
import asyncio
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import List
import uuid


@dataclass
class ConnectionPoolStats:
    total_connections: int = 0
    active_connections: int = 0
    wait_times: List[float] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


class MockAsyncConnectionPool:
    """Simulates async database connection pool behavior."""

    def __init__(self, min_size: int = 5, max_size: int = 20):
        self.min_size = min_size
        self.max_size = max_size
        self._size = min_size
        self._in_use = 0
        self._stats = ConnectionPoolStats()

    @asynccontextmanager
    async def acquire(self):
        start = time.perf_counter()
        while self._in_use >= self._size:
            if self._size < self.max_size:
                self._size += 1
            else:
                await asyncio.sleep(0.01)
        self._in_use += 1
        self._stats.total_connections += 1
        try:
            yield
        finally:
            self._in_use -= 1
            self._stats.wait_times.append(time.perf_counter() - start)

    @property
    def stats(self) -> ConnectionPoolStats:
        return self._stats

    async def reset(self):
        self._size = self.min_size
        self._in_use = 0
        self._stats = ConnectionPoolStats()


async def simulate_concurrent_requests(pool: MockAsyncConnectionPool, count: int):
    """Simulate concurrent database requests."""

    async def _request(_id: int):
        async with pool.acquire():
            await asyncio.sleep(0.05)

    await asyncio.gather(*[_request(i) for i in range(count)])


async def run_pool_test():
    pool = MockAsyncConnectionPool(min_size=5, max_size=20)

    results = []
    for concurrency in [10, 25, 50, 100]:
        start = time.perf_counter()
        await simulate_concurrent_requests(pool, concurrency)
        duration = time.perf_counter() - start
        results.append({
            "concurrency": concurrency,
            "duration_seconds": round(duration, 3),
            "total_connections": pool.stats.total_connections,
            "max_pool_size": pool._size,
        })
        await pool.reset()

    print("\n=== Connection Pool Test Results ===")
    print(f"{'Concurrency':<15} {'Duration (s)':<15} {'Total Conn':<15} {'Max Pool':<15}")
    print("-" * 60)
    for r in results:
        print(f"{r['concurrency']:<15} {r['duration_seconds']:<15} {r['total_connections']:<15} {r['max_pool_size']:<15}")

    assert all(r["duration_seconds"] < 2.0 for r in results), "Pool test failed"
    print("\nAll pool tests passed\n")


if __name__ == "__main__":
    asyncio.run(run_pool_test())
