from __future__ import annotations

import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from endstone_utilitystone.plugin import UtilityStone


def healPlayer(plugin: UtilityStone, target, sender=None) -> None:
    target.health = target.max_health
    plugin.messages.success(target, "You have been healed.")
    if sender is not None and target.unique_id != sender.unique_id:
        plugin.messages.success(sender, f"Healed {target.name}.")


def feedPlayer(plugin: UtilityStone, target, sender=None) -> None:
    console = plugin.server.command_sender
    plugin.server.dispatch_command(console, f'effect "{target.name}" saturation 1 255 true')
    plugin.messages.success(target, "Your hunger has been topped up.")
    if sender is not None and target.unique_id != sender.unique_id:
        plugin.messages.success(sender, f"Fed {target.name}.")


def toggleFlight(plugin: UtilityStone, target, sender=None) -> bool:
    enabled = not target.allow_flight
    target.allow_flight = enabled
    if not enabled:
        target.is_flying = False
    state = "enabled" if enabled else "disabled"
    plugin.messages.success(target, f"Flight {state}.")
    if sender is not None and target.unique_id != sender.unique_id:
        plugin.messages.success(sender, f"Flight {state} for {target.name}.")
    return enabled


def toggleGod(plugin: UtilityStone, target, sender=None) -> bool:
    protected = plugin.godPlayers
    if target.unique_id in protected:
        protected.discard(target.unique_id)
        state = "disabled"
    else:
        protected.add(target.unique_id)
        state = "enabled"
    plugin.messages.success(target, f"God mode {state}.")
    if sender is not None and target.unique_id != sender.unique_id:
        plugin.messages.success(sender, f"God mode {state} for {target.name}.")
    return state == "enabled"
