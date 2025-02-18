"""Kayako Knowledge Base integration package."""

from .interfaces import Article, Ticket, KayakoAPI
from .mock_kayako import MockKayakoAPI

__all__ = ['Article', 'Ticket', 'KayakoAPI', 'MockKayakoAPI'] 