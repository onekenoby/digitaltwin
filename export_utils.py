# export_utils.py
import pandas as pd
import json

def df_from_segments(segments):
    """
    Convert segment list to a DataFrame.
    """
    return pd.DataFrame(segments)

def df_to_csv(df: pd.DataFrame) -> str:
    return df.to_csv(index=False)

def df_to_json(df: pd.DataFrame, indent: int = 2) -> str:
    return json.dumps(df.to_dict(orient="records"), indent=indent)
