"""
Unit & regression tests for the UtilityStone Broadcast System & Admin Panel Broadcast Manager.
"""

from __future__ import annotations

import pathlib
import sys
import types
import unittest
from unittest import mock

_WORKTREE_SRC = pathlib.Path(__file__).resolve().parent.parent / "src"
if str(_WORKTREE_SRC) not in sys.path:
    sys.path.insert(0, str(_WORKTREE_SRC))
for _name in list(sys.modules):
    if _name == "endstone_utilitystone" or _name.startswith("endstone_utilitystone."):
        del sys.modules[_name]


class TestBroadcastSettings(unittest.TestCase):
    def test_broadcast_settings_defaults(self):
        from endstone_utilitystone.core.settings import Settings
        s = Settings()
        self.assertTrue(s.broadcastsEnabled)
        self.assertEqual(s.broadcastsIntervalSeconds, 1200.0)
        self.assertTrue(s.broadcastsCycle)
        self.assertFalse(s.broadcastsSendOnStartup)
        self.assertIn("Discord", s.broadcastsMessages[0])


class TestBroadcastService(unittest.TestCase):
    def setUp(self):
        from endstone_utilitystone.services.broadcasts import BroadcastService

        self.messages_sent = []
        self.tasks_scheduled = []
        self.tasks_cancelled = []

        class TaskStub:
            def __init__(self, tid):
                self.task_id = tid

        def fake_run_task(plugin, func, delay, period):
            tid = len(self.tasks_scheduled) + 1
            self.tasks_scheduled.append((tid, delay, period, func))
            return TaskStub(tid)

        def fake_cancel_task(tid):
            self.tasks_cancelled.append(tid)

        self.player = types.SimpleNamespace(
            unique_id="p1",
            name="TestPlayer",
            send_message=lambda m: self.messages_sent.append(m),
        )

        self.plugin = types.SimpleNamespace(
            logger=types.SimpleNamespace(warning=lambda m: None, info=lambda m: None),
            server=types.SimpleNamespace(
                scheduler=types.SimpleNamespace(
                    run_task=fake_run_task,
                    cancel_task=fake_cancel_task,
                ),
                online_players=[self.player],
            ),
            settings=types.SimpleNamespace(
                broadcastsEnabled=True,
                broadcastsIntervalSeconds=1200.0,
                broadcastsCycle=True,
                broadcastsSendOnStartup=False,
                broadcastsPrefix="&8[&bBroadcast&8]&r ",
                broadcastsMessages=["Msg 1", "Msg 2"],
            ),
            data_folder="/tmp",
            reloadSettings=lambda: None,
        )

        self.service = BroadcastService(self.plugin)

    def test_reload_starts_schedule(self):
        self.service.reload()
        self.assertTrue(self.service.enabled)
        self.assertEqual(len(self.tasks_scheduled), 1)
        self.assertEqual(self.service._taskId, 1)

    def test_changing_interval_restarts_schedule_without_duplicate_active_tasks(self):
        self.service.reload()
        self.assertEqual(len(self.tasks_scheduled), 1)

        self.service.setInterval(600.0)
        self.assertEqual(len(self.tasks_scheduled), 2)
        self.assertEqual(self.tasks_cancelled, [1])
        self.assertEqual(self.service._taskId, 2)

    def test_disable_stops_schedule(self):
        self.service.reload()
        self.service.setEnabled(False)
        self.assertFalse(self.service.enabled)
        self.assertEqual(self.tasks_cancelled, [1])
        self.assertIsNone(self.service._taskId)

    def test_broadcast_next_cycles_messages(self):
        self.service.reload()
        # First call -> Msg 1
        self.service.broadcastNext()
        self.assertTrue(any("Msg 1" in m for m in self.messages_sent))

        self.messages_sent.clear()
        # Second call -> Msg 2
        self.service.broadcastNext()
        self.assertTrue(any("Msg 2" in m for m in self.messages_sent))

    def test_send_specific_message(self):
        self.service.reload()
        self.messages_sent.clear()
        self.service.broadcastNext(specific_message="Custom Alert")
        self.assertTrue(any("Custom Alert" in m for m in self.messages_sent))


class TestBroadcastAdminUI(unittest.TestCase):
    def setUp(self):
        from endstone_utilitystone.ui import admin_menu
        self.admin_menu = admin_menu

        self.sent_forms = []
        self.failures = []

        self.admin = types.SimpleNamespace(
            name="AdminPlayer",
            unique_id="admin-1",
            is_valid=True,
            has_permission=lambda p: True,
        )

        self.plugin = types.SimpleNamespace(
            logger=types.SimpleNamespace(info=lambda m: None, warning=lambda m: None),
            messages=types.SimpleNamespace(
                failure=lambda p, m: self.failures.append(m),
                success=lambda p, m: None,
                info=lambda p, m: None,
            ),
            gui=types.SimpleNamespace(
                safePlayer=lambda p: p,
                sendForm=lambda p, f, label="": self.sent_forms.append((f, label)) or True,
                wrapClick=lambda p, cb, l="": (lambda: cb()),
                wrapSubmit=lambda p, cb, l="": (lambda player, data: cb(player, data)),
                wrapClose=lambda p, l="": (lambda player: None),
            ),
            settings=types.SimpleNamespace(
                broadcastsEnabled=True,
                broadcastsIntervalSeconds=1200.0,
                broadcastsCycle=True,
                broadcastsSendOnStartup=False,
                broadcastsPrefix="&8[&bBroadcast&8]&r ",
                broadcastsMessages=["Msg 1"],
            ),
            broadcasts=types.SimpleNamespace(
                enabled=True,
                intervalSeconds=1200.0,
                messages=["Msg 1"],
                broadcastNext=lambda specific_message=None: True,
                setEnabled=lambda e: None,
                setInterval=lambda s: None,
                addMessage=lambda m: None,
                editMessage=lambda i, m: None,
                deleteMessage=lambda i: None,
            ),
            data_folder="/tmp",
            reloadSettings=lambda: None,
        )

    def test_unauthorized_access_blocked(self):
        unauth = types.SimpleNamespace(
            name="User",
            has_permission=lambda p: False,
        )
        self.admin_menu.openBroadcastManager(self.plugin, unauth)
        self.assertEqual(len(self.failures), 1)
        self.assertIn("permission", self.failures[0])

    def test_open_broadcast_manager(self):
        self.admin_menu.openBroadcastManager(self.plugin, self.admin)
        self.assertTrue(self.sent_forms)
        form, label = self.sent_forms[-1]
        self.assertEqual(label, "broadcast_manager")
        self.assertIn("Manage Broadcasts", form.title)


if __name__ == "__main__":
    unittest.main(verbosity=2)
