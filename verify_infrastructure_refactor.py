"""
Verify infrastructure refactoring.
"""

import sys
import traceback


def verify_infrastructure():
    print("Verifying infrastructure refactor...")

    try:
        # 1. Check new structure imports
        print("Checking new structure imports...")
        from casare_rpa.infrastructure.ai.agent.core import SmartWorkflowAgent
        from casare_rpa.infrastructure.ai.agent.exceptions import (
            WorkflowGenerationError,
        )

        print("✅ New structure imports successful")

        # 2. Check shim imports
        print("Checking shim imports...")
        from casare_rpa.infrastructure.ai.smart_agent import (
            SmartWorkflowAgent as ShimAgent,
        )

        assert ShimAgent is SmartWorkflowAgent
        print("✅ Shim imports successful")

        # 3. Check consolidated infrastructure imports
        print("Checking consolidated infrastructure imports...")
        from casare_rpa.infrastructure import (
            SmartWorkflowAgent as RootAgent,
            PlaywrightManager,
            VaultClient,
            MetricsAggregator,
        )

        assert RootAgent is SmartWorkflowAgent
        print("✅ Consolidated infrastructure imports successful")

        print("\nALL VERIFICATIONS PASSED")
        return 0
    except Exception as e:
        print(f"\n❌ VERIFICATION FAILED: {e}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(verify_infrastructure())
