"""Task Workspace Baseline machinery (v0.1 RC hardening).

DevRelay captures the real task-start workspace state (HEAD + user's staged,
unstaged, deleted, renamed, untracked and binary changes) into durable,
restorable artifacts - **without ever mutating the user's real git index**.
All index manipulation happens through a temporary ``GIT_INDEX_FILE``.

Responsibilities are separated:

* :mod:`devrelay.baseline.store`      - durable artifact persistence/loading
* :mod:`devrelay.baseline.capture`    - building trees from the real worktree
* :mod:`devrelay.baseline.comparator` - task-relative diff + reconstruction
* :mod:`devrelay.baseline.guard`      - repository policy postcondition checks
* :mod:`devrelay.baseline.service`    - facade used by the pipeline engine
"""

from __future__ import annotations
