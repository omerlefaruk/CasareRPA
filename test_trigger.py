"""
Test script for triggers - runs a workflow every 5 seconds
"""
import asyncio
from datetime import datetime

# Add src to path
import sys
sys.path.insert(0, 'src')

from casare_rpa.triggers.base import BaseTriggerConfig, TriggerEvent
from casare_rpa.triggers.implementations.scheduled import ScheduledTrigger


async def on_trigger_fired(event: TriggerEvent):
    """Called when the trigger fires."""
    print(f"\n{'='*50}")
    print(f"TRIGGER FIRED at {datetime.now().strftime('%H:%M:%S')}")
    print(f"  Trigger ID: {event.trigger_id}")
    print(f"  Payload: {event.payload}")
    print(f"{'='*50}\n")

    # Here you would run your workflow
    # For now, just print a message
    print("  -> Running workflow... (simulated)")


async def main():
    print("Starting trigger test - will fire every 5 seconds")
    print("Press Ctrl+C to stop\n")

    # Create trigger configuration
    config = BaseTriggerConfig(
        id="test-trigger-001",
        name="Every 5 Seconds Test",
        trigger_type="scheduled",
        scenario_id="test-scenario",
        workflow_id="test-workflow",
        enabled=True,
        priority=1,
        cooldown_seconds=0,
        config={
            "frequency": "interval",
            "interval_seconds": 5
        }
    )

    # Create the trigger
    trigger = ScheduledTrigger(config, event_callback=on_trigger_fired)

    # Validate config
    valid, error = trigger.validate_config()
    if not valid:
        print(f"Invalid config: {error}")
        return

    # Start the trigger
    success = await trigger.start()
    if not success:
        print(f"Failed to start trigger: {trigger._error_message}")
        return

    print(f"Trigger started! Next run: {trigger.get_next_run()}")

    try:
        # Keep running until Ctrl+C
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping trigger...")
    finally:
        await trigger.stop()
        print("Trigger stopped.")


if __name__ == "__main__":
    asyncio.run(main())
