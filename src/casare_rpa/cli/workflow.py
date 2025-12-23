"""
CasareRPA Workflow Generation CLI.

Provides commands for generating RPA workflows from natural language prompts.
"""

import asyncio
import json
import os
import re
from pathlib import Path
from typing import Optional

import typer
from dotenv import load_dotenv
from loguru import logger

# Load environment variables from .env file
load_dotenv()

app = typer.Typer(name="workflow", help="Workflow generation tools")


def _resolve_path_references(prompt: str) -> str:
    """
    Resolve common path references in the prompt.

    Replaces phrases like "my Documents folder" with actual paths.

    Args:
        prompt: User's natural language prompt

    Returns:
        Prompt with resolved paths
    """
    # Pattern: "my Documents folder" or "Documents folder" or "the Documents"
    # Use raw strings (r"...") for regex patterns
    documents_pattern = re.compile(r"(my\s+|the\s+)?documents\s*(folder)?", re.IGNORECASE)
    downloads_pattern = re.compile(r"(my\s+|the\s+)?downloads\s*(folder)?", re.IGNORECASE)
    desktop_pattern = re.compile(r"(my\s+|the\s+)?desktop\s*(folder)?", re.IGNORECASE)

    # Get actual paths as strings with forward slashes (cross-platform safe)
    documents_path = str(Path.home() / "Documents").replace("\\", "/")
    downloads_path = str(Path.home() / "Downloads").replace("\\", "/")
    desktop_path = str(Path.home() / "Desktop").replace("\\", "/")

    # Replace patterns with actual paths
    prompt = documents_pattern.sub(documents_path, prompt)
    prompt = downloads_pattern.sub(downloads_path, prompt)
    prompt = desktop_pattern.sub(desktop_path, prompt)

    return prompt


def _get_model_from_settings() -> str:
    """Get AI model from config/settings.json."""
    settings_path = Path(__file__).parent.parent.parent.parent / "config" / "settings.json"
    default_model = "openrouter/google/gemini-3-flash-preview"

    try:
        if settings_path.exists():
            with open(settings_path, encoding="utf-8") as f:
                settings = json.load(f)
                model = settings.get("ai", {}).get("model", default_model)
                return model
    except Exception:
        pass

    return default_model


async def _generate_workflow_async(
    prompt: str,
    output_path: Path | None,
    validate_only: bool = False,
) -> dict | None:
    """
    Generate workflow using SmartWorkflowAgent.

    Args:
        prompt: Natural language description of the workflow
        output_path: Optional path to save the generated workflow
        validate_only: If True, only validate against WorkflowBuilder, don't save

    Returns:
        Generated workflow dict or None on failure
    """
    from casare_rpa.domain.ai import AgentConfig, PerformanceConfig, WaitStrategy
    from casare_rpa.infrastructure.ai import (
        SmartWorkflowAgent,
        WorkflowGenerationResult,
    )
    from casare_rpa.tools.workflow_builder import WorkflowBuilder

    # Resolve path references in prompt
    resolved_prompt = _resolve_path_references(prompt)

    # Get model from settings
    model = _get_model_from_settings()

    typer.echo("=" * 60)
    typer.echo("🤖 CasareRPA Workflow Generator")
    typer.echo("=" * 60)
    typer.echo(f"\n📝 Prompt:\n{resolved_prompt}")
    typer.echo(f"🤖 Model: {model}\n")
    typer.echo("=" * 60)
    typer.echo("\n⏳ Generating workflow with AI...")

    try:
        # Create custom config with model from settings
        config = AgentConfig(
            model=model,
            performance=PerformanceConfig(
                wait_strategy=WaitStrategy.SMART_WAITS,
            ),
            temperature=0.2,
            max_tokens=8000,
        )

        agent = SmartWorkflowAgent(config=config)

        # Generate workflow
        result: WorkflowGenerationResult = await agent.generate_workflow(resolved_prompt)

        if not result.success:
            typer.echo(f"\n❌ Generation failed: {result.error}", err=True)
            if result.validation_history:
                typer.echo("\n📝 Validation History:")
                for i, validation in enumerate(result.validation_history):
                    typer.echo(f"   Attempt {i + 1}: {len(validation.errors)} errors")
                    for error in validation.errors[:3]:
                        typer.echo(f"      - {error.message}")
            return None

        workflow = result.workflow

        typer.echo("\n✅ Workflow generated successfully!")
        typer.echo(f"   Attempts: {result.attempts}")
        typer.echo(f"   Generation time: {result.generation_time_ms:.2f}ms")
        typer.echo(
            f"   Nodes: {len(workflow.get('nodes', {}))}, "
            f"Connections: {len(workflow.get('connections', []))}"
        )

        # Safety validation with WorkflowBuilder
        typer.echo("\n🔍 Running safety validation...")
        builder = WorkflowBuilder()
        builder.workflow_data = workflow

        # WorkflowBuilder.save() performs validation internally
        # We use a temp path to trigger validation without committing
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            builder.save(tmp_path)
            typer.echo("   ✅ Safety validation passed")
        except Exception as e:
            typer.echo(f"   ⚠️ Safety validation warning: {e}", err=True)
            # Continue anyway, as warnings are logged but not fatal
        finally:
            # Clean up temp file
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

        if validate_only:
            typer.echo("\n📋 Generated Workflow JSON:")
            typer.echo("-" * 40)
            typer.echo(json.dumps(workflow, indent=2, ensure_ascii=False))
            return workflow

        # Save to output path
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(workflow, f, indent=2, ensure_ascii=False)
            typer.echo(f"\n💾 Saved to: {output_path}")
        else:
            # Print to stdout if no output path
            typer.echo("\n📋 Generated Workflow JSON:")
            typer.echo("-" * 40)
            typer.echo(json.dumps(workflow, indent=2, ensure_ascii=False))

        return workflow

    except ImportError as e:
        typer.echo(f"\n❌ Missing dependencies: {e}", err=True)
        typer.echo("   Ensure LLM dependencies are installed.", err=True)
        return None
    except Exception as e:
        typer.echo(f"\n❌ Error during generation: {e}", err=True)
        logger.exception("Workflow generation failed")
        return None


@app.command("generate")
def generate(
    prompt: str = typer.Argument(
        ...,
        help="Natural language description of the workflow to generate",
    ),
    output: str | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Path to save the generated workflow JSON",
    ),
    validate_only: bool = typer.Option(
        False,
        "--validate",
        "-v",
        help="Only validate and print, don't save",
    ),
):
    """
    Generate an RPA workflow from a natural language prompt.

    Uses AI to create a complete workflow JSON that can be loaded in the Canvas.

    Examples:
        casare workflow generate "Open google.com and search for 'test'"
        casare workflow generate "Extract table data from a website" -o my_workflow.json
    """
    output_path = Path(output) if output else None

    workflow = asyncio.run(_generate_workflow_async(prompt, output_path, validate_only))

    if workflow:
        typer.echo("\n✅ Done! You can load this workflow in the CasareRPA canvas.")
        raise typer.Exit(0)
    else:
        typer.echo("\n⚠️ Workflow generation was not successful.", err=True)
        typer.echo("   Make sure you have LLM API credentials configured in .env", err=True)
        raise typer.Exit(1)


@app.command("schema")
def show_schema():
    """
    Show the JSON schema expected for workflows.

    Useful for understanding the structure of generated workflows
    or for manually creating workflows.
    """
    from casare_rpa.domain.schemas.workflow_ai import WorkflowAISchema

    schema_info = WorkflowAISchema.from_natural_language_hint()

    typer.echo("📋 CasareRPA Workflow JSON Schema")
    typer.echo("=" * 60)
    typer.echo(json.dumps(schema_info, indent=2, ensure_ascii=False))


async def _edit_workflow_async(
    workflow_path: Path,
    instruction: str,
) -> dict | None:
    """
    Edit an existing workflow using AI.

    Args:
        workflow_path: Path to the existing workflow JSON
        instruction: Natural language description of desired changes

    Returns:
        Modified workflow dict or None on failure
    """
    from casare_rpa.domain.ai import AgentConfig, PerformanceConfig, WaitStrategy
    from casare_rpa.infrastructure.ai import SmartWorkflowAgent

    # Load existing workflow
    if not workflow_path.exists():
        typer.echo(f"❌ Workflow not found: {workflow_path}", err=True)
        return None

    with open(workflow_path, encoding="utf-8") as f:
        workflow = json.load(f)

    # Resolve path references in instruction
    resolved_instruction = _resolve_path_references(instruction)

    typer.echo("=" * 60)
    typer.echo("🔧 CasareRPA Workflow Editor")
    typer.echo("=" * 60)
    typer.echo(f"\n📄 Workflow: {workflow_path}")
    typer.echo(f"📝 Instruction: {resolved_instruction}\n")
    typer.echo("=" * 60)
    typer.echo("\n⏳ Applying edits with AI...")

    # Get model from settings
    model = _get_model_from_settings()
    typer.echo(f"🤖 Model: {model}")

    try:
        # Create config for editing with model from settings
        config = AgentConfig(
            model=model,
            performance=PerformanceConfig(
                wait_strategy=WaitStrategy.SMART_WAITS,
            ),
            temperature=0.2,
            max_tokens=8000,
        )

        agent = SmartWorkflowAgent(config=config)

        # Build a prompt that includes the current workflow and asks for modifications
        workflow_json = json.dumps(workflow, indent=2)
        edit_prompt = f"""Modify the following existing workflow according to these instructions:

INSTRUCTIONS: {resolved_instruction}

CURRENT WORKFLOW:
```json
{workflow_json}
```

Return the COMPLETE MODIFIED WORKFLOW JSON. Keep all unchanged parts the same. Apply only the requested changes."""

        # Use generate mode (not edit mode) to get a complete workflow back
        result = await agent.generate_workflow(edit_prompt)

        if not result.success:
            typer.echo(f"\n❌ Edit failed: {result.error}", err=True)
            return None

        modified_workflow = result.workflow

        typer.echo("\n✅ Workflow edited successfully!")
        typer.echo(f"   Nodes: {len(modified_workflow.get('nodes', {}))}")

        # Save the modified workflow
        with open(workflow_path, "w", encoding="utf-8") as f:
            json.dump(modified_workflow, f, indent=2, ensure_ascii=False)
        typer.echo(f"\n💾 Saved to: {workflow_path}")

        return modified_workflow

    except Exception as e:
        typer.echo(f"\n❌ Error during edit: {e}", err=True)
        logger.exception("Workflow editing failed")
        return None


@app.command("edit")
def edit(
    workflow_file: str = typer.Argument(
        ...,
        help="Path to the workflow JSON file to edit",
    ),
    instruction: str = typer.Argument(
        ...,
        help="Natural language description of the changes to make",
    ),
):
    """
    Edit an existing workflow with natural language instructions.

    Uses AI to modify an existing workflow based on your description.

    Examples:
        casare workflow edit my_workflow.json "Add a 3 second wait before extraction"
        casare workflow edit flow.json "Change save path to Desktop"
        casare workflow edit flow.json "Insert a debug node after the click"
    """
    workflow_path = Path(workflow_file)

    result = asyncio.run(_edit_workflow_async(workflow_path, instruction))

    if result:
        typer.echo("\n✅ Done! Reload the workflow in CasareRPA canvas to see changes.")
        raise typer.Exit(0)
    else:
        typer.echo("\n⚠️ Workflow editing was not successful.", err=True)
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
