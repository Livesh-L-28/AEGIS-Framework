# GitHub Providers & Webhooks

```python
from aegis.providers import GitHubConfig
from aegis.providers.production import GitHubDeploymentProvider, GitHubWebhookHandler

config = GitHubConfig(token="...")
deployments = GitHubDeploymentProvider(config, "owner", "repo")
webhook_handler = GitHubWebhookHandler(secret="...")
```
