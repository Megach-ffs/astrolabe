"""Tests for the transform_log module."""

import pytest
import pandas as pd
# import numpy as np  # will be used in future phases


@pytest.fixture(autouse=True)
def clean_session_state():
    """
    Mock streamlit session_state for testing.
    Patches sl.session_state with a plain dict before each test.
    """
    import utils.transform_log as tl_module
    # import importlib  # will be used in future phases

    # Create a mock for streamlit
    class MockSessionState(dict):
        """Dict that behaves like st.session_state."""
        pass

    class MockStreamlit:
        session_state = MockSessionState()

    # Patch the module's reference to streamlit
    original_sl = tl_module.sl
    tl_module.sl = MockStreamlit()
    yield tl_module.sl.session_state
    tl_module.sl = original_sl


@pytest.fixture
def sample_df():
    """Create a simple sample DataFrame."""
    return pd.DataFrame({
        "a": [1, 2, 3, 4, 5],
        "b": ["x", "y", "z", "x", "y"],
    })


class TestTransformLogInit:
    """Tests for initialization."""

    def test_init_creates_keys(self):
        from utils.transform_log import TransformLog
        TransformLog.init_session()
        # Session state should have the keys

    def test_init_idempotent(self):
        from utils.transform_log import TransformLog
        TransformLog.init_session()
        TransformLog.init_session()  # Should not raise


class TestTransformLogAddStep:
    """Tests for adding steps."""

    def test_add_step(self, sample_df):
        from utils.transform_log import TransformLog
        TransformLog.init_session()
        TransformLog.add_step(
            operation="fill_missing",
            params={"strategy": "mean"},
            columns=["a"],
            df_before=sample_df,
        )
        log = TransformLog.get_log()
        assert len(log) == 1
        assert log[0]["operation"] == "fill_missing"

    def test_step_numbering(self, sample_df):
        from utils.transform_log import TransformLog
        TransformLog.init_session()
        TransformLog.add_step("op1", {}, ["a"], sample_df)
        TransformLog.add_step("op2", {}, ["b"], sample_df)
        log = TransformLog.get_log()
        assert log[0]["step_number"] == 1
        assert log[1]["step_number"] == 2

    def test_step_has_timestamp(self, sample_df):
        from utils.transform_log import TransformLog
        TransformLog.init_session()
        TransformLog.add_step("op1", {}, ["a"], sample_df)
        log = TransformLog.get_log()
        assert "timestamp" in log[0]


class TestTransformLogUndo:
    """Tests for undo functionality."""

    def test_undo_returns_previous_df(self, sample_df):
        from utils.transform_log import TransformLog
        TransformLog.init_session()

        # Record step with original df
        TransformLog.add_step("op1", {}, ["a"], sample_df)

        restored = TransformLog.undo_last()
        assert restored is not None
        pd.testing.assert_frame_equal(restored, sample_df)

    def test_undo_empty_returns_none(self):
        from utils.transform_log import TransformLog
        TransformLog.init_session()
        result = TransformLog.undo_last()
        assert result is None

    def test_undo_removes_step(self, sample_df):
        from utils.transform_log import TransformLog
        TransformLog.init_session()
        TransformLog.add_step("op1", {}, ["a"], sample_df)
        TransformLog.add_step("op2", {}, ["b"], sample_df)
        TransformLog.undo_last()
        assert len(TransformLog.get_log()) == 1


class TestTransformLogReset:
    """Tests for reset functionality."""

    def test_reset_clears_log(self, sample_df):
        from utils.transform_log import TransformLog
        TransformLog.init_session()
        TransformLog.add_step("op1", {}, ["a"], sample_df)
        TransformLog.reset_all(sample_df)
        assert len(TransformLog.get_log()) == 0

    def test_reset_returns_copy(self, sample_df):
        from utils.transform_log import TransformLog
        TransformLog.init_session()
        result = TransformLog.reset_all(sample_df)
        pd.testing.assert_frame_equal(result, sample_df)
        # Ensure it's a copy, not the same object
        assert result is not sample_df


class TestTransformLogSummary:
    """Tests for log summary."""

    def test_empty_summary(self):
        from utils.transform_log import TransformLog
        TransformLog.init_session()
        summary = TransformLog.get_log_summary()
        assert "No transformations" in summary

    def test_summary_with_steps(self, sample_df):
        from utils.transform_log import TransformLog
        TransformLog.init_session()
        TransformLog.add_step("fill_missing", {"strategy": "mean"}, ["price"], sample_df)
        summary = TransformLog.get_log_summary()
        assert "fill_missing" in summary
        assert "price" in summary


class TestTransformLogExport:
    """Tests for export."""

    def test_to_dict(self, sample_df):
        from utils.transform_log import TransformLog
        TransformLog.init_session()
        TransformLog.add_step("op1", {"key": "val"}, ["a"], sample_df)
        exported = TransformLog.to_dict()
        assert isinstance(exported, list)
        assert len(exported) == 1
        assert exported[0]["params"] == {"key": "val"}
