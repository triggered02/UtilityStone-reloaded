"""
Broadcast Service — Automated server-wide broadcasts and scheduling.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from endstone_utilitystone.plugin import UtilityStone


class BroadcastService:
    def __init__(self, plugin: UtilityStone):
        self.plugin = plugin
        self._taskId: int | None = None
        self._currentIndex = 0
        self.enabled = True
        self.intervalSeconds = 1200.0
        self.cycle = True
        self.sendOnStartup = False
        self.prefix = "&8[&bBroadcast&8]&r "
        self.messages: list[str] = ["Join our Discord server!\nhttps://discord.gg/gHpgjRTCnu"]

    def reload(self) -> None:
        self.stopSchedule()
        settings = self.plugin.settings
        self.enabled = settings.broadcastsEnabled
        self.intervalSeconds = settings.broadcastsIntervalSeconds
        self.cycle = settings.broadcastsCycle
        self.sendOnStartup = settings.broadcastsSendOnStartup
        self.prefix = settings.broadcastsPrefix
        self.messages = list(settings.broadcastsMessages)

        if self.enabled and self.messages and self.intervalSeconds > 0:
            self.startSchedule(immediate=self.sendOnStartup)

    def startSchedule(self, immediate: bool = False) -> None:
        self.stopSchedule()
        if not self.enabled or not self.messages or self.intervalSeconds <= 0:
            return

        interval_ticks = int(max(1.0, self.intervalSeconds) * 20)

        if immediate:
            self.broadcastNext()

        try:
            task = self.plugin.server.scheduler.run_task(
                self.plugin,
                self._tick,
                delay=interval_ticks,
                period=interval_ticks,
            )
            if task is not None and hasattr(task, "task_id"):
                self._taskId = task.task_id
        except Exception as exc:
            self.plugin.logger.warning(f"Could not schedule broadcast task: {exc}")

    def stopSchedule(self) -> None:
        if self._taskId is not None:
            try:
                self.plugin.server.scheduler.cancel_task(self._taskId)
            except Exception:
                pass
            self._taskId = None

    def _tick(self) -> None:
        self.broadcastNext()

    def broadcastNext(self, specific_message: str | None = None) -> bool:
        if specific_message is not None:
            text = specific_message
        else:
            if not self.messages:
                return False
            if self._currentIndex >= len(self.messages):
                self._currentIndex = 0
            text = self.messages[self._currentIndex]
            if self.cycle and len(self.messages) > 1:
                self._currentIndex = (self._currentIndex + 1) % len(self.messages)

        from endstone_utilitystone.util.text import colorize
        formatted = colorize(f"{self.prefix}{text}")

        try:
            players = list(self.plugin.server.online_players)
            for player in players:
                try:
                    for line in formatted.split("\n"):
                        player.send_message(line)
                except Exception:
                    pass
        except Exception as exc:
            self.plugin.logger.warning(f"Failed to deliver broadcast: {exc}")
            return False

        return True

    def setEnabled(self, enabled: bool) -> None:
        self.enabled = enabled
        if self.enabled:
            self.startSchedule(immediate=False)
        else:
            self.stopSchedule()

    def setInterval(self, interval_seconds: float) -> None:
        self.intervalSeconds = max(5.0, interval_seconds)
        if self.enabled:
            self.startSchedule(immediate=False)

    def addMessage(self, message: str) -> None:
        msg = message.strip()
        if msg:
            self.messages.append(msg)
            if self.enabled and self._taskId is None:
                self.startSchedule(immediate=False)

    def editMessage(self, index: int, new_message: str) -> bool:
        msg = new_message.strip()
        if 0 <= index < len(self.messages) and msg:
            self.messages[index] = msg
            return True
        return False

    def deleteMessage(self, index: int) -> bool:
        if 0 <= index < len(self.messages):
            self.messages.pop(index)
            if self._currentIndex >= len(self.messages):
                self._currentIndex = 0
            if not self.messages:
                self.stopSchedule()
            return True
        return False
