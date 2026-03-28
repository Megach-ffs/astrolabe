import streamlit as sl
from datetime import datetime


class TransformLog:

    SESSION_KEY = "transform_log"
    SNAPSHOTS_KEY = "df_snapshots"

    @staticmethod
    def init_session():
        if TransformLog.SESSION_KEY not in sl.session_state:
            sl.session_state[TransformLog.SESSION_KEY] = []
        if TransformLog.SNAPSHOTS_KEY not in sl.session_state:
            sl.session_state[TransformLog.SNAPSHOTS_KEY] = []

    @staticmethod
    def add_step(operation: str, params: dict, columns: list, df_before=None):
        TransformLog.init_session()

        step = {
            "step_number": len(sl.session_state[TransformLog.SESSION_KEY]) + 1,
            "operation": operation,
            "params": params,
            "columns": columns,
            "timestamp": datetime.now().isoformat(),
        }
        sl.session_state[TransformLog.SESSION_KEY].append(step)

        if df_before is not None:
            sl.session_state[TransformLog.SNAPSHOTS_KEY].append(df_before.copy())

    @staticmethod
    def undo_last():
        TransformLog.init_session()

        log = sl.session_state[TransformLog.SESSION_KEY]
        snapshots = sl.session_state[TransformLog.SNAPSHOTS_KEY]

        if not log or not snapshots:
            return None

        sl.session_state[TransformLog.SESSION_KEY].pop()
        restored_df = sl.session_state[TransformLog.SNAPSHOTS_KEY].pop()

        return restored_df

    @staticmethod
    def reset_all(df_original):
        sl.session_state[TransformLog.SESSION_KEY] = []
        sl.session_state[TransformLog.SNAPSHOTS_KEY] = []
        return df_original.copy()

    @staticmethod
    def get_log() -> list:
        TransformLog.init_session()
        return sl.session_state[TransformLog.SESSION_KEY]

    @staticmethod
    def get_log_summary() -> str:
        log = TransformLog.get_log()
        if not log:
            return "No transformations applied yet."

        lines = []
        for step in log:
            cols = ", ".join(step["columns"]) if step["columns"] else "all"
            lines.append(
                f"**Step {step['step_number']}**: {step['operation']} "
                f"on [{cols}] — {step['timestamp']}"
            )
        return "\n".join(lines)

    @staticmethod
    def to_dict() -> list:
        return TransformLog.get_log()
