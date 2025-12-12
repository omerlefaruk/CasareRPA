#!/usr/bin/env python
"""
Real integration test for Playwright MCP + SmartWorkflowAgent.

This script tests the full flow:
1. Detect URL in prompt
2. Launch Playwright MCP and navigate to URL
3. Extract page context (forms, buttons, selectors)
4. Generate workflow using OpenRouter LLM with real page context

Usage:
    python scripts/test_playwright_mcp_real.py

Requirements:
    - OpenRouter API key configured in credential store
    - Playwright MCP installed (npx @playwright/mcp@latest)
"""

import asyncio
import json
import sys
import os
from pathlib import Path

# Fix Windows encoding
if sys.platform == "win32":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from loguru import logger

# Configure logger for visible output
logger.remove()
logger.add(sys.stderr, level="INFO", format="<level>{level: <8}</level> | {message}")


async def test_playwright_mcp_standalone():
    """Test Playwright MCP client standalone."""
    print("\n" + "=" * 60)
    print("TEST 1: Playwright MCP Client Standalone")
    print("=" * 60)

    from casare_rpa.infrastructure.ai.playwright_mcp import PlaywrightMCPClient

    client = PlaywrightMCPClient()

    # Check if MCP is available
    if not client._npx_path:
        print("[FAIL] Playwright MCP not available (npx not found)")
        return False

    print(f"[OK] npx found at: {client._npx_path}")

    try:
        async with client:
            print("[OK] MCP server started")

            # Navigate to a simple page
            url = "https://example.com"
            print(f"\nNavigating to {url}...")
            result = await client.navigate(url)
            print(f"[OK] Navigation result: {result.success}")

            # Get snapshot
            print("\nGetting page snapshot...")
            snapshot = await client.get_snapshot()
            snapshot_text = snapshot.get_text()
            print(f"[OK] Snapshot received: {len(snapshot_text)} chars")

            if snapshot_text:
                # Pretty print first part of snapshot
                print(f"\nSnapshot preview:\n{snapshot_text[:800]}...")

            return True

    except Exception as e:
        print(f"[FAIL] Error: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_page_analyzer():
    """Test PageAnalyzer with real page."""
    print("\n" + "=" * 60)
    print("TEST 2: Page Analyzer with Real Page")
    print("=" * 60)

    from casare_rpa.infrastructure.ai.playwright_mcp import PlaywrightMCPClient
    from casare_rpa.infrastructure.ai.page_analyzer import PageAnalyzer

    client = PlaywrightMCPClient()
    analyzer = PageAnalyzer()

    try:
        async with client:
            # Test with a page that has forms
            url = "https://www.google.com"
            print(f"\nNavigating to {url}...")
            await client.navigate(url)

            print("Getting snapshot...")
            snapshot = await client.get_snapshot()
            snapshot_text = snapshot.get_text()

            if snapshot_text:
                print("Analyzing page...")
                context = analyzer.analyze_snapshot(
                    snapshot=snapshot_text, url=url, title="Google"
                )

                print("\n[OK] Page Context Extracted:")
                print(f"  - Forms: {len(context.forms)}")
                print(f"  - Buttons: {len(context.buttons)}")
                print(f"  - Links: {len(context.links)}")
                print(f"  - Inputs: {len(context.inputs)}")
                print(f"  - Text Areas: {len(context.text_areas)}")

                # Show prompt context
                prompt_ctx = context.to_prompt_context()
                print(f"\n--- Prompt Context Preview ---\n{prompt_ctx[:1000]}...")

                return True
            else:
                print("[FAIL] No snapshot received")
                return False

    except Exception as e:
        print(f"[FAIL] Error: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_url_detection():
    """Test URL detection in SmartWorkflowAgent."""
    print("\n" + "=" * 60)
    print("TEST 3: URL Detection")
    print("=" * 60)

    from casare_rpa.infrastructure.ai.agent.core import SmartWorkflowAgent

    agent = SmartWorkflowAgent()

    test_prompts = [
        "Go to https://example.com and click the button",
        "Login to https://accounts.google.com with my credentials",
        "Navigate to http://localhost:8080/admin and extract the table",
        "Open https://github.com/anthropics/claude-code and scrape the README",
        "No URL in this prompt",
    ]

    print("\nDetecting URLs in prompts:\n")
    for prompt in test_prompts:
        urls = agent._detect_urls(prompt)
        status = "[OK]" if urls else "[-]"
        print(f'{status} "{prompt[:50]}..."')
        if urls:
            for url in urls:
                print(f"    → {url}")

    return True


async def test_full_workflow_generation():
    """Test full workflow generation with real LLM and page context."""
    print("\n" + "=" * 60)
    print("TEST 4: Full Workflow Generation with OpenRouter")
    print("=" * 60)

    from casare_rpa.infrastructure.ai.agent.core import SmartWorkflowAgent
    from casare_rpa.infrastructure.resources.llm_resource_manager import (
        LLMResourceManager,
        LLMConfig,
        LLMProvider,
    )

    # Get OpenRouter API key - check multiple sources
    api_key = None
    try:
        # 1. Check environment variable
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if api_key:
            print(f"[OK] OpenRouter API key from env: {api_key[:8]}...")

        # 2. Check API key store
        if not api_key:
            from casare_rpa.infrastructure.security.api_key_store import (
                get_api_key_store,
            )

            store = get_api_key_store()
            api_key = store.get_key("openrouter")
            if api_key:
                print(f"[OK] OpenRouter API key from store: {api_key[:8]}...")

        # 3. Check credential store
        if not api_key:
            from casare_rpa.infrastructure.security.credential_store import (
                get_credential_store,
            )

            cred_store = get_credential_store()
            api_key = cred_store.get_api_key_by_provider("openrouter")
            if api_key:
                print(f"[OK] OpenRouter API key from credentials: {api_key[:8]}...")

        if not api_key:
            print("[FAIL] OpenRouter API key not found")
            print("\n   Set it via one of:")
            print("   1. Environment: set OPENROUTER_API_KEY=sk-or-...")
            print(
                "   2. Command line argument: python test_playwright_mcp_real.py sk-or-..."
            )
            return False

    except Exception as e:
        print(f"[FAIL] Could not get API key: {e}")
        import traceback

        traceback.print_exc()
        return False

    # Configure LLM client
    llm_client = LLMResourceManager()
    config = LLMConfig(
        provider=LLMProvider.OPENROUTER,
        model="google/gemini-2.0-flash-001",  # Fast and cheap for testing
        api_key=api_key,
    )
    llm_client.configure(config)
    print(f"[OK] LLM configured: {config.model}")

    # Create agent
    agent = SmartWorkflowAgent(llm_client=llm_client, max_retries=2)

    # Test prompt with URL
    prompt = "Go to https://example.com and extract all the links on the page"
    print(f'\nPrompt: "{prompt}"')
    print("\nGenerating workflow (this may take 10-30 seconds)...")

    try:
        result = await agent.generate_workflow(
            user_prompt=prompt,
            model="google/gemini-2.0-flash-001",
        )

        if result.success:
            print("\n[OK] Workflow generated successfully!")
            print(f"  - Attempts: {result.attempts}")
            print(f"  - Time: {result.generation_time_ms:.0f}ms")

            if result.workflow:
                nodes = result.workflow.get("nodes", {})
                connections = result.workflow.get("connections", [])
                print(f"  - Nodes: {len(nodes)}")
                print(f"  - Connections: {len(connections)}")

                print("\n--- Generated Nodes ---")
                for node_id, node_data in list(nodes.items())[:10]:
                    node_type = node_data.get("node_type", "?")
                    print(f"  • {node_type} ({node_id})")

                # Show full workflow JSON
                print("\n--- Full Workflow JSON ---")
                print(json.dumps(result.workflow, indent=2)[:2000])
                if len(json.dumps(result.workflow)) > 2000:
                    print("... (truncated)")

            return True
        else:
            print(f"\n[FAIL] Workflow generation failed: {result.error}")
            if result.raw_response:
                print(f"\nRaw LLM response:\n{result.raw_response[:500]}...")
            return False

    except Exception as e:
        print(f"[FAIL] Error: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_fetch_page_context_convenience():
    """Test the convenience function for fetching page context."""
    print("\n" + "=" * 60)
    print("TEST 5: fetch_page_context() Convenience Function")
    print("=" * 60)

    from casare_rpa.infrastructure.ai.playwright_mcp import fetch_page_context

    url = "https://httpbin.org/forms/post"
    print(f"\nFetching page context for: {url}")
    print("(This page has a sample form)")

    try:
        result = await fetch_page_context(url)

        if result:
            print("\n[OK] Page context fetched!")
            print(f"  - URL: {result.get('url', 'N/A')}")
            print(f"  - Title: {result.get('title', 'N/A')}")

            # Parse with PageAnalyzer if we have snapshot
            if result.get("snapshot"):
                from casare_rpa.infrastructure.ai.page_analyzer import PageAnalyzer

                analyzer = PageAnalyzer()
                context = analyzer.analyze_snapshot(
                    snapshot=result["snapshot"],
                    url=result.get("url", url),
                    title=result.get("title", ""),
                )
                print(f"  - Forms: {len(context.forms)}")
                print(f"  - Buttons: {len(context.buttons)}")
                print(f"  - Inputs: {len(context.inputs)}")

                if context.forms:
                    print("\n--- Forms Found ---")
                    for i, form in enumerate(context.forms):
                        print(f"  Form {i + 1}: {len(form.fields)} fields")
                        for field in form.fields[:5]:
                            print(
                                f"    - {field.name} ({field.field_type}) - {field.selector}"
                            )

            return True
        else:
            print("[FAIL] No context returned (MCP may not be available)")
            return False

    except Exception as e:
        print(f"[FAIL] Error: {e}")
        import traceback

        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("  PLAYWRIGHT MCP INTEGRATION - REAL DATA TESTS")
    print("=" * 60)

    results = {}

    # Test 1: MCP Client
    results["MCP Client"] = await test_playwright_mcp_standalone()

    # Test 2: Page Analyzer
    results["Page Analyzer"] = await test_page_analyzer()

    # Test 3: URL Detection
    results["URL Detection"] = await test_url_detection()

    # Test 4: Convenience function
    results["fetch_page_context"] = await test_fetch_page_context_convenience()

    # Test 5: Full workflow (only if previous tests passed)
    if all([results.get("MCP Client"), results.get("Page Analyzer")]):
        results["Full Workflow"] = await test_full_workflow_generation()
    else:
        print("\n[WARN] Skipping full workflow test (prerequisites failed)")
        results["Full Workflow"] = None

    # Summary
    print("\n" + "=" * 60)
    print("  TEST SUMMARY")
    print("=" * 60)

    for test_name, passed in results.items():
        if passed is None:
            status = "[WARN] SKIPPED"
        elif passed:
            status = "[OK] PASSED"
        else:
            status = "[FAIL] FAILED"
        print(f"  {status}: {test_name}")

    passed_count = sum(1 for v in results.values() if v is True)
    total_count = sum(1 for v in results.values() if v is not None)
    print(f"\n  Total: {passed_count}/{total_count} passed")

    return all(v is not False for v in results.values())


if __name__ == "__main__":
    # Support API key as command line argument
    if len(sys.argv) > 1 and sys.argv[1].startswith("sk-"):
        os.environ["OPENROUTER_API_KEY"] = sys.argv[1]
        print(f"Using API key from command line: {sys.argv[1][:8]}...")

    success = asyncio.run(main())
    sys.exit(0 if success else 1)
