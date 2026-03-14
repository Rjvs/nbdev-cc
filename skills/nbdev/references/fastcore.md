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
    "Process data in various formats."
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
    "Apply transformation function to data."
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

### `@patch_to` for Special Methods

Use `@patch_to` when `@patch` can't infer the target class — classmethods, staticmethods, properties, and methods with complex signatures:

```python
#| export
@patch_to(DataProcessor)
@classmethod
def from_file(cls, path: Path):
    "Load data from a file."
    return cls(Path(path).read_text().splitlines())
```

```python
#| export
@patch_to(DataProcessor)
@property
def size(self):
    "Number of items in the data."
    return len(self.data)
```

```python
dp = DataProcessor.from_file('data.txt')
test_eq(dp.size, 10)
```

**Rule of thumb**: use `@patch` for regular instance methods (the type annotation on `self` tells it the target); use `@patch_to(ClassName)` for classmethods, staticmethods, properties, and any method where `self` isn't the first parameter.

---

## `docments` — Parameter Documentation

nbdev uses fastcore's `docments` style: inline comments in the function signature instead of docstring parameter sections. This is the preferred way to document parameters in nbdev projects.

### How It Works

```python
#| export
def connect(
    host: str,          # Server hostname or IP address
    port: int = 5432,   # Port number (1-65535)
    timeout: float = 30.0,  # Connection timeout in seconds
    retries: int = 3,       # Number of retry attempts
) -> Connection:
    "Establish a connection to the remote server."
    ...
```

- The **one-line docstring** describes what the function does
- The **inline comments** describe each parameter
- nbdev/Quarto renders both into clean documentation tables automatically

### Classes with `store_attr`

```python
#| export
class DataLoader:
    "Load and iterate over batches of data."
    def __init__(self,
        path: Path,           # Path to the data directory
        batch_size: int = 32, # Number of items per batch
        shuffle: bool = True, # Randomize order each epoch
    ):
        store_attr()
```

### Why Not Docstring `Parameters:` Sections?

Traditional `Parameters` / `Args` sections in docstrings:
- Duplicate the signature (type and default are already there)
- Drift out of sync with the actual code
- Require more vertical space

`docments` keeps parameter documentation in one place — the signature — and nbdev renders it automatically.

---

## `store_attr` — Eliminate `__init__` Boilerplate

Auto-stores all parameters as instance attributes:

```python
#| export
class Config:
    "Application configuration."
    def __init__(self,
        db_url: str,      # Database connection URL
        debug: bool = False,  # Enable debug mode
        workers: int = 4,    # Number of worker threads
    ):
        store_attr()
        # self.db_url, self.debug, self.workers are now set
```

### Selective Storage

```python
store_attr('db_url,workers')   # Only store these
store_attr(but='_internal')    # Store all except _internal
```

### With Additional Init Logic

```python
def __init__(self, path, batch_size=32):
    store_attr()
    self._cache = {}  # Additional setup after store_attr
```

---

## `@delegates` — Explicit Parameter Passing

Replace opaque `**kwargs` with explicit parameters in wrapper functions. Particularly useful in nbdev because it makes the generated documentation show all available parameters.

```python
#| export
class Base:
    def __init__(self,
        a: int = 1,   # First param
        b: str = 'x', # Second param
    ): store_attr()

#| export
@delegates(Base.__init__)
class Child(Base):
    def __init__(self,
        c: float = 0.5,  # New param specific to Child
        **kwargs
    ):
        super().__init__(**kwargs)
        store_attr('c')
```

Without `@delegates`, docs for `Child.__init__` would only show `c` and `**kwargs`. With it, `a` and `b` appear explicitly in the signature and documentation.

### Delegating to a Function

```python
#| export
def create_model(layers: int = 3, dropout: float = 0.1): ...

@delegates(create_model)
def train(epochs: int = 10, **kwargs):
    "Train with all create_model params available."
    model = create_model(**kwargs)
    ...
```

---

## `basic_repr` — Simple `__repr__`

Generate a `__repr__` method from attribute names:

```python
#| export
class Point:
    "A 2D point."
    def __init__(self, x: float, y: float):
        store_attr()
    __repr__ = basic_repr('x,y')
```

```python
p = Point(1.0, 2.5)
p  # Point(x=1.0, y=2.5)
```

Useful for making notebook output readable — when you display an object in a cell, `basic_repr` gives a clean, informative representation.

---

## `GetAttr` — Attribute Delegation

For composition patterns where one class wraps another:

```python
#| export
class ModelWrapper(GetAttr):
    "Wrap a model with additional tracking."
    _default = 'model'  # Attribute to delegate to

    def __init__(self,
        model,            # The model to wrap
        name: str = '',   # Optional name for logging
    ):
        store_attr()
```

```python
# Attribute access delegates to self.model
wrapper = ModelWrapper(some_model, name='v1')
wrapper.predict(x)  # Calls some_model.predict(x)
```

---

## Testing in Notebooks

fastcore's test utilities are designed for the notebook workflow — they give clear
error messages and run inline rather than in a separate test file.

### The Workflow

Every export cell should be followed by test cells:

```python
#| export
def add(a, b):
    "Add two numbers."
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
| `test_close(a, b, eps=1e-3)` | Assert within tolerance |
| `test_fail(f)` | Assert `f()` raises an exception |
| `test_fail(f, contains="msg")` | Assert exception contains "msg" |
| `test_is(a, b)` | Assert `a is b` |
| `test_stdout(f, exp)` | Assert `f()` prints `exp` |

---

## `L` — Enhanced Lists

`L` is a drop-in replacement for `list` with functional methods. Common in nbdev notebooks for data processing:

```python
items = L([1, 2, 3, 4, 5])
items.map(lambda x: x * 2)       # L([2, 4, 6, 8, 10])
items.filter(lambda x: x > 3)    # L([4, 5])
items.sorted(key=lambda x: -x)   # L([5, 4, 3, 2, 1])
items.unique()                    # L([1, 2, 3, 4, 5])
```

### NumPy-style Indexing

```python
items[[0, 2, 4]]   # L([1, 3, 5])
items[True, False, True, False, True]  # L([1, 3, 5])
```

---

## Common Imports

Typical fastcore imports at the top of an nbdev notebook:

```python
#| export
from fastcore.basics import patch, patch_to, store_attr, GetAttr, basic_repr
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
| `@patch_to` | `fastcore.basics` | Patch classmethods, properties, complex signatures |
| `@delegates` | `fastcore.meta` | Replace `**kwargs` with explicit params |
| `store_attr` | `fastcore.basics` | Auto-store `__init__` arguments |
| `basic_repr` | `fastcore.basics` | Simple `__repr__` from attribute names |
| `L` | `fastcore.foundation` | Enhanced list with `.map()`, `.filter()` |
| `test_eq` | `fastcore.test` | Test equality (clear error messages) |
| `@typedispatch` | `fastcore.dispatch` | Multiple dispatch by argument type |
| `GetAttr` | `fastcore.basics` | Attribute delegation for composition |
| `docments` | *(signature style)* | Inline param docs via comments |
