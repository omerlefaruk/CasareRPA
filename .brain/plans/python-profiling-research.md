# Python Profiling Tools and Techniques Research

**Date**: 2025-12-05
**Context**: CasareRPA Canvas Performance Optimization
**Purpose**: Evaluate profiling tools for async Qt/PySide6 application

---

## Executive Summary

For CasareRPA's async Qt application, **yappi** is the recommended primary profiler due to native asyncio support. **py-spy** provides complementary production-safe flame graph generation. **airspeed velocity (asv)** handles performance regression testing.

---

## 1. Profiler Comparison Matrix

| Tool | Type | Async Support | Qt Compat | Overhead | Output Formats |
|------|------|---------------|-----------|----------|----------------|
| **cProfile** | Deterministic | Poor | Good | Medium | pstats |
| **py-spy** | Sampling | Good | Excellent | Very Low | Flame SVG, speedscope |
| **yappi** | Deterministic | Excellent | Good | Medium | callgrind, pstats |
| **line_profiler** | Deterministic | Poor | Good | High | Text |
| **Scalene** | Sampling | Good | Good | Low | HTML, JSON |
| **Austin** | Sampling | Good | Excellent | Very Low | Flame, pprof |
| **Pyinstrument** | Sampling | Good | Good | Low | HTML, Text |

---

## 2. Tool Deep Dives

### 2.1 cProfile + Visualization

**Best For**: Quick function-level profiling during development

```python
import cProfile
import pstats

# Profile a specific function
profiler = cProfile.Profile()
profiler.enable()
# ... code to profile ...
profiler.disable()

# Save for visualization
profiler.dump_stats('profile.prof')
```

**Visualization Options**:
- **SnakeViz**: Interactive browser sunburst/icicle (`pip install snakeviz && snakeviz profile.prof`)
- **gprof2dot**: Call graph PNG (`gprof2dot -f pstats profile.prof | dot -Tpng -o graph.png`)

**Limitations**: Does NOT properly track async coroutine time (sees return events as function exits).

---

### 2.2 py-spy (Recommended for Production)

**Best For**: Zero-overhead production profiling, flame graphs

```bash
# Install (Rust binary)
pip install py-spy

# Profile running process
py-spy record -o profile.svg --pid 12345

# Profile script launch
py-spy record -o profile.svg -- python run.py

# Live top-like view
py-spy top --pid 12345
```

**Key Features**:
- **Zero instrumentation**: No code changes required
- **Minimal overhead**: Reads process memory directly via ReadProcessMemory (Windows)
- **Production-safe**: Designed for live services
- **Flame graph output**: Interactive SVG

**Output Formats**:
- `--format flamegraph` (default): Interactive SVG
- `--format speedscope`: For speedscope.app viewer
- `--format raw`: Text format for custom processing

**Windows Note**: May require elevated privileges for process memory access.

---

### 2.3 yappi (Recommended for Async Qt)

**Best For**: Profiling asyncio + threaded code with accurate time tracking

```python
import yappi
import asyncio

# Configure for wall-clock time (includes I/O wait)
yappi.set_clock_type("WALL")

# Or CPU time only
# yappi.set_clock_type("CPU")

# Start profiling
yappi.start()

# Run async code via Qt event loop / qasync
asyncio.run(main())

# Stop and get results
yappi.stop()

# Print function stats
yappi.get_func_stats().print_all()

# Save to callgrind format (for KCachegrind)
yappi.get_func_stats().save('profile.callgrind', type='callgrind')

# Save to pstats format
yappi.get_func_stats().save('profile.pstats', type='pstat')
```

**Async Coroutine Profiling** (v1.2+):
```python
# Correctly tracks time during await/yield
yappi.set_clock_type("WALL")
with yappi.run():
    asyncio.run(async_workflow())

# Shows accurate coroutine wall time including sleep/await periods
yappi.get_func_stats().print_all()
```

**Why yappi for CasareRPA**:
1. Native asyncio support - handles coroutine context switches
2. Wall-clock vs CPU time distinction
3. Multi-thread aware (Qt threads)
4. PyCharm default profiler - IDE integration
5. Callgrind export for KCachegrind visualization

---

### 2.4 line_profiler

**Best For**: Line-by-line analysis of specific hot functions

```python
# Decorate target functions
@profile  # This decorator is added by kernprof
def slow_function():
    result = []              # Line 1
    for i in range(1000):    # Line 2
        result.append(i**2)  # Line 3 - likely hotspot
    return result
```

```bash
# Run with kernprof
kernprof -l -v script.py
```

**Output Example**:
```
Line #      Hits         Time  Per Hit   % Time  Line Contents
     3      1000      50000.0     50.0     80.0          result.append(i**2)
```

**Limitation**: Requires explicit @profile decoration. Not suitable for async code.

---

### 2.5 Scalene

**Best For**: Combined CPU + memory + GPU profiling

```bash
pip install scalene

# Profile script
scalene script.py

# Profile specific file only
scalene --profile-only mymodule.py script.py

# Reduced overhead mode
scalene --reduced-overhead script.py
```

**Unique Features**:
- Separates Python time from native library time
- Memory allocation tracking per-line
- Copy operation detection (CPU <-> GPU)
- AI-powered optimization suggestions

**For CasareRPA**: Useful for identifying if bottleneck is in Python code vs native Qt/Playwright.

---

### 2.6 Austin

**Best For**: Low-overhead statistical sampling with TUI

```bash
# Install
pip install austin-dist

# Sample a running process
austin -p 12345 | flamegraph.pl > profile.svg

# Use Austin TUI for live view
austin-tui python run.py

# Austin Web for browser-based flame graph
austin-web python run.py
```

**Key Features**:
- Pure C implementation, minimal overhead
- No code instrumentation needed
- TUI and Web interfaces
- Cross-platform (Windows supported)
- Multi-process profiling

---

### 2.7 Pyinstrument

**Best For**: Developer-friendly call stack visualization

```python
from pyinstrument import Profiler

profiler = Profiler(async_mode='enabled')  # For asyncio
profiler.start()

# ... code ...

profiler.stop()
print(profiler.output_text(unicode=True, color=True))

# Or HTML output
with open('profile.html', 'w') as f:
    f.write(profiler.output_html())
```

**Output**: Readable call tree with time percentages, not raw numbers.

---

## 3. Best Profiler for Async Qt Application

### Recommended Stack

| Use Case | Tool | Reason |
|----------|------|--------|
| **Primary Development** | yappi | Native asyncio, wall/CPU time, callgrind export |
| **Production Monitoring** | py-spy | Zero overhead, flame graphs, no instrumentation |
| **Hot Function Analysis** | line_profiler | Line-by-line for identified bottlenecks |
| **Memory Investigation** | Scalene | Combined CPU+memory profiling |
| **Live Debugging** | Austin TUI | Real-time view of slow process |

### CasareRPA Integration Points

```python
# src/casare_rpa/utils/profiling.py

import contextlib
from typing import Generator

@contextlib.contextmanager
def profile_async_section(name: str, clock: str = "WALL") -> Generator:
    """Profile an async code section with yappi."""
    import yappi

    yappi.set_clock_type(clock)
    yappi.start()
    try:
        yield
    finally:
        yappi.stop()
        stats = yappi.get_func_stats()
        stats.save(f'profiles/{name}.callgrind', type='callgrind')
        yappi.clear_stats()
```

---

## 4. Profiling Workflow for RPA Development

### Phase 1: Identify (Weekly)

```bash
# Quick sampling during manual testing
py-spy record -o weekly_profile.svg -- python run.py
```

Review flame graph for unexpected wide bars.

### Phase 2: Investigate (On-Demand)

```python
# When bottleneck identified, use yappi for async accuracy
yappi.set_clock_type("WALL")
with yappi.run():
    # Run specific workflow
    pass
yappi.get_func_stats().print_all()
```

### Phase 3: Pinpoint (For Hot Functions)

```python
@profile  # kernprof decorator
def identified_slow_function():
    # Line-by-line analysis
    pass
```

### Phase 4: Validate (After Optimization)

Compare before/after flame graphs. Use asv for regression tracking.

---

## 5. Performance Regression Testing

### Airspeed Velocity (asv) Setup

```bash
pip install asv

# Initialize in project
asv quickstart
```

**benchmarks/benchmark_workflow.py**:
```python
class WorkflowSuite:
    """Benchmark workflow execution performance."""

    def setup(self):
        self.workflow_data = load_test_workflow()

    def time_simple_workflow(self):
        """Benchmark simple 5-node workflow."""
        execute_workflow(self.workflow_data['simple'])

    def time_browser_workflow(self):
        """Benchmark browser automation workflow."""
        execute_workflow(self.workflow_data['browser'])

    def mem_large_workflow(self):
        """Memory usage for 100-node workflow."""
        return execute_workflow(self.workflow_data['large'])
```

**Run Benchmarks**:
```bash
# Run against current commit
asv run

# Run against commit range
asv run v1.0..main

# Find regression source
asv find v1.0 v1.1 benchmark_workflow.WorkflowSuite.time_simple_workflow

# Generate HTML report
asv publish
asv preview
```

### pytest-benchmark Integration

```python
# tests/benchmarks/test_node_performance.py

def test_click_node_speed(benchmark):
    """Benchmark ClickElementNode execution."""
    node = ClickElementNode()
    context = create_mock_context()

    result = benchmark(node.execute, context)

    assert result.success

def test_workflow_execution(benchmark):
    """Benchmark complete workflow."""
    workflow = load_workflow("benchmark_workflow.json")

    benchmark.pedantic(
        execute_workflow,
        args=(workflow,),
        iterations=10,
        rounds=5
    )
```

### CI Integration

```yaml
# .github/workflows/benchmark.yml
name: Performance Regression

on:
  pull_request:
    branches: [main]

jobs:
  benchmark:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: pip install -e .[dev]

      - name: Run benchmarks
        run: pytest tests/benchmarks/ --benchmark-json=benchmark.json

      - name: Check regression
        run: |
          # Compare against main branch baseline
          python scripts/check_regression.py benchmark.json
```

---

## 6. Continuous Profiling (Production)

### Pyroscope/Grafana Integration

For production deployment:

```python
# In robot startup
import pyroscope

pyroscope.configure(
    application_name="casare-rpa-robot",
    server_address="http://pyroscope:4040",
    tags={
        "env": "production",
        "robot_name": robot_name,
    }
)
```

Provides:
- Continuous flame graph collection
- Compare profiles between time periods
- Correlate with metrics/traces

---

## 7. Practical Recommendations

### For CasareRPA Canvas (Current Focus)

1. **Profile Event Loop**: Use yappi with WALL clock to find slow event handlers
2. **Monitor Timer Callbacks**: Viewport culling timer already optimized (33ms)
3. **Track Qt Signal Overhead**: Use py-spy during heavy node manipulation
4. **Memory for Large Workflows**: Scalene when 100+ nodes cause issues

### Quick Profiling Commands

```bash
# Development: Quick flame graph
py-spy record -o canvas_profile.svg -- python run.py

# Development: Async-aware stats
python -c "import yappi; yappi.set_clock_type('WALL'); yappi.run(exec(open('run.py').read())); yappi.get_func_stats().print_all()"

# Production: Attach to running canvas
py-spy top --pid $(pgrep -f casare_rpa)
```

---

## 8. Sources

- [py-spy GitHub](https://github.com/benfred/py-spy)
- [yappi GitHub](https://github.com/sumerc/yappi)
- [yappi Coroutine Profiling Documentation](https://github.com/sumerc/yappi/blob/master/doc/coroutine-profiling.md)
- [Austin GitHub](https://github.com/P403n1x87/austin)
- [Airspeed Velocity Documentation](https://asv.readthedocs.io/en/stable/)
- [Bencher pytest-benchmark Guide](https://bencher.dev/learn/benchmarking/python/pytest-benchmark/)
- [Scalene GitHub](https://github.com/plasma-umass/scalene)
- [Deterministic and Statistical Python Profiling](https://p403n1x87.github.io/deterministic-and-statistical-python-profiling.html)

---

## Summary

| Question | Answer |
|----------|--------|
| Best for async Qt? | **yappi** (native asyncio, wall/CPU time) |
| Best for production? | **py-spy** (zero overhead, flame graphs) |
| Best for line-level? | **line_profiler** (after identifying hot function) |
| Best for regression? | **asv** (historical tracking) + **pytest-benchmark** (CI) |
| Best for memory? | **Scalene** (combined CPU+memory) |
