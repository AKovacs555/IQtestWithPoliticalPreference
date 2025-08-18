import math
from typing import Optional

def safe_float(x: Optional[float]) -> Optional[float]:
    if x is None:
        return None
    return x if math.isfinite(x) else None

def to_2f(x: Optional[float]) -> Optional[float]:
    x = safe_float(x)
    return round(x, 2) if x is not None else None
