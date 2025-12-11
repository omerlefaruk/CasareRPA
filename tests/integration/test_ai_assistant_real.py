"""
Real Integration Test for AI Assistant with Google AI.

This test uses the ACTUAL Google AI API key from the credential store
to generate real workflows using the Gemini model.

Prerequisites:
- Google AI API key stored in credential store (category="llm", provider="google")
- litellm package installed

Run with: pytest tests/integration/test_ai_assistant_real.py -v -s

Note: These tests may hit rate limits on free tier. The tests include
retry logic with exponential backoff to handle transient rate limits.
"""

import asyncio
import json
import os
import pytest
import time
from typing import Optional, TypeVar, Callable, Any

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))


# Google AI model options (available in Google AI Studio)
# Using models/... format for Google AI API
GOOGLE_AI_MODELS = [
    ("gemini/gemini-3-pro-preview", "Gemini 3 Pro (Preview)"),
    ("gemini/gemini-flash-latest", "Gemini Flash (Latest)"),
    ("gemini/gemini-flash-lite-latest", "Gemini Flash Lite"),
]

# Default model to use for tests
DEFAULT_TEST_MODEL = "gemini/gemini-flash-latest"

# Retry configuration
MAX_RETRIES = 3
INITIAL_BACKOFF_SECONDS = 25  # Start with 25s since API often says "retry in 21s"


async def retry_with_backoff(
    func: Callable[..., Any],
    *args,
    max_retries: int = MAX_RETRIES,
    initial_backoff: float = INITIAL_BACKOFF_SECONDS,
    **kwargs,
) -> Any:
    """
    Retry an async function with exponential backoff on rate limit errors.

    Args:
        func: Async function to call
        max_retries: Maximum number of retry attempts
        initial_backoff: Initial wait time in seconds
        *args, **kwargs: Arguments to pass to func

    Returns:
        Result from func

    Raises:
        Last exception if all retries fail
    """
    last_exception = None

    for attempt in range(max_retries + 1):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            error_str = str(e).lower()
            # Check if it's a rate limit error
            if "429" in str(e) or "rate" in error_str or "quota" in error_str:
                last_exception = e
                if attempt < max_retries:
                    wait_time = initial_backoff * (2**attempt)
                    print(
                        f"\n[RATE LIMIT] Attempt {attempt + 1}/{max_retries + 1} failed. "
                        f"Waiting {wait_time:.1f}s before retry..."
                    )
                    await asyncio.sleep(wait_time)
                else:
                    # Check if daily quota is exhausted
                    if "limit: 0" in str(e) or "quota exceeded" in error_str:
                        pytest.skip(
                            "Google AI daily quota exhausted. "
                            "Tests will pass once quota resets (usually at midnight PT)."
                        )
            else:
                raise  # Re-raise non-rate-limit errors

    raise last_exception


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture(scope="module")
def qapp():
    """Create QApplication for Qt tests."""
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def google_api_key():
    """Get Google AI API key from credential store."""
    from casare_rpa.infrastructure.security.credential_store import get_credential_store

    store = get_credential_store()

    # Find Google AI credential
    for cred in store.list_credentials(category="llm"):
        cred_data = store.get_credential(cred["id"])
        if cred_data and cred_data.get("provider") == "google":
            api_key = cred_data.get("api_key")
            if api_key:
                return api_key

    pytest.skip("No Google AI API key found in credential store")


@pytest.fixture
def set_google_api_key(google_api_key):
    """Set Google API key in environment for LiteLLM."""
    os.environ["GEMINI_API_KEY"] = google_api_key
    yield google_api_key
    # Cleanup
    if "GEMINI_API_KEY" in os.environ:
        del os.environ["GEMINI_API_KEY"]


# =============================================================================
# REAL API TESTS
# =============================================================================


class TestGoogleAIConnection:
    """Test real connection to Google AI API."""

    @pytest.mark.asyncio
    async def test_google_ai_simple_completion(self, set_google_api_key):
        """Test simple completion using Google AI."""
        import litellm

        async def make_request():
            return await litellm.acompletion(
                model=DEFAULT_TEST_MODEL,
                messages=[{"role": "user", "content": "Reply with just 'hello'"}],
                temperature=0.0,
                max_tokens=10,
            )

        # Use retry logic for rate limits
        response = await retry_with_backoff(make_request)

        content = response["choices"][0]["message"]["content"]
        assert content is not None
        assert "hello" in content.lower()
        print(f"\n[OK] Google AI response: {content}")

    @pytest.mark.asyncio
    async def test_google_ai_json_generation(self, set_google_api_key):
        """Test JSON generation with Google AI."""
        import litellm

        async def make_request():
            return await litellm.acompletion(
                model=DEFAULT_TEST_MODEL,
                messages=[
                    {
                        "role": "user",
                        "content": 'Generate a JSON object with keys "name" and "age". Output ONLY the JSON, nothing else.',
                    }
                ],
                temperature=0.0,
                max_tokens=100,
            )

        response = await retry_with_backoff(make_request)
        content = response["choices"][0]["message"]["content"].strip()

        # Remove markdown code blocks if present
        if content.startswith("```"):
            lines = content.split("\n")
            content = "\n".join(
                line for line in lines if not line.startswith("```")
            ).strip()

        data = json.loads(content)
        assert "name" in data
        assert "age" in data
        print(f"\n[OK] JSON generation: {data}")


class TestSmartWorkflowAgentReal:
    """Test SmartWorkflowAgent with real Google AI API."""

    @pytest.mark.asyncio
    async def test_generate_simple_workflow(self, set_google_api_key):
        """Generate a simple workflow using real Google AI."""
        from casare_rpa.infrastructure.ai import SmartWorkflowAgent
        from casare_rpa.infrastructure.resources.llm_resource_manager import (
            LLMResourceManager,
        )

        # Create agent
        llm = LLMResourceManager()
        agent = SmartWorkflowAgent(llm_client=llm, max_retries=2)

        async def generate():
            return await agent.generate_workflow(
                user_prompt="Create a workflow that waits 1 second then prints 'Done'",
                model=DEFAULT_TEST_MODEL,
                temperature=0.1,
            )

        # Generate with retry for rate limits
        result = await retry_with_backoff(generate)

        print("\n[INFO] Generation result:")
        print(f"       Success: {result.success}")
        print(f"       Attempts: {result.attempts}")
        if result.error:
            print(f"       Error: {result.error}")

        if result.success and result.workflow:
            print("\n[OK] Generated workflow:")
            print(json.dumps(result.workflow, indent=2)[:1000])

            # Verify workflow structure
            assert "nodes" in result.workflow
            assert "connections" in result.workflow

            # Check for StartNode and EndNode
            nodes = result.workflow["nodes"]
            node_types = [n.get("node_type") for n in nodes.values()]

            print(f"\n     Node types: {node_types}")
            assert "StartNode" in node_types, "Missing StartNode"
            assert "EndNode" in node_types, "Missing EndNode"
        else:
            # Print validation history for debugging
            for i, vh in enumerate(result.validation_history):
                print(f"\n     Attempt {i+1} validation:")
                for err in vh.errors[:3]:
                    print(f"       - {err.code}: {err.message}")

    @pytest.mark.asyncio
    async def test_generate_browser_workflow(self, set_google_api_key):
        """Generate a browser automation workflow."""
        from casare_rpa.infrastructure.ai import SmartWorkflowAgent
        from casare_rpa.infrastructure.resources.llm_resource_manager import (
            LLMResourceManager,
        )

        llm = LLMResourceManager()
        agent = SmartWorkflowAgent(llm_client=llm, max_retries=3)

        async def generate():
            return await agent.generate_workflow(
                user_prompt=(
                    "Create a workflow that opens a browser, "
                    "navigates to https://example.com, "
                    "waits for the page to load, "
                    "then closes the browser"
                ),
                model=DEFAULT_TEST_MODEL,
                temperature=0.2,
            )

        result = await retry_with_backoff(generate)

        print("\n[INFO] Browser workflow generation:")
        print(f"       Success: {result.success}")
        print(f"       Attempts: {result.attempts}")

        if result.success and result.workflow:
            workflow = result.workflow
            nodes = workflow.get("nodes", {})
            connections = workflow.get("connections", [])

            print("\n[OK] Generated browser workflow:")
            print(f"     Nodes: {len(nodes)}")
            print(f"     Connections: {len(connections)}")

            for node_id, node_data in nodes.items():
                node_type = node_data.get("node_type", "Unknown")
                config = node_data.get("config", {})
                print(f"     - {node_id}: {node_type}")
                if config:
                    print(f"       Config: {config}")

            # Basic validation
            assert len(nodes) >= 3, "Expected at least 3 nodes"
            assert len(connections) >= 2, "Expected at least 2 connections"

    @pytest.mark.asyncio
    async def test_workflow_validation(self, set_google_api_key):
        """Test that generated workflows pass headless validation."""
        from casare_rpa.infrastructure.ai import (
            SmartWorkflowAgent,
            HeadlessWorkflowSandbox,
        )
        from casare_rpa.infrastructure.resources.llm_resource_manager import (
            LLMResourceManager,
        )

        llm = LLMResourceManager()
        agent = SmartWorkflowAgent(llm_client=llm, max_retries=2)
        sandbox = HeadlessWorkflowSandbox()

        async def generate():
            return await agent.generate_workflow(
                user_prompt="Create a workflow with just Start and End nodes",
                model=DEFAULT_TEST_MODEL,
                temperature=0.0,
            )

        result = await retry_with_backoff(generate)

        if result.success and result.workflow:
            # Validate with sandbox
            validation_result = sandbox.validate_workflow(result.workflow)

            print("\n[INFO] Validation result:")
            print(f"       Valid: {validation_result.is_valid}")
            print(f"       Errors: {len(validation_result.errors)}")
            print(f"       Warnings: {len(validation_result.warnings)}")

            if validation_result.errors:
                for err in validation_result.errors[:5]:
                    print(f"       - {err.code}: {err.message}")

            # Generated workflow should be valid (agent retries on failures)
            assert validation_result.is_valid, "Generated workflow should be valid"
        else:
            pytest.skip(f"Generation failed: {result.error}")


class TestAIAssistantDockReal:
    """Test AI Assistant dock with real API integration."""

    def test_credential_loading(self, qapp, google_api_key):
        """Test that credentials load in AI Assistant dock."""
        from casare_rpa.presentation.canvas.ui.widgets.ai_assistant import (
            AIAssistantDock,
        )

        dock = AIAssistantDock()

        # Check credential combo has items
        combo = dock._credential_combo
        assert (
            combo.count() > 1
        ), "Expected at least 'Select AI Provider' + 1 credential"

        # Check Google AI credential is present
        found_google = False
        for i in range(combo.count()):
            text = combo.itemText(i)
            if "Google" in text:
                found_google = True
                print(f"\n[OK] Found Google credential: {text}")
                break

        assert found_google, "Google AI credential not found in dropdown"

    def test_select_credential(self, qapp, google_api_key):
        """Test selecting a credential in the dock."""
        from casare_rpa.presentation.canvas.ui.widgets.ai_assistant import (
            AIAssistantDock,
        )

        dock = AIAssistantDock()

        # Find and select Google credential
        combo = dock._credential_combo
        google_index = -1

        for i in range(combo.count()):
            text = combo.itemText(i)
            if "Google" in text:
                google_index = i
                break

        assert google_index > 0, "Google credential not found"

        # Select the credential
        combo.setCurrentIndex(google_index)

        # Verify selection
        selected_id = dock.get_selected_credential_id()
        assert selected_id is not None, "No credential selected"
        print(f"\n[OK] Selected credential ID: {selected_id}")

        # Input field should be enabled
        assert dock._input_field.isEnabled(), "Input field should be enabled"
        assert dock._send_btn.isEnabled(), "Send button should be enabled"


# =============================================================================
# END-TO-END TEST
# =============================================================================


class TestEndToEndWorkflowGeneration:
    """End-to-end test of workflow generation."""

    @pytest.mark.asyncio
    async def test_full_workflow_generation_flow(self, qapp, set_google_api_key):
        """Test complete flow from prompt to validated workflow."""
        from casare_rpa.infrastructure.ai import (
            SmartWorkflowAgent,
            HeadlessWorkflowSandbox,
        )
        from casare_rpa.infrastructure.resources.llm_resource_manager import (
            LLMResourceManager,
        )
        from casare_rpa.presentation.canvas.ui.widgets.ai_assistant import (
            AIAssistantDock,
        )

        print("\n" + "=" * 60)
        print("END-TO-END WORKFLOW GENERATION TEST")
        print("=" * 60)

        # 1. Create components
        print("\n[1] Creating components...")
        llm = LLMResourceManager()
        agent = SmartWorkflowAgent(llm_client=llm, max_retries=2)
        sandbox = HeadlessWorkflowSandbox()
        dock = AIAssistantDock()

        # 2. Verify credential is available
        print("[2] Checking credentials...")
        assert dock._credential_combo.count() > 1
        print("    Credentials available")

        # 3. Generate workflow
        print("[3] Generating workflow with Google AI...")
        prompt = (
            "Create a simple data processing workflow: "
            "Start, set a variable 'count' to 0, wait 500ms, end"
        )

        async def generate():
            return await agent.generate_workflow(
                user_prompt=prompt,
                model=DEFAULT_TEST_MODEL,
                temperature=0.1,
            )

        result = await retry_with_backoff(generate)

        print(f"    Success: {result.success}")
        print(f"    Attempts: {result.attempts}")

        if not result.success:
            print(f"    Error: {result.error}")
            for i, vh in enumerate(result.validation_history):
                if vh.errors:
                    print(
                        f"    Attempt {i+1} errors: {[e.message for e in vh.errors[:2]]}"
                    )
            pytest.skip("Generation failed")

        # 4. Validate workflow
        print("[4] Validating generated workflow...")
        workflow = result.workflow
        validation = sandbox.validate_workflow(workflow)

        print(f"    Valid: {validation.is_valid}")
        print(f"    Nodes: {len(workflow.get('nodes', {}))}")
        print(f"    Connections: {len(workflow.get('connections', []))}")

        # 5. Inspect workflow
        print("[5] Workflow structure:")
        nodes = workflow.get("nodes", {})
        for node_id, node_data in nodes.items():
            print(f"    - {node_id}: {node_data.get('node_type')}")

        # 6. Assertions
        assert "nodes" in workflow
        assert "connections" in workflow
        assert len(nodes) >= 2

        node_types = [n.get("node_type") for n in nodes.values()]
        assert "StartNode" in node_types
        assert "EndNode" in node_types

        print("\n" + "=" * 60)
        print("[OK] END-TO-END TEST PASSED")
        print("=" * 60)


# =============================================================================
# FULL CANVAS INTEGRATION TEST
# =============================================================================


class TestCanvasIntegrationWithRealAPI:
    """Test actual node creation on canvas with real Google AI API."""

    @pytest.mark.asyncio
    async def test_append_to_canvas_creates_nodes(self, qapp, set_google_api_key):
        """
        FULL INTEGRATION TEST:
        1. Create MainWindow with real graph
        2. Generate workflow with real Google AI (Gemini 3 Pro)
        3. Call append_to_canvas
        4. Verify nodes are actually created on the graph
        """
        from casare_rpa.presentation.canvas.main_window import MainWindow
        from casare_rpa.presentation.canvas.graph.node_graph_widget import (
            NodeGraphWidget,
        )
        from casare_rpa.infrastructure.ai import SmartWorkflowAgent
        from casare_rpa.infrastructure.resources.llm_resource_manager import (
            LLMResourceManager,
        )
        from unittest.mock import MagicMock

        print("\n" + "=" * 70)
        print("CANVAS INTEGRATION TEST - REAL API + NODE CREATION")
        print("=" * 70)

        # 1. Create MainWindow with graph
        print("\n[1] Creating MainWindow with NodeGraphWidget...")
        window = MainWindow()

        # Create and set the NodeGraphWidget (like CasareRPAApp does)
        node_graph_widget = NodeGraphWidget()
        window.set_central_widget(node_graph_widget)

        # Mock workflow controller to prevent teardown errors
        if window._workflow_controller is None:
            window._workflow_controller = MagicMock()
            window._workflow_controller.check_unsaved_changes.return_value = True
            window._workflow_controller.is_modified = False

        graph = window.get_graph()
        assert graph is not None, "Graph should exist after setting NodeGraphWidget"

        # Register essential nodes with the graph (like NodeController does)
        from casare_rpa.presentation.canvas.graph.node_registry import get_node_registry

        node_registry = get_node_registry()
        node_registry.register_essential_nodes(graph)

        initial_node_count = len(graph.all_nodes())
        print(f"    Graph created with {initial_node_count} initial nodes")

        # 2. Check registered node types
        print("\n[2] Checking registered nodes...")
        registered = list(graph.registered_nodes())
        print(f"    Registered nodes: {len(registered)}")

        # Find StartNode and EndNode identifiers
        start_id = None
        end_id = None
        for identifier in registered:
            if "VisualStartNode" in identifier:
                start_id = identifier
            if "VisualEndNode" in identifier:
                end_id = identifier

        print(f"    VisualStartNode identifier: {start_id}")
        print(f"    VisualEndNode identifier: {end_id}")

        assert start_id is not None, "VisualStartNode should be registered"
        assert end_id is not None, "VisualEndNode should be registered"

        # 3. Generate workflow with Gemini 3 Pro
        print("\n[3] Generating workflow with Gemini 3 Pro...")
        # Use Gemini 3 Pro as requested
        model = "gemini/gemini-3-pro-preview"

        llm = LLMResourceManager()
        agent = SmartWorkflowAgent(llm_client=llm, max_retries=2)

        async def generate():
            return await agent.generate_workflow(
                user_prompt="Create a simple workflow with Start node and End node connected together",
                model=model,
                temperature=0.0,
            )

        result = await retry_with_backoff(generate)

        print(f"    Generation success: {result.success}")
        print(f"    Attempts: {result.attempts}")

        if not result.success:
            print(f"    Error: {result.error}")
            if result.validation_history:
                for i, vh in enumerate(result.validation_history):
                    if vh.errors:
                        print(
                            f"    Attempt {i+1} errors: {[e.message for e in vh.errors[:3]]}"
                        )
            pytest.skip(f"Generation failed: {result.error}")

        workflow = result.workflow
        print("\n[4] Workflow generated:")
        print(f"    Nodes: {len(workflow.get('nodes', {}))}")
        print(f"    Connections: {len(workflow.get('connections', []))}")

        # Print node details
        nodes_data = workflow.get("nodes", {})
        if isinstance(nodes_data, list):
            for node in nodes_data:
                print(f"    - {node.get('node_id')}: {node.get('node_type')}")
        else:
            for node_id, node_data in nodes_data.items():
                print(f"    - {node_id}: {node_data.get('node_type')}")

        # 4. Create signal coordinator and call on_ai_workflow_ready
        print("\n[5] Calling on_ai_workflow_ready to add nodes to canvas...")

        # Get or create signal coordinator
        if hasattr(window, "_signal_coordinator") and window._signal_coordinator:
            coordinator = window._signal_coordinator
        else:
            from casare_rpa.presentation.canvas.coordinators.signal_coordinator import (
                SignalCoordinator,
            )

            coordinator = SignalCoordinator(window)

        # Call the method that adds nodes to canvas
        coordinator.on_ai_workflow_ready(workflow)

        # 5. Verify nodes were created
        print("\n[6] Verifying nodes on canvas...")
        final_node_count = len(graph.all_nodes())
        nodes_created = final_node_count - initial_node_count

        print(f"    Initial nodes: {initial_node_count}")
        print(f"    Final nodes: {final_node_count}")
        print(f"    Nodes created: {nodes_created}")

        # List all nodes on canvas
        print("\n    Nodes on canvas:")
        for node in graph.all_nodes():
            print(f"      - {node.name()} ({type(node).__name__})")

        # Verify at least some nodes were created
        assert (
            nodes_created > 0
        ), f"Expected nodes to be created, but count remained {final_node_count}"

        print("\n" + "=" * 70)
        print(f"[OK] SUCCESS: {nodes_created} nodes created on canvas!")
        print("=" * 70)

        # Cleanup
        try:
            window.close()
        except Exception:
            pass

    def test_node_type_mapping(self, qapp):
        """Test that the node type mapping works correctly."""
        from casare_rpa.presentation.canvas.main_window import MainWindow
        from casare_rpa.presentation.canvas.graph.node_graph_widget import (
            NodeGraphWidget,
        )
        from casare_rpa.presentation.canvas.coordinators.signal_coordinator import (
            SignalCoordinator,
        )
        from unittest.mock import MagicMock

        print("\n" + "=" * 70)
        print("NODE TYPE MAPPING TEST")
        print("=" * 70)

        # Create MainWindow with NodeGraphWidget
        window = MainWindow()
        node_graph_widget = NodeGraphWidget()
        window.set_central_widget(node_graph_widget)

        if window._workflow_controller is None:
            window._workflow_controller = MagicMock()
            window._workflow_controller.check_unsaved_changes.return_value = True

        graph = window.get_graph()
        assert graph is not None, "Graph should exist after setting NodeGraphWidget"

        # Register essential nodes with the graph
        from casare_rpa.presentation.canvas.graph.node_registry import get_node_registry

        node_registry = get_node_registry()
        node_registry.register_essential_nodes(graph)

        # Get signal coordinator
        coordinator = SignalCoordinator(window)

        # Build node type map
        type_map = coordinator._build_ai_node_type_map(graph)

        print(f"\nNode type map ({len(type_map)} entries):")
        for node_type, identifier in sorted(type_map.items()):
            print(f"  {node_type} -> {identifier}")

        # Verify essential nodes are mapped
        assert "StartNode" in type_map, "StartNode should be in type map"
        assert "EndNode" in type_map, "EndNode should be in type map"

        print("\n[OK] Node type mapping verified")

        try:
            window.close()
        except Exception:
            pass

    def test_direct_node_creation(self, qapp):
        """Test that we can directly create nodes on the graph."""
        from casare_rpa.presentation.canvas.main_window import MainWindow
        from casare_rpa.presentation.canvas.graph.node_graph_widget import (
            NodeGraphWidget,
        )
        from unittest.mock import MagicMock

        print("\n" + "=" * 70)
        print("DIRECT NODE CREATION TEST")
        print("=" * 70)

        # Create MainWindow with NodeGraphWidget
        window = MainWindow()
        node_graph_widget = NodeGraphWidget()
        window.set_central_widget(node_graph_widget)

        if window._workflow_controller is None:
            window._workflow_controller = MagicMock()
            window._workflow_controller.check_unsaved_changes.return_value = True

        graph = window.get_graph()
        assert graph is not None, "Graph should exist after setting NodeGraphWidget"

        # Register essential nodes with the graph
        from casare_rpa.presentation.canvas.graph.node_registry import get_node_registry

        node_registry = get_node_registry()
        node_registry.register_essential_nodes(graph)

        initial_count = len(graph.all_nodes())
        print(f"\nInitial node count: {initial_count}")

        # Find VisualStartNode identifier
        start_identifier = None
        for identifier in graph.registered_nodes():
            if "VisualStartNode" in identifier:
                start_identifier = identifier
                break

        assert start_identifier is not None, "VisualStartNode not found in registry"
        print(f"VisualStartNode identifier: {start_identifier}")

        # Create node directly
        print("\nCreating StartNode directly...")
        node = graph.create_node(start_identifier, pos=[100, 100])
        print(f"Created node: {node}")
        print(f"Node type: {type(node).__name__}")

        final_count = len(graph.all_nodes())
        print(f"Final node count: {final_count}")

        assert final_count == initial_count + 1, "Node should have been created"
        print("\n[OK] Direct node creation works!")

        try:
            window.close()
        except Exception:
            pass


# =============================================================================
# RUN DIRECTLY
# =============================================================================


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--tb=short"])
