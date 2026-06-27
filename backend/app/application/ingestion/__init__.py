"""Ingestion use cases: parse → normalize → index → detect → persist."""

from app.application.ingestion.ingest_file import IngestFileUseCase, IngestSummary

__all__ = ["IngestFileUseCase", "IngestSummary"]
