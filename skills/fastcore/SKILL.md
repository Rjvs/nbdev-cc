---
name: fastcore
description: |
  Python library extending the language with features from Julia (multiple dispatch), Ruby (mixins/patching),
  and Haskell (currying, binding). Provides @patch, delegates, store_attr, L, type dispatch, enhanced testing,
  parallel processing, and functional programming utilities. Foundational for fast.ai projects including
  nbdev and FastHTML. Generally useful in any Python project that benefits from concise, expressive code.
license: Apache-2.0
allowed-tools: Read, Write, Edit, Grep, Glob, Bash
metadata:
  author: Robert Spencer, Claude
  version: "1.0.0"
  sources:
    - "[fastcore Documentation](https://fastcore.fast.ai/)"
    - "[fastcore LLM Context](https://fastcore.fast.ai/llms-ctx.txt)"
    - "[fastcore Quick Tour](https://fastcore.fast.ai/tour.html)"
    - "[Hamel Husain - fastcore Blog Post](https://fastpages.fast.ai/fastcore/)"
---

# fastcore Python Extensions Skill

You are working with fastcore, a library that extends Python with features from other languages. fastcore follows fast.ai style: concise code, liberal use of `import *`, minimize ceremony.

## Core Philosophy

**Concise over verbose**: Reduce boilerplate. `store_attr()` replaces five lines of `self.x = x`. `@patch` replaces subclassing. `L` replaces verbose list operations.

**Transparent APIs**: Use `@delegates` to replace opaque `**kwargs` with explicit parameters. IDE support and documentation should never be sacrificed for flexibility.

**Safe wildcard imports**: All fastcore modules define `__all__`. Use `from fastcore.module import *` freely — the library is designed for it.

**Tests as documentation**: Use `test_eq`, `test_ne`, etc. — they show expected behavior while verifying correctness.

---

## The `@patch` Decorator

The most important fastcore feature. Adds methods to any class (including built-ins and third-party classes) without subclassing, using type annotations to specify the target class.

```python
from fastcore.basics import patch

class Dog:
    def __init__(self, name): self.name = name

@patch
def bark(self: Dog):
    """Make the dog bark."""
    return f"{self.name} says woof!"

Dog("Rex").bark()  # "Rex says woof!"
```

### Patching external classes

```python
@patch
def num_items(self: Path): return len(self.ls())

Path('images').num_items()  # 6
```

### `@patch_to` for complex signatures

When the type annotation approach doesn't fit (e.g. classmethods, properties):

```python
from fastcore.basics import patch_to

@patch_to(Dog, cls_method=True)
def create(cls, name): return cls(name.title())

Dog.create("rex")  # Dog with name "Rex"
```

---

## `store_attr` — Eliminate `__init__` Boilerplate

```python
from fastcore.basics import store_attr

class ProductPage:
    def __init__(self, author, price, cost):
        store_attr()  # equivalent to self.author, self.price, self.cost = author, price, cost

# Selective storage
class Config:
    def __init__(self, host, port, debug=False, **kwargs):
        store_attr('host,port,debug')  # only store named attrs
```

---

## `@delegates` — Transparent Keyword Arguments

Replaces `**kwargs` with explicit parameters from the delegated function, preserving IDE autocomplete and documentation.

```python
from fastcore.meta import delegates

def baz(a, b=2, c=3, d=4): return a + b + c

@delegates(baz)
def foo(c, a, **kwargs): return c + baz(a, **kwargs)

# foo's signature now shows: foo(c, a, b=2, d=4)
# 'c' is excluded since foo defines it explicitly
```

### Class delegation

```python
@delegates()
class Child(Parent):
    def __init__(self, extra_param, **kwargs):
        super().__init__(**kwargs)
        self.extra_param = extra_param
```

---

## `L` — Enhanced List

A drop-in replacement for `list` with NumPy-like indexing, method chaining, and functional methods.

```python
from fastcore.foundation import L

# Construction
L(1, 2, 3)           # (#3) [1,2,3]
L(range(5))          # (#5) [0,1,2,3,4]
L.range(20).shuffle() # (#20) [5,1,9,10,18,...]

# NumPy-style indexing
p = L.range(20)
p[2, 4, 6]           # (#3) [2,4,6]
p[True, False, True]  # boolean mask indexing

# Functional methods
p.filter(lambda x: x > 10)
p.map(lambda x: x * 2)
p.argwhere(ge(15))   # indices where condition is true
p.sorted(key='name') # sort by attribute

# Arithmetic
1 + L(2, 3, 4)       # (#4) [1,2,3,4]
L(1, 2) + L(3, 4)    # (#4) [1,2,3,4]
```

---

## Type Dispatch (`@typedispatch`)

Multiple dispatch based on argument types — like Julia's dispatch system.

```python
from fastcore.dispatch import typedispatch

@typedispatch
def process(x: int, y: int): return x + y

@typedispatch
def process(x: str, y: str): return f"{x} {y}"

process(1, 2)           # 3
process("hello", "world") # "hello world"
```

---

## Testing Utilities

Prefer fastcore test functions over bare `assert` — they provide clear error messages and work well with nbdev.

```python
from fastcore.test import test_eq, test_ne, test_close, test_fail, test_stdout

test_eq([0, 1, 2], range(3))       # equality (works across types)
test_ne(1, 2)                       # inequality
test_close(0.1 + 0.2, 0.3)         # float comparison with tolerance
test_fail(lambda: 1/0)              # verify exception raised
test_fail(lambda: int("x"), contains="invalid literal")  # check error message
test_stdout(lambda: print("hi"), "hi")  # verify stdout output
```

---

## `GetAttr` — Transparent Attribute Delegation

Allows tab-completion and `dir()` to work correctly when delegating to a wrapped object.

```python
from fastcore.basics import GetAttr

class Author:
    def __init__(self, name): self.name = name

class ProductPage(GetAttr):
    _default = 'author'
    def __init__(self, author, price):
        self.author, self.price = author, price

p = ProductPage(Author("Jeremy"), 1.50)
p.name  # "Jeremy" — delegated to author
```

---

## `basic_repr` — Simple Object Representations

```python
from fastcore.basics import basic_repr

class Config:
    def __init__(self, host, port):
        store_attr()
    __repr__ = basic_repr('host,port')

Config("localhost", 8080)  # Config(host='localhost', port=8080)
```

---

## Parallel Processing

Enhanced `ProcessPoolExecutor` and `ThreadPoolExecutor` with `max_workers=0` for easy serial debugging.

```python
from fastcore.parallel import parallel, threaded

# Simple parallel processing with progress bar
results = parallel(process_item, items, n_workers=4, progress=True)

# Decorator for background execution
@threaded
def background_task(x): return expensive_operation(x)
future = background_task(42)
result = future.result()  # blocks until complete
```

---

## Functional Programming Utilities

```python
from fastcore.basics import compose, maps, filter_ex, first

# Function composition
process = compose(str.strip, str.lower, str.split)

# Map multiple functions
maps(items, func1, func2)

# Filter with function
filter_ex(items, lambda x: x > 0)

# First matching item
first(items, lambda x: x.name == "target")
```

### Curried comparison operators

```python
from fastcore.basics import gt, ge, lt, le, eq

# Two args: normal comparison
gt(3, 2)  # True

# One arg: returns curried function
over_10 = gt(10)
L(5, 15, 8, 20).filter(over_10)  # (#2) [15,20]
```

---

## Enhanced `Path`

fastcore extends `pathlib.Path` with additional methods:

```python
from fastcore.xtras import Path

p = Path('data')
p.ls()          # L of contents (returns L, not list)
p.read_json()   # parse JSON file
p.write_json(d) # write JSON file
p.mk_write(data) # create parent dirs + write
```

---

## `docments` — Parameter Documentation

Document parameters using comments in the function signature:

```python
from fastcore.docments import docments

def connect(
    host: str,  # Server hostname
    port: int = 5432,  # Server port number
    ssl: bool = True,  # Use SSL connection
): ...

docments(connect)
# {'host': 'Server hostname', 'port': 'Server port number', 'ssl': 'Use SSL connection'}
```

---

## `Transform` and `Pipeline`

Building blocks for data processing pipelines with type dispatch, reversibility, and composition.

```python
from fastcore.transform import Transform, Pipeline

class Normalize(Transform):
    def encodes(self, x): return (x - self.mean) / self.std
    def decodes(self, x): return x * self.std + self.mean

# Simple transforms via decorator
@Transform
def double(x): return x * 2

# Compose into pipeline
pipe = Pipeline([double, Normalize()])
pipe(3)       # apply forward
pipe.decode(y) # apply reverse
```

---

## CLI Creation

Turn functions into command-line tools:

```python
from fastcore.script import call_parse

@call_parse
def main(
    name: str,       # User's name
    count: int = 1,  # Number of greetings
    shout: bool = False, # Use uppercase
):
    """Greet someone."""
    msg = f"Hello, {name}!" * count
    print(msg.upper() if shout else msg)
```

---

## `funcs_kwargs` — Customize Class Behavior Without Subclassing

```python
from fastcore.meta import funcs_kwargs

@funcs_kwargs
class DataLoader:
    _methods = ['collate_fn', 'worker_init_fn']
    def __init__(self, **kwargs):
        assert not kwargs, f'Unknown args: {kwargs}'

# Users pass functions instead of subclassing
dl = DataLoader(collate_fn=my_collate)
```

---

## Common Import Patterns

```python
# Everything (safe, uses __all__)
from fastcore.basics import *

# Targeted imports for specific features
from fastcore.basics import patch, store_attr, GetAttr, basic_repr, compose
from fastcore.meta import delegates, funcs_kwargs
from fastcore.foundation import L
from fastcore.dispatch import typedispatch
from fastcore.test import test_eq, test_ne, test_close, test_fail
from fastcore.parallel import parallel, threaded
from fastcore.transform import Transform, Pipeline
from fastcore.script import call_parse
```

---

## Quick Reference

| Feature | Import | One-liner |
|---------|--------|-----------|
| `@patch` | `fastcore.basics` | Add methods to any class via type annotation |
| `store_attr()` | `fastcore.basics` | Auto-store `__init__` params as attributes |
| `@delegates` | `fastcore.meta` | Replace `**kwargs` with explicit params |
| `L` | `fastcore.foundation` | Enhanced list with NumPy-like indexing |
| `@typedispatch` | `fastcore.dispatch` | Multiple dispatch by argument types |
| `test_eq` | `fastcore.test` | Equality test with clear error messages |
| `GetAttr` | `fastcore.basics` | Transparent attribute delegation |
| `basic_repr` | `fastcore.basics` | Simple `__repr__` from attribute names |
| `parallel` | `fastcore.parallel` | Parallel map with progress bar |
| `@threaded` | `fastcore.parallel` | Run function in background thread |
| `compose` | `fastcore.basics` | Function composition |
| `Transform` | `fastcore.transform` | Reversible, type-dispatched transform |
| `Pipeline` | `fastcore.transform` | Compose transforms into pipeline |
| `call_parse` | `fastcore.script` | Function to CLI tool |
| `Path.ls()` | `fastcore.xtras` | List directory as `L` |

---

## Reference Files

For detailed specifications and the full API, consult:
- `references/api-reference.md` - Module-by-module API summary
