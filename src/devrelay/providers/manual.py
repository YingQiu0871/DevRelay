"""Manual reviewer provider.

A manual reviewer never runs automatically: DevRelay writes a
``review-NN-request.md`` into the task artifacts and stops at REVIEWING.
The human imports the result with ``devrelay review import review.json``.
"""

from __future__ import annotations

from devrelay.artifacts.renderer import (
    ReviewBundle,
    render_review_request_md,
)
from devrelay.providers.base import ReviewerProvider


class ManualReviewer(ReviewerProvider):
    name = "manual"

    @property
    def automatic(self) -> bool:
        return False

    def prepare_request(
        self, bundle: ReviewBundle, review_number: int | None = None
    ) -> str:
        return render_review_request_md(bundle, review_number=review_number or 1)
