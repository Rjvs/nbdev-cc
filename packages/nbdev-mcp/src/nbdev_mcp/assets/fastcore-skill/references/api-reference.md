# fastcore API Reference

Module-by-module summary of all fastcore functions and classes. For full details and examples, see `inspo/fastcore/llms-ctx.txt`.

---

## fastcore.basics

> Core utilities used across all fast.ai projects

### Key Functions

| Function | Description |
|----------|-------------|
| `store_attr(names, ...)` | Store params from calling context into `self` attrs |
| `patch(f)` | Add `f` to the first parameter's class (via type annotation) |
| `patch_to(cls, ...)` | Add `f` to `cls` directly |
| `compose(*funcs)` | Create composed function from `funcs` |
| `GetAttr` | Base class for transparent attribute delegation |
| `basic_repr(flds)` | Minimal `__repr__` from field names |
| `delegates(to, keep, but)` | (re-exported from meta) Replace `**kwargs` with params from `to` |

### Utility Functions

| Function | Description |
|----------|-------------|
| `ifnone(a, b)` | `b` if `a` is None else `a` |
| `listify(o)` | Convert `o` to a list |
| `chunked(it, chunk_sz)` | Return batches from iterator |
| `flatten(o)` | Concatenate all collections as generator |
| `merge(*ds)` | Merge all dictionaries |
| `groupby(x, key, val)` | Like `itertools.groupby` but doesn't need sorting |
| `filter_ex(iterable, f)` | Enhanced `filter` with negate and kwargs |
| `first(x, f)` | First element, optionally filtered |
| `maps(*args)` | `map` with composed functions |
| `partialler(f, ...)` | Like `partial` but copies docstring |
| `AttrDict` | Dict with attribute access |
| `str_enum(name, *vals)` | Create StrEnum type |
| `NotStr` | Behaves like str but isn't instance of str |

### Comparison Operators (curried)

`gt`, `ge`, `lt`, `le`, `eq`, `ne` — two args: normal comparison; one arg: returns curried function.

---

## fastcore.meta

> Metaclasses and signature manipulation

| Item | Description |
|------|-------------|
| `delegates(to, keep, but)` | Replace `**kwargs` with params from `to` |
| `use_kwargs(names, keep)` | Replace `**kwargs` with named params |
| `funcs_kwargs(as_method)` | Replace class methods via kwargs |
| `FixSigMeta` | Metaclass fixing signatures on `__new__` override |
| `PrePostInitMeta` | Calls `__pre_init__` and `__post_init__` |
| `AutoInit` | No need for `super().__init__()` |
| `NewChkMeta` | Avoid recreating object passed to constructor |

---

## fastcore.foundation

> The `L` class and helpers

| Item | Description |
|------|-------------|
| `L` | Enhanced list with NumPy-like indexing |
| `Config` | Reading/writing ConfigParser ini files |
| `CollBase` | Base class for list composition |
| `working_directory(path)` | Context manager to change working directory |
| `coll_repr(c, max_n)` | String repr of collection |

### `L` Methods

`map`, `filter`, `argwhere`, `argfirst`, `sorted`, `unique`, `shuffle`, `cycle`, `zip`, `zipwith`, `concat`, `reduce`, `sum`, `product`, `enumerate`, `renumerate`, `map_dict`, `itemgot`, `attrgot`, `starmap`, `val2idx`, `setattrs`

---

## fastcore.dispatch

> Type dispatch (multiple dispatch by argument types)

| Item | Description |
|------|-------------|
| `TypeDispatch` | Dict-like; `__getitem__` matches types via `issubclass` |
| `DispatchReg` | Global registry for TypeDispatch objects |
| `cast(x, typ)` | Cast `x` to type `typ` |
| `retain_type(new, old)` | Cast `new` to type of `old` if superclass |

---

## fastcore.test

> Testing helpers for notebooks

| Function | Description |
|----------|-------------|
| `test_eq(a, b)` | Test `a == b` (works across types) |
| `test_eq_type(a, b)` | Test `a == b` and same type |
| `test_ne(a, b)` | Test `a != b` |
| `test_close(a, b, eps)` | Test `a` within `eps` of `b` |
| `test_is(a, b)` | Test `a is b` |
| `test_fail(f, ...)` | Test that `f()` raises exception |
| `test_stdout(f, exp)` | Test stdout output |
| `test_shuffled(a, b)` | Test same items, different order |
| `test(a, b, cmp)` | General comparison test |
| `ExceptionExpected` | Context manager for expected exceptions |

---

## fastcore.parallel

> Threading and multiprocessing

| Item | Description |
|------|-------------|
| `parallel(f, items, ...)` | Apply `f` in parallel with progress bar |
| `threaded(process)` | Run in thread (or process), return Future |
| `startthread(f)` | Start thread immediately |
| `ThreadPoolExecutor` | Enhanced: `max_workers=0` for serial execution |
| `ProcessPoolExecutor` | Enhanced: `max_workers=0` for serial execution |
| `parallel_gen(cls, items)` | Parallel generator across workers |

---

## fastcore.transform

> Data transforms and pipelines

| Item | Description |
|------|-------------|
| `Transform` | Base class: `encodes`/`decodes`/`setups` methods |
| `Pipeline` | Composed sequence of transforms |
| `InplaceTransform` | Modifies in-place, returns input |
| `ItemTransform` | Always takes tuples as items |
| `compose_tfms(x, tfms)` | Apply transforms in sequence |
| `mk_transform(f)` | Convert function to Transform |

---

## fastcore.script

> CLI creation from functions

| Item | Description |
|------|-------------|
| `call_parse(func)` | Decorator: function to CLI tool |
| `Param(help, type, ...)` | Parameter annotation for CLI args |
| `anno_parser(func)` | Create ArgumentParser from annotations |

---

## fastcore.net

> Network and HTTP utilities

| Function | Description |
|----------|-------------|
| `urlopen(url, ...)` | Enhanced `urllib.request.urlopen` |
| `urlread(url, ...)` | Retrieve URL content |
| `urljson(url, ...)` | Retrieve and decode JSON |
| `urlsave(url, dest)` | Download and save file |
| `urlsend(url, verb, ...)` | Send HTTP request |
| `do_request(url, post, ...)` | GET or POST request |

---

## fastcore.xml

> XML/HTML generation (FT = "Fast Tags")

| Item | Description |
|------|-------------|
| `FT` | Fast Tag structure: `tag`, `children`, `attrs` |
| `ft(tag, *c, **kw)` | Create FT structure |
| `Html(*c, **kw)` | HTML tag with optional DOCTYPE |
| `Safe` | Mark string as safe (no escaping) |
| `to_xml(elm, ...)` | Convert FT tree to XML string |

This is the foundation of FastHTML's component system.

---

## fastcore.xtras

> Extended utilities

### Path Extensions

| Method | Description |
|--------|-------------|
| `Path.ls(n_max, file_type)` | List directory contents as `L` |
| `Path.read_json()` | Read and parse JSON |
| `Path.mk_write(data)` | Make parent dirs + write |
| `Path.readlines()` | Read lines of file |
| `Path.delete()` | Delete file/dir tree |
| `Path.relpath(start)` | Relative path as Path |

### Other Utilities

| Function | Description |
|----------|-------------|
| `dict2obj(d)` | Convert dicts to AttrDict (nested) |
| `obj2dict(d)` | Convert AttrDicts to dict (nested) |
| `loads(s)` | `json.loads` that handles None |
| `dumps(obj)` | `json.dumps`, uses ujson if available |
| `run(cmd)` | Run subprocess, return stdout |
| `globtastic(path, ...)` | Powerful glob with regex |
| `walk(path, ...)` | Generator `os.walk` with filters |
| `timed_cache(seconds)` | `lru_cache` with time expiry |
| `flexicache(*funcs)` | Customisable cache with policy functions |
| `nullable_dc(cls)` | Dataclass with UNSET defaults |
| `flexiclass(cls)` | Convert class to dataclass-like |
| `asdict(o)` | Convert to dict (dataclasses, namedtuples, etc.) |

---

## fastcore.docments

> Document parameters using comments

| Function | Description |
|----------|-------------|
| `docments(elt, full)` | Generate parameter documentation |
| `parse_docstring(sym)` | Parse numpy-style docstring |
| `get_source(s)` | Get source code for function/class |

---

## fastcore.imports

> Basic imports and environment checks

| Function | Description |
|----------|-------------|
| `is_iter(o)` | Test if usable in for loop |
| `is_coll(o)` | Test if has usable `len` |
| `noop(x)` | Do nothing |
| `in_notebook()` | Check if running in Jupyter |
| `in_colab()` | Check if running in Colab |

---

## fastcore.style

> Terminal text styling

| Item | Description |
|------|-------------|
| `Style` | Minimal terminal text styler |
| `StyleCode` | Escape sequence for styling |
