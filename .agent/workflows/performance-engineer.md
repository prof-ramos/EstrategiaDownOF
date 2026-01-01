---
description: Profile applications, optimize bottlenecks, and implement caching strategies
---

# Performance Engineer Workflow

Profile applications, optimize bottlenecks, and implement caching strategies. Handles load testing,
CDN setup, and query optimization.

## Focus Areas

- Application profiling (CPU, memory, I/O)
- Load testing with JMeter/k6/Locust
- Caching strategies (Redis, CDN, browser)
- Database query optimization
- Frontend performance (Core Web Vitals)
- API response time optimization

## Approach

1. Measure before optimizing
2. Focus on biggest bottlenecks first
3. Set performance budgets
4. Cache at appropriate layers
5. Load test realistic scenarios

## Output

- Performance profiling results with flamegraphs
- Load test scripts and results
- Caching implementation with TTL strategy
- Optimization recommendations ranked by impact
- Before/after performance metrics
- Monitoring dashboard setup

## Commands

### Profile Python Application

// turbo

```bash
python -m cProfile -s cumulative main.py --headless 2>&1 | head -50
```

### Memory Profiling

```bash
pip install memory-profiler
python -m memory_profiler main.py
```

### Run Benchmark Script

// turbo

```bash
python benchmark.py
```

### Analyze Download Performance

// turbo

```bash
python benchmark.py --analyze
```

## Performance Targets for Estratégia Downloader

- Download speed: ≥10 MB/s per file (with good connection)
- Concurrent downloads: 4-8 workers optimal
- Memory usage: <500MB during operation
- CPU usage: <50% (I/O bound, not CPU bound)
- Compression ratio: ≥40% size reduction with H.265
