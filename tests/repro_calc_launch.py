import asyncio
import sys
from loguru import logger
from casare_rpa.desktop.managers.window_manager import WindowManager

# Configure logger
logger.remove()
logger.add(sys.stderr, level="DEBUG")


async def test_calc_launch():
    wm = WindowManager()
    try:
        logger.info("Launching Calculator...")
        # Using "calc" which resolves to calc.exe on Windows
        # Timeout 10s
        window = await wm.launch_application("calc", timeout=10.0)
        logger.success(f"Successfully launched and found window: {window.get_text()}")

        await asyncio.sleep(2)

        logger.info("Closing Calculator...")
        await wm.close_application(window)
        logger.success("Closed Calculator")

    except Exception as e:
        logger.error(f"Test failed: {e}")
        logger.info("Dumping visible windows...")
        try:
            windows = await wm.get_all_windows()
            for w in windows:
                logger.info(
                    f"Window: '{w.get_text()}' | PID: {w._control.ProcessId} | Class: {w._control.ClassName}"
                )
        except Exception as ex:
            logger.error(f"Failed to dump windows: {ex}")
        raise
    finally:
        wm.cleanup()


if __name__ == "__main__":
    asyncio.run(test_calc_launch())
