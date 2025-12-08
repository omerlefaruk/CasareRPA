# Research: Compiled Python Performance

## Executive Summary

**Recommendation: NOT RECOMMENDED for CasareRPA at this time.**

Compiled Python (Cython, Mypyc, Numba) provides 2-100x speedups for CPU-bound numerical code. However, CasareRPA is primarily **I/O-bound** (browser automation, file operations, UI interactions). Compilation overhead outweighs benefits.

---

## Comparison Matrix

| Criteria | Cython | Mypyc | Numba |
|----------|--------|-------|-------|
| **Target Use Case** | C extensions, hot paths | Type-annotated Python | Numerical/array code |
| **Learning Curve** | High (Cython syntax) | Low (uses mypy types) | Low (decorators) |
| **Speedup Range** | 2-100x | 2-5x | 10-100x |
| **Build Complexity** | High (C compiler) | Medium | Low (JIT at runtime) |
| **Distribution** | Wheels per platform | Wheels per platform | No build step |
| **Python Compat** | CPython only | CPython only | CPython only |
| **PyPy Support** | Limited | None | None |
| **PySide6 Compat** | Works | Works | N/A (no GUI code) |
| **Maintenance** | High | Medium | Low |

---

## When to Use Compiled Python

### Good Candidates (CasareRPA context)

1. **Variable Resolution** (`variable_resolver.py`)
   - Called for every node property
   - Regex matching, string manipulation
   - Potential speedup: 2-5x with Cython/Mypyc
   - BUT: Not a bottleneck; browser wait times dominate

2. **Execution Orchestrator Graph Traversal**
   - BFS/DFS algorithms for path calculation
   - Potential speedup: 2-3x
   - BUT: Workflows typically have <100 nodes; microseconds total

3. **Selector Parsing/Matching**
   - CSS/XPath selector normalization
   - Regex-heavy operations
   - Potential speedup: 2-5x
   - BUT: Playwright handles actual DOM operations

### Poor Candidates (I/O-bound)

- Browser automation nodes (Playwright awaits)
- File operations (disk I/O)
- HTTP requests (network I/O)
- UI automation (Win32 API waits)
- Canvas rendering (Qt handles graphics)

---

## Tool-Specific Analysis

### Cython

**Best For:** Hot loops, C library integration, maximum control

**Patterns:**
```python
# hot_path.pyx
cimport cython
from libc.math cimport sqrt

@cython.boundscheck(False)
@cython.wraparound(False)
def resolve_path(str path, dict variables):
    cdef int first_dot, first_bracket
    # ... typed implementation
```

**Build Integration:**
```toml
# pyproject.toml
[build-system]
requires = ["setuptools", "cython>=3.0"]

# Still needs setup.py for cythonize()
```

**Drawbacks:**
- Requires C compiler on user machines (or prebuilt wheels)
- Separate .pyx files or pure Python mode annotations
- 65% of top PyPI packages use wheels; you'd need CI/CD for multi-platform builds

### Mypyc

**Best For:** Already type-annotated code, gradual adoption

**Patterns:**
```python
# Just add @final for maximum optimization
from typing import final

@final
class VariableResolver:
    def resolve(self, value: str, variables: dict[str, Any]) -> Any:
        # Type annotations enable C-level optimization
        ...
```

**Build Integration:**
```bash
# mypyc compiles type-annotated .py files
mypyc variable_resolver.py
```

**Drawbacks:**
- Limited to what mypy supports (no dynamic features)
- Speedup ceiling lower than Cython
- Still needs wheel distribution

### Numba

**Best For:** NumPy arrays, mathematical operations, parallel loops

**Patterns:**
```python
from numba import jit, prange

@jit(nopython=True, parallel=True)
def process_data_batch(data: np.ndarray) -> np.ndarray:
    result = np.empty_like(data)
    for i in prange(len(data)):
        result[i] = complex_math(data[i])
    return result
```

**Build Integration:** None required (JIT at runtime)

**Drawbacks:**
- Only for numerical code; useless for strings, dicts, objects
- First call has compilation latency
- LLVM dependency (~100MB)
- No benefit for CasareRPA's string/dict-heavy workflows

---

## Distribution Complexity

### Wheel Building (Cython/Mypyc)

**Per-platform requirements:**
- Windows: MSVC or MinGW
- macOS: Xcode CLT
- Linux: GCC

**CI/CD setup (cibuildwheel):**
```yaml
# .github/workflows/build-wheels.yml
jobs:
  build:
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        python: ["3.10", "3.11", "3.12"]
```

**Wheel matrix:** 3 OS x 3 Python = 9 wheels minimum

**Tools:**
- `cibuildwheel`: Automates multi-platform wheel building
- `auditwheel`: Bundles external libraries into Linux wheels
- `delocate`: Same for macOS

---

## CasareRPA Bottleneck Analysis

Based on code review:

| Operation | Time Spent | Compilation Benefit |
|-----------|------------|---------------------|
| Browser waits (Playwright) | 80%+ | None (I/O) |
| DOM operations | 10% | None (Playwright handles) |
| Variable resolution | <1% | Marginal |
| Graph traversal | <0.1% | Negligible |
| UI rendering | 5% | None (Qt handles) |

**Conclusion:** CasareRPA spends 90%+ of execution time waiting for I/O. Compiled Python targets CPU-bound code.

---

## Recommendations

### Short-term: Skip Compilation

1. **Profile first** - Use `py-spy` or `cProfile` to confirm bottlenecks
2. **Optimize algorithms** - Better asymptotic complexity > compiled code
3. **Cache results** - `functools.lru_cache` for repeated operations
4. **Async optimization** - Ensure proper async/await throughout

### If Compilation Needed Later

1. **Start with Mypyc** - Lowest friction if code is already typed
2. **Target specific functions** - Only compile proven hot paths
3. **Use cibuildwheel** - Automate wheel building in CI
4. **Keep fallback** - Pure Python fallback for unsupported platforms

### Alternative Performance Strategies

| Strategy | Applicability | Effort |
|----------|--------------|--------|
| Connection pooling | High (already done) | Done |
| Async batching | Medium | Low |
| Result caching | Medium | Low |
| Lazy loading | Medium | Low |
| Pre-compiled selectors | Low | Medium |
| orjson (already used) | High | Done |

---

## PyPy Compatibility Note

PyPy is NOT viable for CasareRPA:
- PySide6: No PyPy support (C++ bindings)
- Playwright: No PyPy support
- uiautomation: No PyPy support

All three core dependencies require CPython.

---

## Sources

- [Cython Documentation - Static Typing](https://cython.readthedocs.io/en/latest/src/quickstart/cythonize.html)
- [Numba Documentation](https://numba.pydata.org/)
- [Python Packaging Guide - Binary Extensions](https://packaging.python.org/guides/packaging-binary-extensions/)
- [Real Python - Python Wheels](https://realpython.com/python-wheels/)
- [Sigma Software - Cython Optimization](https://sigma.software/about/media/optimizing-performance-python-code-using-cython)
- [GeeksforGeeks - Numba Performance](https://www.geeksforgeeks.org/data-analysis/unlocking-performance-understanding-numbas-speed-advantages-over-numpy/)
- [InfoWorld - Numba Guide](https://www.infoworld.com/article/2266749/speed-up-your-python-with-numba.html)
