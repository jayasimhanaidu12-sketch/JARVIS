"""
News service module for JARVIS.
Fetches real-time, present-day news updates and formats them for natural voice presentation.
"""

import html
import re
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional
import requests

from logging_system.logger import jarvis_logger


class NewsService:
    """
    Live real-time news aggregation and voice synthesis formatting engine.
    Supports top headlines, categorized searches, deduplication, and natural speech delivery.
    """

    GOOGLE_NEWS_TOP_URL = "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en"
    GOOGLE_NEWS_SEARCH_URL = "https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
    BBC_NEWS_URL = "http://feeds.bbci.co.uk/news/rss.xml"

    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
    }

    ORDINALS = [
        "First",
        "Second",
        "Third",
        "Fourth",
        "Fifth",
        "Sixth",
        "And seventh",
        "Eighth",
        "Ninth",
        "Tenth",
    ]

    def _clean_headline(self, text: str) -> Tuple[str, str]:
        """
        Cleans HTML entities, removes redundant tags, normalizes quotes/dashes,
        and splits headline from source publisher.
        """
        if not text:
            return "", ""

        clean = html.unescape(text).strip()

        # Normalize unicode smart quotes and dashes to plain punctuation for TTS
        clean = (
            clean.replace("\u2018", "'")
            .replace("\u2019", "'")
            .replace("\u201c", '"')
            .replace("\u201d", '"')
            .replace("\u2013", "-")
            .replace("\u2014", "--")
            .replace("\u2026", "...")
            .replace("\xa0", " ")
        )

        # Extract publisher if separated by ' - '
        source = ""
        if " - " in clean:
            headline, source = clean.rsplit(" - ", 1)
            source = source.strip()
        else:
            headline = clean

        # Strip noisy prefix tags like BREAKING:, EXCLUSIVE:, WATCH:, LIVE:
        headline = re.sub(
            r"^(?:EXCLUSIVE|BREAKING|WATCH|UPDATE|LIVE|JUST IN|ALERT|SPECIAL REPORT):\s*",
            "",
            headline,
            flags=re.IGNORECASE,
        ).strip()

        # Remove extra whitespace
        headline = re.sub(r"\s+", " ", headline)

        # Remove any lingering HTML tags
        headline = re.sub(r"<[^>]+>", "", headline).strip()

        # Remove terminal punctuation if any so we control sentence endings
        headline = headline.rstrip(" .!?;:")

        return headline, source

    def _fetch_from_google_rss(self, topic: Optional[str] = None) -> List[Dict[str, str]]:
        """Fetches news items from Google News RSS feed."""
        if topic:
            encoded_topic = urllib.parse.quote_plus(topic)
            url = self.GOOGLE_NEWS_SEARCH_URL.format(query=encoded_topic)
        else:
            url = self.GOOGLE_NEWS_TOP_URL

        resp = requests.get(url, headers=self.HEADERS, timeout=8)
        resp.raise_for_status()

        # Use resp.content with XML parser to handle encoding automatically
        root = ET.fromstring(resp.content)
        items = root.findall(".//item")

        results = []
        for item in items:
            title_node = item.find("title")
            link_node = item.find("link")
            pub_date_node = item.find("pubDate")

            raw_title = title_node.text if title_node is not None else ""
            link = link_node.text if link_node is not None else ""
            pub_date = pub_date_node.text if pub_date_node is not None else ""

            headline, source = self._clean_headline(raw_title)
            if headline:
                results.append({
                    "headline": headline,
                    "source": source,
                    "link": link,
                    "pub_date": pub_date,
                })
        return results

    def _fetch_from_bbc_rss(self) -> List[Dict[str, str]]:
        """Fallback to BBC News Top Stories RSS feed."""
        resp = requests.get(self.BBC_NEWS_URL, headers=self.HEADERS, timeout=8)
        resp.raise_for_status()

        root = ET.fromstring(resp.content)
        items = root.findall(".//item")

        results = []
        for item in items:
            title_node = item.find("title")
            link_node = item.find("link")
            pub_date_node = item.find("pubDate")

            raw_title = title_node.text if title_node is not None else ""
            link = link_node.text if link_node is not None else ""
            pub_date = pub_date_node.text if pub_date_node is not None else ""

            headline, _ = self._clean_headline(raw_title)
            if headline:
                results.append({
                    "headline": headline,
                    "source": "BBC News",
                    "link": link,
                    "pub_date": pub_date,
                })
        return results

    def fetch_news(self, count: int = 7, topic: Optional[str] = None) -> List[Dict[str, str]]:
        """
        Retrieves real-time, present-day news updates with automatic deduplication.
        Tries Google News RSS first, then falls back to BBC News RSS.
        """
        raw_items: List[Dict[str, str]] = []

        try:
            raw_items = self._fetch_from_google_rss(topic=topic)
        except Exception as e:
            jarvis_logger.warning(f"Google News RSS fetch error: {e}. Trying fallback...")
            try:
                raw_items = self._fetch_from_bbc_rss()
            except Exception as e2:
                jarvis_logger.error(f"Fallback News RSS also failed: {e2}")

        if not raw_items:
            return []

        # Deduplicate items using a normalized token set to prevent overlapping stories
        deduped: List[Dict[str, str]] = []
        seen_tokens = set()

        for item in raw_items:
            headline = item["headline"]
            # Extract key lowercase words (length > 3)
            tokens = set(re.findall(r"\b[a-z]{4,}\b", headline.lower()))

            # Check overlap with already selected headlines
            overlap = False
            for prev_tokens in seen_tokens:
                if len(tokens.intersection(prev_tokens)) >= 4:
                    overlap = True
                    break

            if not overlap:
                seen_tokens.add(frozenset(tokens))
                deduped.append(item)
                if len(deduped) >= count:
                    break

        return deduped

    def format_news_for_voice(
        self,
        news_items: List[Dict[str, str]],
        count: int = 7,
        topic: Optional[str] = None,
    ) -> str:
        """
        Formats retrieved news items into an elegant, clear natural speech transcript
        specifically engineered for Text-to-Speech output.
        """
        if not news_items:
            return (
                "I'm currently unable to retrieve the latest news feed, sir. "
                "Please ensure the internet connection is active."
            )

        actual_count = len(news_items)
        topic_phrase = f" on {topic}" if topic else ""

        lines = [f"Here are today's top {actual_count} news updates{topic_phrase}, sir:"]

        for i, item in enumerate(news_items):
            ordinal = self.ORDINALS[i] if i < len(self.ORDINALS) else f"Number {i + 1}"
            headline = item["headline"]
            source = item.get("source")

            if source:
                # Add source smoothly for conversational cadence
                line = f"{ordinal}: {headline}, reported by {source}."
            else:
                line = f"{ordinal}: {headline}."

            lines.append(line)

        lines.append("Those are the primary headlines for today, sir.")
        return "\n".join(lines)

    def get_voice_news_update(
        self,
        count: int = 7,
        topic: Optional[str] = None,
    ) -> Tuple[bool, str]:
        """
        Main entry point for tool execution:
        Fetches the present day news and produces the complete voice speech payload.
        """
        items = self.fetch_news(count=count, topic=topic)
        if not items:
            return (
                False,
                "I was unable to retrieve today's news updates from the live feeds, sir.",
            )

        speech_text = self.format_news_for_voice(items, count=count, topic=topic)
        return True, speech_text


news_service = NewsService()
