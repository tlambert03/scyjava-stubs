# scyjava-stubs

[![License](https://img.shields.io/pypi/l/scyjava-stubs.svg?color=green)](https://github.com/tlambert03/scyjava-stubs/raw/main/LICENSE)
[![PyPI](https://img.shields.io/pypi/v/scyjava-stubs.svg?color=green)](https://pypi.org/project/scyjava-stubs)
[![Python Version](https://img.shields.io/pypi/pyversions/scyjava-stubs.svg?color=green)](https://python.org)
[![CI](https://github.com/tlambert03/scyjava-stubs/actions/workflows/ci.yml/badge.svg)](https://github.com/tlambert03/scyjava-stubs/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/tlambert03/scyjava-stubs/branch/main/graph/badge.svg)](https://codecov.io/gh/tlambert03/scyjava-stubs)

Type stub generator for maven artifacts

```sh
pip install git+https://github.com/tlambert03/scyjava-stubs
```

Then generate stubs:

```sh
scyjava-stubgen org.scijava:parsington:3.1.0
```

then use them:

```python
from scyjava_stubs.modules.org.scijava.parsington import Function

f = Function(1)
print(f.isPrefix())
```
