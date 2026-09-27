---
schema_version: 1
open_count: 1
waived_count: 0
fixed_count: 0
total_count: 1
last_updated: 2026-09-27T22:04:18.109Z
---

# Broken Windows Ledger

> Cross-phase defect register. With `workflow.windows_enforce` enabled, `/gsd-ship` blocks while `open_count > 0`.
> Waive with `gsd-tools windows waive <id> "<reason>"` (reason required).
> Mark fixed with `gsd-tools windows fixed <id>`.

| id | phase | kind | file | line | description | status | reason | recorded_at | resolved_at |
|----|-------|------|------|------|-------------|--------|--------|-------------|-------------|
| 1 | 02 | deviation | frontend/src/features/dashboard/routes.tsx |  | BO_MON dashboard menu label kept as shared 'Tổng quan' instead of role-specific 'Tổng quan toàn khoa' — MenuEntry contract supports one label per route; defer per-role label to whichever plan renders the sidebar | open |  | 2026-09-27T22:04:18.109Z |  |

````json
[
  {
    "id": 1,
    "kind": "deviation",
    "phase": "02",
    "file": "frontend/src/features/dashboard/routes.tsx",
    "line": null,
    "description": "BO_MON dashboard menu label kept as shared 'Tổng quan' instead of role-specific 'Tổng quan toàn khoa' — MenuEntry contract supports one label per route; defer per-role label to whichever plan renders the sidebar",
    "status": "open",
    "reason": "",
    "recorded_at": "2026-09-27T22:04:18.109Z",
    "resolved_at": null,
    "milestone": null
  }
]
````
