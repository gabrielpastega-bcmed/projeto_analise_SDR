"""
Tests for Filter Component and Excel Export.
"""

from datetime import date, datetime
from unittest.mock import MagicMock

import pandas as pd


class TestFilterComponent:
    """Tests for FilterComponent."""

    def test_init_creates_session_state_keys(self):
        """Test that initialization creates session state keys."""
        # Mock session state
        import src.filters
        from src.filters import FilterComponent

        src.filters.st = MagicMock()
        src.filters.st.session_state = {}

        FilterComponent(key_prefix="test")

        assert "test_date_start" in src.filters.st.session_state
        assert "test_date_end" in src.filters.st.session_state
        assert "test_agents" in src.filters.st.session_state

    def test_get_current_filters_returns_dict(self):
        """Test get_current_filters returns expected structure."""
        import src.filters
        from src.filters import FilterComponent

        src.filters.st = MagicMock()
        src.filters.st.session_state = {
            "test_date_start": date(2024, 1, 1),
            "test_date_end": date(2024, 1, 31),
            "test_agents": ["Agent1"],
            "test_origins": [],
            "test_qualifications": [],
        }

        filter_comp = FilterComponent(key_prefix="test")
        filters = filter_comp.get_current_filters()

        assert filters["date_start"] == date(2024, 1, 1)
        assert filters["agents"] == ["Agent1"]

    def test_has_active_filters_true(self):
        """Test has_active_filters returns True when filters exist."""
        import src.filters
        from src.filters import FilterComponent

        src.filters.st = MagicMock()
        src.filters.st.session_state = {
            "test_date_start": date(2024, 1, 1),
            "test_date_end": None,
            "test_agents": [],
            "test_origins": [],
            "test_qualifications": [],
        }

        filter_comp = FilterComponent(key_prefix="test")

        assert filter_comp.has_active_filters() is True

    def test_has_active_filters_false(self):
        """Test has_active_filters returns False when no filters."""
        import src.filters
        from src.filters import FilterComponent

        src.filters.st = MagicMock()
        src.filters.st.session_state = {
            "test_date_start": None,
            "test_date_end": None,
            "test_agents": [],
            "test_origins": [],
            "test_qualifications": [],
        }

        filter_comp = FilterComponent(key_prefix="test")

        assert filter_comp.has_active_filters() is False


class TestExcelExporter:
    """Tests for ExcelExporter."""

    def test_exporter_creates_workbook(self):
        """Test that ExcelExporter creates a workbook."""
        from src.excel_export import ExcelExporter

        exporter = ExcelExporter()

        assert exporter.workbook is not None
        assert len(exporter.workbook.sheetnames) == 0  # Default sheet removed

    def test_add_dataframe_sheet(self):
        """Test adding a dataframe as a sheet."""
        from src.excel_export import ExcelExporter

        df = pd.DataFrame({"A": [1, 2, 3], "B": ["x", "y", "z"]})

        exporter = ExcelExporter()
        ws = exporter.add_dataframe_sheet(df, "TestSheet")

        assert "TestSheet" in exporter.workbook.sheetnames
        assert ws.max_row == 4  # Header + 3 rows

    def test_add_summary_sheet(self):
        """Test adding a summary sheet."""
        from src.excel_export import ExcelExporter

        exporter = ExcelExporter()
        summary = {"Total": 100, "Average": 50.5}

        ws = exporter.add_summary_sheet(summary, "Summary")

        assert "Summary" in exporter.workbook.sheetnames
        assert ws["A1"].value == "Métrica"
        assert ws["A2"].value == "Total"
        assert ws["B2"].value == 100

    def test_save_to_bytes_returns_buffer(self):
        """Test saving to BytesIO buffer."""
        from src.excel_export import ExcelExporter

        df = pd.DataFrame({"A": [1, 2]})

        exporter = ExcelExporter()
        exporter.add_dataframe_sheet(df, "Data")

        buffer = exporter.save_to_bytes()

        assert buffer.tell() == 0  # Buffer rewound
        assert len(buffer.getvalue()) > 0  # Has content


class TestCreateChatExport:
    """Tests for create_chat_export function."""

    def test_creates_multi_sheet_export(self):
        """Test that export creates multiple sheets."""
        from src.excel_export import create_chat_export

        # Mock chat objects
        mock_chats = [
            MagicMock(
                id=1,
                timestamp=datetime(2024, 1, 1),
                agentName="Agent1",
                waitingTime=300,
                messagesCount=5,
                messages=[],
            )
        ]

        # Mock functions
        import src.excel_export

        src.excel_export.get_lead_origin = lambda c: "Website"
        src.excel_export.classify_lead_qualification = lambda tags: "qualificado"
        src.excel_export.get_chat_tags = lambda c: ["tag1"]

        buffer = create_chat_export(mock_chats)

        # Should have content
        assert len(buffer.getvalue()) > 0
