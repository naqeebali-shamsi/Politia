"""Tests for data ingestion adapters."""
import pytest
import tempfile
import os

from app.infrastructure.ingestion.base_adapter import BaseSourceAdapter, IngestionResult
from app.infrastructure.ingestion.adapters.csv_import_adapter import (
    CsvImportAdapter, DatameetElectionAdapter, AffidavitCsvAdapter,
)


class TestIngestionResult:
    def test_success_rate_all_success(self):
        r = IngestionResult(source_name="test", records_processed=10, records_failed=0)
        assert r.success_rate == 100.0

    def test_success_rate_all_failed(self):
        r = IngestionResult(source_name="test", records_processed=10, records_failed=10)
        assert r.success_rate == 0.0

    def test_success_rate_zero_processed(self):
        r = IngestionResult(source_name="test", records_processed=0, records_failed=0)
        assert r.success_rate == 0.0

    def test_success_rate_partial(self):
        r = IngestionResult(source_name="test", records_processed=10, records_failed=3)
        assert r.success_rate == 70.0


class TestCsvImportAdapter:
    def test_reads_csv_file(self, tmp_path):
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("name,party,state\nModi,BJP,Gujarat\nGandhi,INC,UP\n", encoding="utf-8")

        adapter = CsvImportAdapter(str(csv_file), source="test")
        records = adapter.fetch()
        assert len(records) == 2
        assert records[0]["name"] == "Modi"

    def test_handles_bom(self, tmp_path):
        """UTF-8 BOM should be handled correctly."""
        csv_file = tmp_path / "bom.csv"
        csv_file.write_bytes(b"\xef\xbb\xbfname,party\nModi,BJP\n")

        adapter = CsvImportAdapter(str(csv_file), source="test")
        records = adapter.fetch()
        assert len(records) == 1
        assert "name" in records[0]  # BOM should not corrupt the first header

    def test_missing_file_raises(self, tmp_path):
        adapter = CsvImportAdapter(str(tmp_path / "nonexistent.csv"), source="test")
        with pytest.raises(FileNotFoundError):
            adapter.fetch()

    def test_empty_csv(self, tmp_path):
        csv_file = tmp_path / "empty.csv"
        csv_file.write_text("name,party\n", encoding="utf-8")

        adapter = CsvImportAdapter(str(csv_file), source="test")
        records = adapter.fetch()
        assert len(records) == 0

    def test_source_name(self):
        adapter = CsvImportAdapter("test.csv", source="my_source")
        assert adapter.source_name == "my_source"

    def test_parse_passthrough(self, tmp_path):
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("a,b\n1,2\n", encoding="utf-8")

        adapter = CsvImportAdapter(str(csv_file))
        raw = adapter.fetch()
        parsed = adapter.parse(raw)
        assert parsed == raw  # Default parse is passthrough


class TestDatameetElectionAdapter:
    def test_parses_election_data(self, tmp_path):
        csv_file = tmp_path / "parliament.csv"
        csv_file.write_text(
            "CANDIDATE,PARTY,PC_NAME,STATE,YEAR,VOTES,POSITION\n"
            "NARENDRA MODI,BJP,VARANASI,UTTAR PRADESH,2019,674664,1\n"
            "AJAY RAI,INC,VARANASI,UTTAR PRADESH,2019,195159,2\n",
            encoding="utf-8",
        )

        adapter = DatameetElectionAdapter(str(csv_file))
        raw = adapter.fetch()
        parsed = adapter.parse(raw)

        assert len(parsed) == 2
        assert parsed[0]["candidate_name"] == "NARENDRA MODI"
        assert parsed[0]["party"] == "BJP"
        assert parsed[0]["constituency"] == "VARANASI"
        assert parsed[0]["year"] == 2019
        assert parsed[0]["votes"] == 674664
        assert parsed[0]["result"] == "Won"
        assert parsed[1]["result"] == "Lost"

    def test_handles_missing_fields(self, tmp_path):
        csv_file = tmp_path / "bad.csv"
        csv_file.write_text(
            "CANDIDATE,PARTY,PC_NAME,STATE,YEAR,VOTES,POSITION\n"
            "TEST,,,,bad_year,,\n",
            encoding="utf-8",
        )

        adapter = DatameetElectionAdapter(str(csv_file))
        raw = adapter.fetch()
        parsed = adapter.parse(raw)
        # Should skip malformed rows
        assert len(parsed) == 0


class TestAffidavitCsvAdapter:
    def test_parses_affidavit_data(self, tmp_path):
        csv_file = tmp_path / "affidavits.csv"
        csv_file.write_text(
            "candidate_name,constituency,state,party,year,criminal_cases,total_assets,liabilities,education\n"
            "Narendra Modi,Varanasi,Uttar Pradesh,BJP,2024,0,\"3,07,00,000\",\"50,00,000\",Post Graduate\n",
            encoding="utf-8",
        )

        adapter = AffidavitCsvAdapter(str(csv_file))
        raw = adapter.fetch()
        parsed = adapter.parse(raw)

        assert len(parsed) == 1
        assert parsed[0]["candidate_name"] == "Narendra Modi"
        assert parsed[0]["criminal_cases"] == 0
        assert parsed[0]["total_assets"] == 30700000.0
        assert parsed[0]["total_liabilities"] == 5000000.0
        assert parsed[0]["education"] == "Post Graduate"

    def test_handles_na_values(self, tmp_path):
        csv_file = tmp_path / "na.csv"
        csv_file.write_text(
            "candidate_name,constituency,state,party,year,criminal_cases,total_assets,liabilities,education\n"
            "Test Person,TestPlace,TestState,IND,2024,0,N/A,N/A,\n",
            encoding="utf-8",
        )

        adapter = AffidavitCsvAdapter(str(csv_file))
        raw = adapter.fetch()
        parsed = adapter.parse(raw)

        assert len(parsed) == 1
        assert parsed[0]["total_assets"] is None
        assert parsed[0]["total_liabilities"] is None

    def test_parse_float_edge_cases(self):
        assert AffidavitCsvAdapter._parse_float(None) is None
        assert AffidavitCsvAdapter._parse_float("") is None
        assert AffidavitCsvAdapter._parse_float("N/A") is None
        assert AffidavitCsvAdapter._parse_float("Rs 1,00,000") == 100000.0
        assert AffidavitCsvAdapter._parse_float("~50000") == 50000.0
        assert AffidavitCsvAdapter._parse_float(12345) == 12345.0
        assert AffidavitCsvAdapter._parse_float("not_a_number") is None
