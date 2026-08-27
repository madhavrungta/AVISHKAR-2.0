from __future__ import annotations

import pytest


@pytest.fixture
def firms_csv() -> str:
    """Mocked FIRMS-shaped CSV used only by tests."""

    return "\n".join(
        [
            "latitude,longitude,bright_ti4,scan,track,acq_date,acq_time,satellite,instrument,confidence,version,bright_ti5,frp,daynight",
            "22.5726,88.3639,330.1,0.4,0.5,2026-08-20,530,NPP,VIIRS,n,2.0NRT,290.2,12.5,D",
        ]
    )

