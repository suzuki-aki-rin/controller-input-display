import asyncio
from core.gamepad import GamepadReader, find_device
from core.pollers import GamepadPoller, send_holded_buttons_async

#  =====================================================================
#            Logger
#  =====================================================================
import logging

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class GamepadManager:
    def __init__(self, device_name: str, button_queue: asyncio.Queue) -> None:
        self.device_name = device_name
        self.gamepad: GamepadReader | None = None
        self.poller: GamepadPoller | None = None

        self.task: asyncio.Task

        self.is_running = False
        self._queue = button_queue

    def is_connected(self) -> bool:
        return find_device(self.device_name) is not None

    async def notify_state(self, is_running: bool, is_connected: bool) -> None:
        await self._queue.put(
            {"type": "status", "is_running": is_running, "is_connected": is_connected}
        )

    async def start_task(self):
        if self.is_running:
            logger.error("already running: %s", self.device_name)
            return
        if not self.is_connected():
            logger.error("device is disconneted: %s", self.device_name)
            return

        try:
            self.gamepad = GamepadReader.from_device_name(self.device_name)
        except OSError:
            logger.error("device not found: %s", self.device_name)
            return

        self.poller = GamepadPoller(
            self.gamepad, lambda btns: send_holded_buttons_async(self._queue, btns)
        )
        self.is_running = True
        try:
            async with asyncio.TaskGroup() as tg:
                tg.create_task(self.poller.run_with_reader())
        except* asyncio.CancelledError:
            logger.error("cancellederror")
            raise asyncio.CancelledError
        except* OSError:
            logger.error("cable disconnected")
            # raise OSError
        finally:
            self.is_running = False
            self.gamepad = None
            self.poller = None
            await self.notify_state(self.is_running, False)

    async def start(self):
        self.task = asyncio.create_task(self.start_task())
        logger.debug("%s started", self.device_name)

    async def stop(self):
        self.task.cancel()
        logger.debug("%s stopped", self.device_name)
