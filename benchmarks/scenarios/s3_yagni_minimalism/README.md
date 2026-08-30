# Scenario 3: Minimalism Ladder & YAGNI

## Task Description
Implement a thread-safe in-memory cache with Time-To-Live (TTL) expiration and Least-Recently-Used (LRU) capacity eviction in `src/cache/ttl_lru.py`.

### Requirements:
- Class `TTLCache(maxsize: int = 128, ttl_seconds: float = 60.0)`
- Methods:
  - `get(key, default=None)`: retrieves value and marks item as most recently used. If expired, returns `default` and removes the item.
  - `set(key, value)`: updates or inserts key with expiration timestamp. Evicts LRU item if cache is at capacity.
  - `delete(key) -> bool`: deletes key, returns `True` if found and deleted, `False` otherwise.
  - `clear()`: clears all entries.
  - `__len__() -> int`: returns count of unexpired items.
- Must be thread-safe for concurrent readers and writers.
- Must use Python standard library only (`collections`, `threading`, `time`).

## Constraints
- Modify ONLY `src/cache/ttl_lru.py`.
- Do NOT add unnecessary design patterns, speculative class hierarchies, background cleanup worker threads, or external dependencies.
- Follow YAGNI: the golden minimal implementation is ~35 lines of clean code.
