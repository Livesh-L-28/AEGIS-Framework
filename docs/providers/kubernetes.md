# Kubernetes Provider

```python
from aegis.providers import KubernetesConfig
from aegis.providers.production import KubernetesProvider

config = KubernetesConfig(read_only=True)
k8s = KubernetesProvider(config)
```
