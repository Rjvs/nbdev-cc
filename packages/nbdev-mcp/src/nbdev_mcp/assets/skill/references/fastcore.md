# fastcore in nbdev Projects

nbdev projects use fastcore extensively. For the complete fastcore API, see the
**fastcore** skill. This reference covers only the nbdev-specific patterns — how
fastcore utilities integrate with notebooks, directives, and literate programming.

---

## `@patch` in Notebooks

`@patch` is the most important fastcore feature for nbdev. It enables the core
literate programming pattern: define a class, then introduce each method in its
own cell with prose and tests between them.

### The Pattern

```python
#| export
class DataProcessor:
    """Process data in various formats."""
    def __init__(self, data):
        self.data = data
```

```markdown
The `DataProcessor` class holds raw data. Now let's add a way to transform it:
```

```python
#| export
@patch
def transform(self: DataProcessor, fn):
    """Apply transformation function to data."""
    return fn(self.data)
```

```python
# Test the method immediately
dp = DataProcessor([1, 2, 3])
test_eq(dp.transform(sum), 6)
```

Each method gets its own `#| export` cell, its own explanation, and its own tests.
This is what makes nbdev documentation read like a tutorial rather than an API listing.

### Why Not Just Define Methods Inside the Class?

In a regular `.py` file, you'd put all methods in the class body. In nbdev:

- A 200-line class in one cell is unreadable as documentation
- You can't interleave prose and tests between methods
- You can't show the reasoning behind each method's design

---

## Testing in Notebooks

fastcore's test utilities are designed for the notebook workflow — they give clear
error messages and run inline rather than in a separate test file.

### The Workflow

Every export cell should be followed by test cells:

```python
#| export
def add(a, b):
    """Add two numbers."""
    return a + b
```

```python
# Tests in the next cell — no directive needed
test_eq(add(1, 2), 3)
test_eq(add(-1, 1), 0)
test_eq(add(0, 0), 0)
```

### Test Philosophy

- Tests run top-to-bottom; first failure stops execution
- Use `test_eq`, `test_ne`, `test_fail` — not bare `assert` (better error messages)
- Tests ARE the usage examples — write them to teach, not just verify
- Every exported function should have tests in the cell below it
- `nbdev_test` runs all test cells across all notebooks

### Quick Reference

| Function | Use |
|----------|-----|
| `test_eq(a, b)` | Assert `a == b` |
| `test_ne(a, b)` | Assert `a != b` |
| `test_close(a, b)` | Assert approximately equal (floats) |
| `test_fail(f)` | Assert `f()` raises an exception |
| `test_fail(f, contains="msg")` | Assert exception contains "msg" |
| `test_is(a, b)` | Assert `a is b` |

---

## Common Imports

Typical fastcore imports at the top of an nbdev notebook:

```python
#| export
from fastcore.basics import patch, store_attr, GetAttr
from fastcore.meta import delegates
from fastcore.foundation import L
from fastcore.test import test_eq, test_ne, test_fail, test_close
```

---

## Essential Utilities Quick Reference

These are the fastcore features most commonly used in nbdev. See the **fastcore**
skill for full documentation of each.

| Feature | Import | Purpose |
|---------|--------|---------|
| `@patch` | `fastcore.basics` | Add methods to classes across cells |
| `@delegates` | `fastcore.meta` | Replace `**kwargs` with explicit params |
| `store_attr` | `fastcore.basics` | Auto-store `__init__` arguments |
| `L` | `fastcore.foundation` | Enhanced list with `.map()`, `.filter()` |
| `test_eq` | `fastcore.test` | Test equality (clear error messages) |
| `@typedispatch` | `fastcore.dispatch` | Multiple dispatch by argument type |
| `GetAttr` | `fastcore.basics` | Attribute delegation for composition |
