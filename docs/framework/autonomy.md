# Autonomy Tiers & Safety Boundaries

AEGIS enforces bounded autonomy tiers:

| Tier | Name | Behavior |
|---|---|---|
| `LEVEL_0` | Observe Only | Automated actions disabled entirely |
| `LEVEL_1` | Recommend | Actions require explicit human signoff |
| `LEVEL_2` | Auto-Execute Low Risk | Low risk actions permitted automatically |
| `LEVEL_3` | Auto-Execute Approved Classes | Bounded medium risk actions allowed |

> **Critical Safety Invariant**: `LEVEL_4` (unrestricted autonomy) is permanently omitted and unsupported by architecture design.
