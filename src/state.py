import pandas as pd
from typing import TypedDict, List
class APAState(TypedDict):
    """LangGraph iş akışı durumunu temsil eder."""
    df: pd.DataFrame
    current_row_index: int
    max_rows: int
    form_labels: List[str]
    current_plan: dict
    error_message: str