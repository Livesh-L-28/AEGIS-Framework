# Getting Started with AEGIS Framework

Welcome to the AEGIS Framework developer guide.

## Overview

AEGIS Framework is a modular library designed to provide developer primitives for building autonomous reliability engineering systems, automated incident investigation, evidence correlation, and verified remediation pipelines.

## Installation

```bash
pip install aegis-ai
```

*(During development / pre-alpha stage, install locally in editable mode):*

```bash
git clone https://github.com/Livesh-L-28/AEGIS-Framework.git
cd AEGIS-Framework
pip install -e .
```

## First Steps

```python
import aegis
from aegis import Aegis

print("Initialized AEGIS Framework version:", aegis.__version__)
client = Aegis()
```

Further detailed guides will be published as individual subsystem engines are extracted and released.
