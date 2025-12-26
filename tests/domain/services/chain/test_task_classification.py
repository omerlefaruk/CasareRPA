"""
Tests for task type classification in chain executor.

Tests the ChainClassifier's ability to map user descriptions
to appropriate task types and agent chains.
"""


from casare_rpa.domain.entities.chain import (
    AgentType,
    TaskType,
)


class TestChainClassifier:
    """Test task type classification."""

    def test_classify_implement_keywords(self, chain_executor):
        """'Add', 'create', 'build' → IMPLEMENT."""
        assert chain_executor.classify("Add OAuth2 support") == TaskType.IMPLEMENT
        assert chain_executor.classify("Create new node") == TaskType.IMPLEMENT
        assert chain_executor.classify("Build workflow engine") == TaskType.IMPLEMENT

    def test_classify_fix_keywords(self, chain_executor):
        """'Fix', 'bug', 'debug' → FIX."""
        assert chain_executor.classify("Fix null pointer") == TaskType.FIX
        assert chain_executor.classify("Bug in workflow loader") == TaskType.FIX
        assert chain_executor.classify("Debug crash on startup") == TaskType.FIX

    def test_classify_refactor_keywords(self, chain_executor):
        """'Refactor', 'clean', 'optimize' → REFACTOR."""
        assert chain_executor.classify("Refactor HTTP client") == TaskType.REFACTOR
        assert chain_executor.classify("Clean up legacy code") == TaskType.REFACTOR
        assert chain_executor.classify("Optimize database queries") == TaskType.REFACTOR

    def test_classify_research_keywords(self, chain_executor):
        """'Research', 'investigate', 'analyze' → RESEARCH."""
        assert chain_executor.classify("Research best practices") == TaskType.RESEARCH
        assert chain_executor.classify("Investigate performance issue") == TaskType.RESEARCH
        assert chain_executor.classify("Analyze architecture") == TaskType.RESEARCH

    def test_classify_extend_keywords(self, chain_executor):
        """'Extend', 'enhance' → EXTEND."""
        assert chain_executor.classify("Extend browser nodes") == TaskType.EXTEND
        # Note: "Enhance UI components" matches UI keyword first, which is correct
        assert chain_executor.classify("Enhance performance") == TaskType.EXTEND

    def test_classify_clone_keywords(self, chain_executor):
        """'Clone', 'duplicate', 'copy' → CLONE."""
        assert chain_executor.classify("Clone click node") == TaskType.CLONE
        assert chain_executor.classify("Duplicate pattern") == TaskType.CLONE

    def test_classify_test_keywords(self, chain_executor):
        """'Test', 'verify' → TEST."""
        assert chain_executor.classify("Test authentication") == TaskType.TEST
        assert chain_executor.classify("Verify behavior") == TaskType.TEST

    def test_classify_docs_keywords(self, chain_executor):
        """'Document', 'docs' → DOCS."""
        assert chain_executor.classify("Document API") == TaskType.DOCS
        assert chain_executor.classify("Update docs for feature") == TaskType.DOCS

    def test_classify_security_keywords(self, chain_executor):
        """'Security', 'audit' → SECURITY."""
        assert chain_executor.classify("Security audit") == TaskType.SECURITY
        assert chain_executor.classify("Audit authentication flow") == TaskType.SECURITY

    def test_classify_ui_keywords(self, chain_executor):
        """'UI', 'interface' → UI."""
        assert chain_executor.classify("Create UI for settings") == TaskType.UI
        assert chain_executor.classify("Fix interface bug") == TaskType.UI
        assert chain_executor.classify("Enhance UI components") == TaskType.UI  # UI takes priority

    def test_classify_integration_keywords(self, chain_executor):
        """'Integration', 'API' → INTEGRATION."""
        assert chain_executor.classify("Integration with Google API") == TaskType.INTEGRATION
        assert chain_executor.classify("API connector for service") == TaskType.INTEGRATION

    def test_classify_explicit_type(self, chain_executor):
        """Explicit task_type overrides classification."""
        result = chain_executor.classify("Fix this bug", TaskType.REFACTOR)
        assert result == TaskType.REFACTOR  # Not FIX

    def test_classify_default_to_implement(self, chain_executor):
        """Unknown descriptions default to IMPLEMENT."""
        assert chain_executor.classify("Something new") == TaskType.IMPLEMENT


class TestChainTemplates:
    """Test agent chain templates for each task type."""

    def test_implement_chain(self, chain_executor):
        """IMPLEMENT → EXPLORE → ARCHITECT → BUILDER → QUALITY → REVIEWER."""
        chain = chain_executor.get_chain_template(TaskType.IMPLEMENT)
        assert chain == [
            AgentType.EXPLORE,
            AgentType.ARCHITECT,
            AgentType.BUILDER,
            AgentType.QUALITY,
            AgentType.REVIEWER,
        ]

    def test_fix_chain(self, chain_executor):
        """FIX → EXPLORE → BUILDER → QUALITY → REVIEWER (no ARCHITECT)."""
        chain = chain_executor.get_chain_template(TaskType.FIX)
        assert chain == [
            AgentType.EXPLORE,
            AgentType.BUILDER,
            AgentType.QUALITY,
            AgentType.REVIEWER,
        ]
        assert AgentType.ARCHITECT not in chain

    def test_refactor_chain(self, chain_executor):
        """REFACTOR → EXPLORE → REFACTOR → QUALITY → REVIEWER."""
        chain = chain_executor.get_chain_template(TaskType.REFACTOR)
        assert chain == [
            AgentType.EXPLORE,
            AgentType.REFACTOR,
            AgentType.QUALITY,
            AgentType.REVIEWER,
        ]

    def test_research_chain(self, chain_executor):
        """RESEARCH → EXPLORE → RESEARCHER (no reviewer loop)."""
        chain = chain_executor.get_chain_template(TaskType.RESEARCH)
        assert chain == [
            AgentType.EXPLORE,
            AgentType.RESEARCHER,
        ]
        assert AgentType.REVIEWER not in chain

    def test_security_chain(self, chain_executor):
        """SECURITY → EXPLORE → SECURITY_AUDITOR → REVIEWER."""
        chain = chain_executor.get_chain_template(TaskType.SECURITY)
        assert chain == [
            AgentType.EXPLORE,
            AgentType.SECURITY_AUDITOR,
            AgentType.REVIEWER,
        ]

    def test_ui_chain(self, chain_executor):
        """UI → EXPLORE → UI → QUALITY → REVIEWER."""
        chain = chain_executor.get_chain_template(TaskType.UI)
        assert chain == [
            AgentType.EXPLORE,
            AgentType.UI,
            AgentType.QUALITY,
            AgentType.REVIEWER,
        ]
