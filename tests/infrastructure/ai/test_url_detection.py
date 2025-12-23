"""
Unit tests for URL detection in SmartWorkflowAgent.

Tests the _detect_urls method which extracts URLs from user prompts
to enable automatic page context fetching for browser workflows.

Test Coverage:
- Single URL detection
- Multiple URL detection
- URL with paths and query strings
- No URLs in prompt
- HTTP and HTTPS protocols
- URLs in quotes
- URLs with trailing punctuation
- Edge cases (malformed, duplicates)
"""

import pytest


class TestURLDetection:
    """Tests for SmartWorkflowAgent._detect_urls method."""

    @pytest.fixture
    def agent(self):
        """Create SmartWorkflowAgent instance for testing."""
        # Import here to avoid import errors if dependencies missing
        from casare_rpa.infrastructure.ai.agent.core import SmartWorkflowAgent

        # Create agent without LLM client (we only test URL detection)
        return SmartWorkflowAgent(llm_client=None)

    def test_detect_single_url(self, agent):
        """Should detect single URL in prompt."""
        prompt = "Go to https://example.com and fill the form"
        urls = agent._detect_urls(prompt)

        assert len(urls) == 1
        assert urls[0] == "https://example.com"

    def test_detect_multiple_urls(self, agent):
        """Should detect multiple URLs in prompt."""
        prompt = "Navigate to https://example.com, then go to https://other.com/page"
        urls = agent._detect_urls(prompt)

        assert len(urls) == 2
        assert "https://example.com" in urls
        assert "https://other.com/page" in urls

    def test_detect_url_with_path(self, agent):
        """Should detect URLs with paths."""
        prompt = "Open https://example.com/login/user/dashboard"
        urls = agent._detect_urls(prompt)

        assert len(urls) == 1
        assert urls[0] == "https://example.com/login/user/dashboard"

    def test_detect_url_with_query_string(self, agent):
        """Should detect URLs with query parameters."""
        prompt = "Visit https://example.com/search?q=test&page=1"
        urls = agent._detect_urls(prompt)

        assert len(urls) == 1
        assert "search?q=test" in urls[0]

    def test_no_urls_returns_empty_list(self, agent):
        """Should return empty list when no URLs present."""
        prompt = "Create a workflow that clicks a button"
        urls = agent._detect_urls(prompt)

        assert urls == []

    def test_detect_http_protocol(self, agent):
        """Should detect HTTP URLs (not just HTTPS)."""
        prompt = "Go to http://localhost:8080/test"
        urls = agent._detect_urls(prompt)

        assert len(urls) == 1
        assert urls[0] == "http://localhost:8080/test"

    def test_detect_http_and_https(self, agent):
        """Should detect both HTTP and HTTPS URLs."""
        prompt = "Navigate to http://localhost:3000 and https://api.example.com"
        urls = agent._detect_urls(prompt)

        assert len(urls) == 2

    def test_url_in_single_quotes(self, agent):
        """Should detect URL inside single quotes."""
        prompt = "Navigate to 'https://example.com/login' and fill the form"
        urls = agent._detect_urls(prompt)

        assert len(urls) == 1
        # URL should be extracted without the quotes
        assert "https://example.com/login" in urls[0]

    def test_url_in_double_quotes(self, agent):
        """Should detect URL inside double quotes."""
        prompt = 'Open "https://example.com/dashboard"'
        urls = agent._detect_urls(prompt)

        assert len(urls) == 1
        assert "https://example.com/dashboard" in urls[0]

    def test_url_with_trailing_period(self, agent):
        """Should strip trailing period from URL."""
        prompt = "Go to https://example.com."
        urls = agent._detect_urls(prompt)

        assert len(urls) == 1
        assert urls[0] == "https://example.com"
        assert not urls[0].endswith(".")

    def test_url_with_trailing_comma(self, agent):
        """Should strip trailing comma from URL."""
        prompt = "Visit https://example.com, then click login"
        urls = agent._detect_urls(prompt)

        assert len(urls) == 1
        assert urls[0] == "https://example.com"
        assert not urls[0].endswith(",")

    def test_url_with_trailing_exclamation(self, agent):
        """Should strip trailing exclamation mark from URL."""
        prompt = "Check out https://example.com!"
        urls = agent._detect_urls(prompt)

        assert len(urls) == 1
        assert not urls[0].endswith("!")

    def test_url_with_trailing_question_mark(self, agent):
        """Should strip trailing question mark (not part of query)."""
        prompt = "Have you seen https://example.com?"
        urls = agent._detect_urls(prompt)

        assert len(urls) == 1
        assert urls[0] == "https://example.com"

    def test_max_urls_limit(self, agent):
        """Should respect MAX_URLS_TO_ANALYZE limit."""
        prompt = """
        https://url1.com
        https://url2.com
        https://url3.com
        https://url4.com
        https://url5.com
        """
        urls = agent._detect_urls(prompt)

        # Should be limited to MAX_URLS_TO_ANALYZE (default 3)
        assert len(urls) <= agent.MAX_URLS_TO_ANALYZE

    def test_duplicate_urls_removed(self, agent):
        """Should remove duplicate URLs."""
        prompt = "Go to https://example.com, fill form on https://example.com"
        urls = agent._detect_urls(prompt)

        assert len(urls) == 1
        assert urls[0] == "https://example.com"

    def test_url_with_port(self, agent):
        """Should detect URL with port number."""
        prompt = "Connect to https://example.com:8443/api"
        urls = agent._detect_urls(prompt)

        assert len(urls) == 1
        assert ":8443" in urls[0]

    def test_url_with_fragment(self, agent):
        """Should detect URL with fragment identifier."""
        prompt = "Jump to https://example.com/docs#section-1"
        urls = agent._detect_urls(prompt)

        assert len(urls) == 1
        assert "#section-1" in urls[0]

    def test_url_pattern_is_case_insensitive(self, agent):
        """Should detect URLs regardless of case."""
        prompt = "Visit HTTPS://EXAMPLE.COM/PAGE"
        urls = agent._detect_urls(prompt)

        assert len(urls) == 1

    def test_url_in_markdown_link(self, agent):
        """Should detect URL in markdown link format."""
        prompt = "Click [here](https://example.com/link) to continue"
        urls = agent._detect_urls(prompt)

        assert len(urls) == 1
        # URL extracted even from markdown
        assert "https://example.com/link" in urls[0]

    def test_empty_prompt(self, agent):
        """Should handle empty prompt gracefully."""
        urls = agent._detect_urls("")

        assert urls == []

    def test_whitespace_only_prompt(self, agent):
        """Should handle whitespace-only prompt."""
        urls = agent._detect_urls("   \n\t  ")

        assert urls == []

    def test_url_at_end_of_sentence(self, agent):
        """Should handle URL at end of sentence with punctuation."""
        prompt = "The login page is at https://example.com/login."
        urls = agent._detect_urls(prompt)

        assert len(urls) == 1
        assert urls[0] == "https://example.com/login"

    def test_complex_url_with_special_chars(self, agent):
        """Should handle complex URLs with encoded characters."""
        prompt = "Search at https://example.com/search?q=hello%20world&sort=asc"
        urls = agent._detect_urls(prompt)

        assert len(urls) == 1
        assert "%20" in urls[0] or "hello" in urls[0]


class TestURLPatternRegex:
    """Tests for the URL_PATTERN regex itself."""

    @pytest.fixture
    def agent(self):
        """Create SmartWorkflowAgent for pattern testing."""
        from casare_rpa.infrastructure.ai.agent.core import SmartWorkflowAgent

        return SmartWorkflowAgent(llm_client=None)

    def test_pattern_matches_basic_https(self, agent):
        """Pattern should match basic HTTPS URL."""
        match = agent.URL_PATTERN.search("https://example.com")
        assert match is not None
        assert "example.com" in match.group()

    def test_pattern_matches_basic_http(self, agent):
        """Pattern should match basic HTTP URL."""
        match = agent.URL_PATTERN.search("http://example.com")
        assert match is not None

    def test_pattern_does_not_match_ftp(self, agent):
        """Pattern should NOT match FTP URLs."""
        match = agent.URL_PATTERN.search("ftp://example.com")
        assert match is None

    def test_pattern_does_not_match_invalid(self, agent):
        """Pattern should NOT match invalid URLs."""
        match = agent.URL_PATTERN.search("not-a-url")
        assert match is None

        match = agent.URL_PATTERN.search("httpx://example.com")
        assert match is None


class TestURLDetectionIntegration:
    """Integration tests for URL detection with page context fetching."""

    @pytest.fixture
    def agent(self):
        """Create SmartWorkflowAgent for testing."""
        from casare_rpa.infrastructure.ai.agent.core import SmartWorkflowAgent

        return SmartWorkflowAgent(llm_client=None)

    @pytest.mark.asyncio
    async def test_mcp_available_check(self, agent):
        """Should check MCP availability without crashing."""
        # This should not raise even if MCP is not installed
        result = await agent._check_mcp_available()
        assert isinstance(result, bool)

    @pytest.mark.asyncio
    async def test_fetch_page_context_returns_none_when_mcp_unavailable(self, agent):
        """Should return None when MCP is not available."""
        # Force MCP to be unavailable
        agent._mcp_available = False

        result = await agent._fetch_page_context("https://example.com")
        assert result is None

    def test_format_page_contexts_empty_list(self, agent):
        """Should return empty string for empty context list."""
        result = agent._format_page_contexts([])
        assert result == ""

    def test_format_page_contexts_with_contexts(self, agent):
        """Should format page contexts correctly."""
        from casare_rpa.infrastructure.ai.page_analyzer import PageContext

        context = PageContext(
            url="https://example.com",
            title="Example",
            buttons=[{"text": "Click", "selector": "button", "ref": "btn1"}],
        )

        result = agent._format_page_contexts([context])

        assert "example.com" in result.lower() or "Example" in result
