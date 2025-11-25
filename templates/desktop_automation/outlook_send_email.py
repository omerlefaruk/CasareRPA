"""
Outlook Send Email Template

Demonstrates sending an email via Microsoft Outlook automation.

Usage:
    python templates/desktop_automation/outlook_send_email.py
"""

import sys
from pathlib import Path

src_path = Path(__file__).parent.parent.parent / "src"
if src_path.exists():
    sys.path.insert(0, str(src_path))

import asyncio
from casare_rpa.core.workflow_schema import WorkflowSchema, WorkflowMetadata, NodeConnection
from casare_rpa.runner.workflow_runner import WorkflowRunner
from casare_rpa.nodes.basic_nodes import StartNode, EndNode
from casare_rpa.nodes.desktop_nodes import OutlookSendEmailNode
from casare_rpa.nodes.variable_nodes import SetVariableNode


async def create_outlook_email_workflow() -> WorkflowSchema:
    """
    Create a workflow that sends an email via Outlook.

    Workflow:
        Start → Set Variables → Send Email → End
    """
    metadata = WorkflowMetadata(name="Outlook Send Email Demo")

    # Create nodes
    start = StartNode("start_1")

    set_recipient = SetVariableNode("set_recipient",
        variable_name="email_to",
        default_value="recipient@example.com"
    )

    set_subject = SetVariableNode("set_subject",
        variable_name="email_subject",
        default_value="Test Email from CasareRPA"
    )

    set_body = SetVariableNode("set_body",
        variable_name="email_body",
        default_value="This email was sent automatically by CasareRPA Desktop Automation."
    )

    send_email = OutlookSendEmailNode("send_email", config={
        "html_body": False
    })

    end = EndNode("end_1")

    # Build workflow
    nodes = {
        "start_1": start,
        "set_recipient": set_recipient,
        "set_subject": set_subject,
        "set_body": set_body,
        "send_email": send_email,
        "end_1": end
    }

    connections = [
        NodeConnection("start_1", "exec_out", "set_recipient", "exec_in"),
        NodeConnection("set_recipient", "exec_out", "set_subject", "exec_in"),
        NodeConnection("set_subject", "exec_out", "set_body", "exec_in"),
        NodeConnection("set_body", "exec_out", "send_email", "exec_in"),
        NodeConnection("set_recipient", "value", "send_email", "to"),
        NodeConnection("set_subject", "value", "send_email", "subject"),
        NodeConnection("set_body", "value", "send_email", "body"),
        NodeConnection("send_email", "exec_out", "end_1", "exec_in"),
    ]

    workflow = WorkflowSchema(metadata)
    workflow.nodes = nodes
    workflow.connections = connections

    return workflow


async def main():
    """Run the Outlook email workflow."""
    print("=" * 60)
    print("Outlook Send Email Template")
    print("=" * 60)

    print("\n WARNING: This will attempt to send an actual email!")
    print("Make sure to update the recipient address before running.")

    workflow = await create_outlook_email_workflow()
    runner = WorkflowRunner(workflow)

    # Note: Uncomment to actually run
    # await runner.run()
    print("\n Workflow created (not executed - uncomment to run)")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
