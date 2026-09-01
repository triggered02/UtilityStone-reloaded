from __future__ import annotations

import json
import logging
import threading
import time
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from endstone_utilitystone.plugin import UtilityStone


class FormSession:
    __slots__ = ("playerId", "createdAt", "label")

    def __init__(self, playerId, label: str = ""):
        self.playerId = playerId
        self.createdAt = time.time()
        self.label = label


class FormManager:
    def __init__(self, plugin: UtilityStone):
        self.plugin = plugin
        self._sessions: dict[int, FormSession] = {}
        self._lock = threading.Lock()
        self._sessionTtl = 300.0

    def track(self, player, label: str = "") -> None:
        pid = player.unique_id
        with self._lock:
            self._sessions[pid] = FormSession(pid, label)

    def untrack(self, player) -> None:
        pid = player.unique_id
        with self._lock:
            self._sessions.pop(pid, None)

    def isTracked(self, player) -> bool:
        pid = player.unique_id
        with self._lock:
            return pid in self._sessions

    def cleanupExpired(self) -> None:
        now = time.time()
        with self._lock:
            expired = [pid for pid, s in self._sessions.items() if now - s.createdAt > self._sessionTtl]
            for pid in expired:
                self._sessions.pop(pid, None)

    def onPlayerQuit(self, player) -> None:
        self.untrack(player)

    def safePlayer(self, player):
        try:
            if player.is_valid:
                return player
        except Exception:
            pass
        return None

    def wrapSubmit(self, player, callback: Callable[[Any, Any], None], actionLabel: str = "") -> Callable[[Any, Any], None]:
        def onSubmit(p, data):
            try:
                current = self.safePlayer(p)
                if current is None:
                    return
                if current.unique_id != player.unique_id:
                    return
                callback(current, data)
            except Exception as exc:
                self.plugin.logger.error(f"Form callback error ({actionLabel}): {exc}", exc_info=True)
                try:
                    current = self.safePlayer(p)
                    if current is not None:
                        self.plugin.messages.failure(current, "That action encountered an error.")
                except Exception:
                    pass

        return onSubmit

    def wrapClick(self, player, callback: Callable[[], None], actionLabel: str = "") -> Callable[[Any], None]:
        def onClick(p):
            try:
                current = self.safePlayer(p)
                if current is None:
                    return
                if current.unique_id != player.unique_id:
                    return
                callback()
            except Exception as exc:
                self.plugin.logger.error(f"Form click callback error ({actionLabel}): {exc}", exc_info=True)
                try:
                    current = self.safePlayer(p)
                    if current is not None:
                        self.plugin.messages.failure(current, "That action encountered an error.")
                except Exception:
                    pass

        return onClick

    def wrapClose(self, player, actionLabel: str = "") -> Callable[[Any], None]:
        def onClose(p):
            try:
                current = self.safePlayer(p)
                if current is not None and current.unique_id == player.unique_id:
                    self.untrack(current)
            except Exception:
                pass

        return onClose

    def sendForm(self, player, form, label: str = "") -> bool:
        try:
            self.track(player, label)
            player.send_form(form)
            return True
        except Exception as exc:
            self.plugin.logger.error(f"Failed to send form '{label}': {exc}")
            self.untrack(player)
            try:
                self.plugin.messages.failure(player, "Could not open that menu.")
            except Exception:
                pass
            return False

    def parseModalData(self, data: str) -> list | None:
        try:
            parsed = json.loads(data)
            if isinstance(parsed, list):
                return parsed
            return [parsed] if parsed is not None else []
        except (json.JSONDecodeError, TypeError):
            return None
