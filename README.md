# UtilityStone Reloaded

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Endstone](https://img.shields.io/badge/Endstone-0.11%2B-blue.svg)](https://endstone.dev)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Discord](https://img.shields.io/badge/Discord-Join%20Community-7289da.svg)](https://discord.gg/gHpgjRTCnu)

An essentials-style utility toolkit and UI suite for [Endstone](https://endstone.dev) Bedrock Dedicated Servers, optimized for busy 50+ player realms. Rebuilt against Endstone's Python API, **UtilityStone Reloaded** offers zero-lag movement handling, asynchronous disk I/O, custom resource-pack UI styling, in-game player administration, rank management, safe area protection, daily login rewards, and an optional two-way Discord relay.

---

## 📜 Fork Attribution & Vibe-Coding Notice

- **Original Project & Creator**: UtilityStone Reloaded is a **fork** of the original [UtilityStone](https://github.com/ozorical/UtilityStone) project created by **Ozz**. All original core concepts, initial architecture, and foundation are attributed to Ozz.
- **Fork Maintainer**: Maintained and expanded by **Tigger02** (`triggered02`).
- **Development Style**: This fork is **completely vibe-coded** — built, expanded, and maintained through AI-assisted and vibe-coded engineering workflows rather than traditional manual software writing.
- **Licensing & Copyright**: Released under the **MIT License**. Original copyright notices and licensing details are fully preserved.

---

## 💬 Community & Support

Need help setting up, found a bug, or want to discuss feature requests? Join our community on Discord:

👉 **[Join the UtilityStone Reloaded Discord Server](https://discord.gg/gHpgjRTCnu)** 👈

---

## 📋 Table of Contents

- [Requirements](#requirements)
- [Installation](#installation)
- [UI Architecture & Server Menu](#ui-architecture--server-menu)
- [Feature Overview](#feature-overview)
  - [Server Menu & Quick-Access Item](#server-menu--quick-access-item)
  - [Travel & Teleportation (TPA, Spawn, Back)](#travel--teleportation-tpa-spawn-back)
  - [Homes System](#homes-system)
  - [Warps System](#warps-system)
  - [Expanded Utilities](#expanded-utilities)
  - [Admin Panel & Player Inspector](#admin-panel--player-inspector)
  - [Editable Inventory & Ender Chest Management](#editable-inventory--ender-chest-management)
  - [Ranks & Permission Management](#ranks--permission-management)
  - [Safe Area Protection](#safe-area-protection)
  - [Daily Rewards System](#daily-rewards-system)
  - [Kits System](#kits-system)
  - [Player State & Moderation](#player-state--moderation)
  - [Messaging, Chat & Ignore System](#messaging-chat--ignore-system)
  - [Discord Two-Way Relay](#discord-two-way-relay)
  - [USTBridge Integration API](#ustbridge-integration-api)
- [Commands Reference](#commands-reference)
- [Permissions Reference](#permissions-reference)
- [Configuration Guide (`config.toml`)](#configuration-guide-configtoml)
- [Development & Testing](#development--testing)
- [License](#license)

---

## Requirements

- **Endstone**: 0.11 or newer (tested against Endstone 0.11.10, Bedrock Dedicated Server 1.26.45)
- **Python**: 3.10 or newer
- **Dependencies**: No third-party Python packages required. The optional Discord relay uses `aiohttp`, which ships bundled with Endstone.

---

## Installation

1. **Download or Build the Wheel**: Obtain `endstone_utilitystone-1.0.1-py3-none-any.whl` (or build it yourself using `python -m build --wheel`).
2. **Install the Plugin**:
   - Place `endstone_utilitystone-1.0.1-py3-none-any.whl` into your server's `plugins/` directory (or `pip install` it directly into your Endstone Python virtual environment).
3. **Install the Resource Pack**:
   - Copy `resource_pack/` (or package it as `UtilityStone.mcpack`) to `bedrock_server/resource_packs/UtilityStone/`.
   - Update your world's resource pack pin in `bedrock_server/worlds/<world_name>/world_resource_packs.json`:
     ```json
     [
       {
         "pack_id": "66983660-16d8-4d6d-8636-1c8657a66a6b",
         "version": [1, 0, 6]
       }
     ]
     ```
4. **Start the Server**: Launch Endstone. On first startup, UtilityStone creates `plugins/utilitystone/config.toml` and json storage files.
5. **Reloading**: Run `/utilitystone reload` in-game or from the console whenever configuration changes are made.

---

## UI Architecture & Server Menu

UtilityStone Reloaded features an **Obsidian Essentials-inspired UI suite** that runs seamlessly on Minecraft Bedrock:

- **Logic Ownership**: Python/Endstone owns all UI forms (`ActionForm`, `ModalForm`), callbacks, permissions, menu state, and business logic.
- **Visual Rendering**: The Bedrock Resource Pack detects UtilityStone's protocol marker (`§❖§U§S§T§D`) prepended to form titles via `server_form.json` and routes rendering to `utilitystone.json`. Buttons display nine-slice card backgrounds (`c_button`), pixel-art icons, hover/pressed visual states, and right-hand curved chevrons (`Arrow_Right_Curved`).
- **Navigation Architecture**:
  ```
  Server Menu (/menu)
  ├── Travel ───────────► Homes, Spawn, Travel Options ───► Back ──► Server Menu
  ├── Warps ────────────► Available Warps List ────────────► Back ──► Server Menu
  ├── Utilities ────────► Kits, Info, TPA, AFK, Rewards ──► Back ──► Server Menu
  ├── Admin Panel ──────► Player Inspector, Ranks, etc. ──► Back ──► Server Menu
  └── Back ─────────────► Closes Form
  ```
  Every submenu has an explicit `Back` button returning to `Server Menu`, while the `Back` button on `Server Menu` safely closes the form.

---

## Feature Overview

### Server Menu & Quick-Access Item
- **`/menu` Command**: Opens the central **Server Menu**. Compatible with `/usttest` alias.
- **Server Menu Item**: Configurable quick-access item (defaults to `minecraft:written_book` in slot 8, titled `"Server Menu"`).
  - Given automatically on join when enabled in `config.toml` (`[menuItem]`).
  - Players can claim the item anytime via `/menu item` (or `/menu getitem`).
  - Right-clicking the item in-game checks `utilitystone.command.menu` permission and opens `Server Menu`.

### Travel & Teleportation (TPA, Spawn, Back)
- **`/tpa <player>` & `/tpahere <player>`**: Send teleport or summon requests with configurable warmup delays, cooldown timers, request timeouts, and movement-cancellation checks.
- **`/tpaccept` & `/tpdeny` & `/tpcancel`**: Manage incoming and outgoing teleport requests.
- **`/spawn` & `/setspawn`**: Set and travel to the world spawn point. Optional `teleportOnFirstJoin` setting.
- **`/back`**: Returns to your previous teleport origin or death location. Remembers up to 5 positions per player.

### Homes System
- **`/sethome [name]`, `/home [name]`, `/delhome <name>`, `/homes`**: Save, travel to, delete, and list personal homes.
- **Home Limits**: Configurable default home limit (default: 3). Unlimited homes granted via `utilitystone.homes.unlimited` permission. Per-permission limits can be configured under `[homes.limits]`.

### Warps System
- **`/warp [name]`, `/warps`, `/setwarp <name>`, `/delwarp <name>`**: Public warp points created by admins and accessible via the `/warps` menu.
- **Per-Warp Permissions**: Optional `requirePerWarpPermission = true` setting requires `utilitystone.warp.<name>` to access specific warps.

### Expanded Utilities
The **Utilities** section under `/menu` aggregates player-facing utility tools:
- **Kits**: View and claim available kits.
- **Daily Reward**: View daily streak, time remaining, and claim login rewards.
- **Player Info**: View your health, location coordinates, gamemode, ping latency, total playtime, first/last seen timestamps, AFK status, and mute status.
- **Homes**: Quick access to your saved homes.
- **Teleport**: Quick access to TPA requests.
- **AFK**: Toggle AFK status directly from the UI.

### Admin Panel & Player Inspector
Admins with `utilitystone.admin.gui` permission access the **Admin Panel** (`/menu admin`), containing:
- **Player List / Inspector**: Inspect online players, view health, ping, coordinates, dimension, gamemode, first seen, rank, AFK status, and active mutes.
- **Player Management Actions**: Teleport To Player, Teleport Player To Me, View Homes, View Inventory, View Ender Chest, Heal, Feed, Fly Toggle, God Mode Toggle, Mute (30m/1h/24h), Unmute, and Assign Rank.
- **Admin Management Sections**: Homes, Warps, Spawn, Kits, Safe Areas, Ranks, Daily Rewards, Plugin Info, Reload Config, and Live Configuration Editor.

### Editable Inventory & Ender Chest Management
Full in-game item and container editing built into the Admin Player Inspector:
- **Permissions**:
  - View: `utilitystone.admin.players.inventory.view` / `utilitystone.admin.inventory.view`
  - Edit: `utilitystone.admin.players.inventory.edit` / `utilitystone.admin.inventory.edit` (default: `op`)
  - Ender Chest View: `utilitystone.admin.players.enderchest.view` / `utilitystone.admin.enderchest.view`
  - Ender Chest Edit: `utilitystone.admin.players.enderchest.edit` / `utilitystone.admin.enderchest.edit` (default: `op`)
- **Paginated Editor**: Displays 7 slots per page (`ITEMS_PER_PAGE`) with slot numbers, current item types, amounts, and pending edit tags.
- **Slot Modal Editor**: Clicking any slot opens a `ModalForm` exposing:
  - Item Identifier (e.g. `minecraft:diamond`, or `air` to clear)
  - Amount (0 to 64)
  - Data / Aux Value (integer)
- **Atomic Validation & Safety**:
  - Local edits stay in memory and **never** mutate the live container while being edited.
  - On **Save All Changes**, every slot is validated (`ItemStack` creation, item ID, amount, data range).
  - If any slot validation fails, the entire batch is aborted without partial updates.
  - Re-checks edit permissions and target player validity before applying.
  - Logs audit entry with admin name, target player, and changed slot count.

### Ranks & Permission Management
- **`/rank` Commands**: `list`, `info <rank>`, `create <rank>`, `delete <rank>`, `set <player> <rank>`, `remove <player>`, `player <target>`.
- **Rank Properties**: Priorities, display prefixes, display suffixes, inheritance nodes (`utilitystone.command.*`), and default rank assignment.
- **Chat Formatting**: Custom rank prefixes and suffixes integrate directly into public chat formatting (`{prefix}{name}{suffix}`).

### Safe Area Protection
- **`/safearea` Commands**: `set <name> <radius>`, `remove <name>`, `list`, `info <name>`, `enable <name>`, `disable <name>`. Alias `/sa`.
- **Protection**: Defines spherical/cuboid protected zones where player damage, block breaking, and pvp are restricted.
- **Bypass**: Granted via `utilitystone.safearea.bypass` permission or `utilitystone.admin` tag.

### Daily Rewards System
- **`/dailyreward` (`claim`, `status`)**: Player daily login streak tracking and reward claims.
- **Milestone Rewards**: Configurable reward commands executed when reaching specific streak thresholds (e.g. Day 1, Day 7, Day 30).
- **Admin Management**: Admins can view player streak details, reset streaks (`/dailyreward reset`), and manage milestone reward commands in-game.

### Kits System
- **`/kit [name]` & `/kits`**: Claim equipment/item kits configured in `config.toml`.
- **Features**: Support for item display names, lore, enchantments (`efficiency = 3`), cooldowns (`24h`), per-kit permissions (`utilitystone.kit.tools`), and automatic ground-dropping for overflow items.

### Player State & Moderation
- **State Commands**: `/heal`, `/feed`, `/fly`, `/god`, `/speed <0.1-10.0>`, `/repair` (item in main hand). All support `.others` permissions (e.g. `utilitystone.command.heal.others`).
- **Moderation Commands**: `/tempban <player> <duration|perm> [reason]`, `/mute <player> <duration> [reason]`, `/unmute <player>`.
- **Duration Parser**: Supports `30s`, `15m`, `2h`, `7d`, `3w`, `1mo`, `1y`, `1d12h`, `perm`, `forever`.

### Messaging, Chat & Ignore System
- **Private Messaging**: `/pm <player> <message>` (alias `/dm`), `/reply <message>` (alias `/r`).
- **Ignore System**: `/ignore <player>`, `/unignore <player>`, `/ignorelist`. Ignores public chat and private messages from blocked players.
- **Broadcasting**: `/broadcast <message>` (alias `/bc`).
- **Chat Management**: UtilityStone manages public chat formatting (`manageFormat = true`) to enforce ignore filtering and rank prefix formatting.

### Discord Two-Way Relay
Optional Discord bot integration shipping with no required external Python dependencies (uses `aiohttp` bundled with Endstone):
- **Features**: 2-way chat relay, death message relay, join/leave notices, server start/stop notifications.
- **Security & Efficiency**: Async websocket gateway (`gateway.discord.gg`), REST API v10, bounded thread-safe queues, batched message sending (rate-limit friendly), message truncation, and stripped `@everyone` / `@here` mentions.
- **Configuration**: Store bot token and channel ID in `plugins/utilitystone/.env` (`DISCORD_BOT_TOKEN` & `DISCORD_CHANNEL_ID`).

### USTBridge Integration API
Public integration surface exposed for diagnostic and third-party Endstone plugins (`endstone_ust_bridge_test`):
- **Class**: `endstone_utilitystone.integrations.USTBridgeIntegration`
- **Resolution**: `USTBridgeIntegration.from_plugin_manager(server.plugin_manager)`
- **Entry point**: `integration.open_test_form(player)` opens a real UtilityStone ActionForm through UtilityStone's UI pipeline.
- **Diagnostic Commands**: `/usttest` (opens Server Menu), `/ustdiag` (standalone diagnostic form).

---

## Commands Reference

| Command | Syntax | Permission Node | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| **`/menu`** | `/menu [action]` | `utilitystone.command.menu` | Everyone | Opens the Server Menu (aliases: `/usttest`, `/menu item`). |
| **`/sethome`** | `/sethome [name]` | `utilitystone.command.sethome` | Everyone | Saves a home at your current location. |
| **`/home`** | `/home [name]` | `utilitystone.command.home` | Everyone | Teleports to a saved home. |
| **`/delhome`** | `/delhome <name>` | `utilitystone.command.delhome` | Everyone | Deletes a saved home. |
| **`/homes`** | `/homes` | `utilitystone.command.homes` | Everyone | Lists your saved homes and limits. |
| **`/warp`** | `/warp [name]` | `utilitystone.command.warp` | Everyone | Teleports to a warp or lists warps. |
| **`/warps`** | `/warps` | `utilitystone.command.warps` | Everyone | Lists accessible warps. |
| **`/setwarp`** | `/setwarp <name>` | `utilitystone.command.setwarp` | Operator | Creates or updates a warp location. |
| **`/delwarp`** | `/delwarp <name>` | `utilitystone.command.delwarp` | Operator | Deletes a warp. |
| **`/spawn`** | `/spawn` | `utilitystone.command.spawn` | Everyone | Teleports to the spawn point. |
| **`/setspawn`** | `/setspawn` | `utilitystone.command.setspawn` | Operator | Sets the server spawn point. |
| **`/tpa`** | `/tpa <player>` | `utilitystone.command.tpa` | Everyone | Sends a teleport request to a player. |
| **`/tpahere`** | `/tpahere <player>` | `utilitystone.command.tpahere` | Everyone | Requests a player to teleport to you. |
| **`/tpaccept`** | `/tpaccept [player]` | `utilitystone.command.tpaccept` | Everyone | Accepts a teleport request (alias `/tpyes`). |
| **`/tpdeny`** | `/tpdeny [player]` | `utilitystone.command.tpdeny` | Everyone | Denies a teleport request (alias `/tpno`). |
| **`/tpcancel`** | `/tpcancel` | `utilitystone.command.tpcancel` | Everyone | Cancels your outgoing teleport request. |
| **`/back`** | `/back` | `utilitystone.command.back` | Everyone | Teleports to your previous location or death spot. |
| **`/heal`** | `/heal [player]` | `utilitystone.command.heal` | Operator | Restores health (others: `.heal.others`). |
| **`/feed`** | `/feed [player]` | `utilitystone.command.feed` | Operator | Restores hunger (others: `.feed.others`). |
| **`/fly`** | `/fly [player]` | `utilitystone.command.fly` | Operator | Toggles flight (others: `.fly.others`). |
| **`/god`** | `/god [player]` | `utilitystone.command.god` | Operator | Toggles invulnerability (others: `.god.others`). |
| **`/speed`** | `/speed <val> [player]`| `utilitystone.command.speed` | Operator | Sets walk/fly speed (0.1–10.0) (others: `.speed.others`). |
| **`/repair`** | `/repair` | `utilitystone.command.repair` | Operator | Repairs the item held in your main hand. |
| **`/pm`** | `/pm <player> <msg>` | `utilitystone.command.pm` | Everyone | Sends a private message (alias `/dm`). |
| **`/reply`** | `/reply <msg>` | `utilitystone.command.reply` | Everyone | Replies to the last private message (alias `/r`). |
| **`/ignore`** | `/ignore <player>` | `utilitystone.command.ignore` | Everyone | Blocks chat and PMs from a player. |
| **`/unignore`** | `/unignore <player>`| `utilitystone.command.unignore` | Everyone | Unblocks a player. |
| **`/ignorelist`**| `/ignorelist` | `utilitystone.command.ignorelist`| Everyone | Lists players you are currently ignoring. |
| **`/broadcast`** | `/broadcast <msg>` | `utilitystone.command.broadcast`| Operator | Broadcasts an announcement to the server (alias `/bc`). |
| **`/tempban`** | `/tempban <p> <t> [r]`| `utilitystone.command.tempban` | Operator | Temporarily or permanently bans a player. |
| **`/mute`** | `/mute <p> <t> [r]` | `utilitystone.command.mute` | Operator | Mutes a player for a set duration. |
| **`/unmute`** | `/unmute <player>` | `utilitystone.command.unmute` | Operator | Unmutes a player. |
| **`/kit`** | `/kit [name]` | `utilitystone.command.kit` | Everyone | Claims a kit or lists available kits. |
| **`/kits`** | `/kits` | `utilitystone.command.kits` | Everyone | Lists available kits. |
| **`/who`** | `/who` | `utilitystone.command.who` | Everyone | Lists online players and AFK status (alias `/online`). |
| **`/ping`** | `/ping [player]` | `utilitystone.command.ping` | Everyone | Displays connection latency (others: `.ping.others`). |
| **`/playtime`** | `/playtime [player]` | `utilitystone.command.playtime` | Everyone | Shows total playtime (others: `.playtime.others`). |
| **`/seen`** | `/seen <player>` | `utilitystone.command.seen` | Everyone | Shows when a player was last online. |
| **`/whois`** | `/whois <player>` | `utilitystone.command.whois` | Everyone | Displays detailed info on an online player. |
| **`/afk`** | `/afk [reason]` | `utilitystone.command.afk` | Everyone | Toggles AFK status with an optional reason. |
| **`/safearea`** | `/safearea <subcmd>`| `utilitystone.command.safearea`| Everyone | Manage safe areas (alias `/sa`). |
| **`/rank`** | `/rank <subcmd>` | `utilitystone.admin.ranks.view`| Operator | Manage ranks, priorities, and assignments. |
| **`/dailyreward`**| `/dailyreward [cmd]`| `utilitystone.command.dailyreward`| Everyone | Claim daily reward or check streak status. |
| **`/utilitystone`**| `/utilitystone [cmd]`| `utilitystone.command.utilitystone`| Operator | Reload config or show status (alias `/ustone`). |

---

## Permissions Reference

| Permission Node | Description | Default Level |
| :--- | :--- | :--- |
| `utilitystone.command.menu` | Access `/menu` and the Server Menu item | Everyone (`true`) |
| `utilitystone.command.sethome` | Save personal homes | Everyone (`true`) |
| `utilitystone.command.home` | Teleport to personal homes | Everyone (`true`) |
| `utilitystone.command.delhome` | Delete personal homes | Everyone (`true`) |
| `utilitystone.command.homes` | List personal homes | Everyone (`true`) |
| `utilitystone.command.warp` | Use warps | Everyone (`true`) |
| `utilitystone.command.warps` | List accessible warps | Everyone (`true`) |
| `utilitystone.command.setwarp` | Create or update warps | Operator (`op`) |
| `utilitystone.command.delwarp` | Delete warps | Operator (`op`) |
| `utilitystone.command.spawn` | Teleport to server spawn | Everyone (`true`) |
| `utilitystone.command.setspawn` | Set server spawn point | Operator (`op`) |
| `utilitystone.command.tpa` | Send TPA requests | Everyone (`true`) |
| `utilitystone.command.tpahere` | Send TPAHERE requests | Everyone (`true`) |
| `utilitystone.command.tpaccept` | Accept TPA requests | Everyone (`true`) |
| `utilitystone.command.tpdeny` | Deny TPA requests | Everyone (`true`) |
| `utilitystone.command.tpcancel` | Cancel TPA requests | Everyone (`true`) |
| `utilitystone.command.back` | Return to previous/death location | Everyone (`true`) |
| `utilitystone.command.heal` | Heal self | Operator (`op`) |
| `utilitystone.command.heal.others` | Heal other players | Operator (`op`) |
| `utilitystone.command.feed` | Feed self | Operator (`op`) |
| `utilitystone.command.feed.others` | Feed other players | Operator (`op`) |
| `utilitystone.command.fly` | Toggle flight for self | Operator (`op`) |
| `utilitystone.command.fly.others` | Toggle flight for others | Operator (`op`) |
| `utilitystone.command.god` | Toggle god mode for self | Operator (`op`) |
| `utilitystone.command.god.others` | Toggle god mode for others | Operator (`op`) |
| `utilitystone.command.speed` | Change movement speed | Operator (`op`) |
| `utilitystone.command.speed.others` | Change speed for others | Operator (`op`) |
| `utilitystone.command.repair` | Repair held item | Operator (`op`) |
| `utilitystone.command.pm` | Send private messages | Everyone (`true`) |
| `utilitystone.command.reply` | Reply to private messages | Everyone (`true`) |
| `utilitystone.command.ignore` | Ignore players | Everyone (`true`) |
| `utilitystone.command.unignore` | Stop ignoring players | Everyone (`true`) |
| `utilitystone.command.ignorelist` | View ignore list | Everyone (`true`) |
| `utilitystone.command.broadcast` | Broadcast server announcements | Operator (`op`) |
| `utilitystone.command.tempban` | Temporarily ban players | Operator (`op`) |
| `utilitystone.command.mute` | Mute players | Operator (`op`) |
| `utilitystone.command.unmute` | Unmute players | Operator (`op`) |
| `utilitystone.command.kit` | Claim kits | Everyone (`true`) |
| `utilitystone.command.kits` | List kits | Everyone (`true`) |
| `utilitystone.command.who` | View online players | Everyone (`true`) |
| `utilitystone.command.ping` | View own ping | Everyone (`true`) |
| `utilitystone.command.ping.others` | View another player's ping | Operator (`op`) |
| `utilitystone.command.playtime` | View own playtime | Everyone (`true`) |
| `utilitystone.command.playtime.others`| View another player's playtime | Operator (`op`) |
| `utilitystone.command.seen` | View last seen timestamp | Everyone (`true`) |
| `utilitystone.command.whois` | Inspect online player details | Everyone (`true`) |
| `utilitystone.command.afk` | Toggle AFK status | Everyone (`true`) |
| `utilitystone.command.dailyreward` | Claim daily rewards | Everyone (`true`) |
| `utilitystone.command.safearea` | View/use safearea info | Everyone (`true`) |
| `utilitystone.command.safearea.set` | Create/edit safe areas | Operator (`op`) |
| `utilitystone.command.safearea.remove`| Delete safe areas | Operator (`op`) |
| `utilitystone.command.utilitystone`| Reload/manage plugin | Operator (`op`) |
| `utilitystone.admin.gui` | Access the Admin Panel | Operator (`op`) |
| `utilitystone.admin.players.inspect`| Inspect players in Admin Panel | Operator (`op`) |
| `utilitystone.admin.homes.view` | View other players' homes | Operator (`op`) |
| `utilitystone.admin.homes.teleport`| Teleport to other players' homes | Operator (`op`) |
| `utilitystone.admin.homes.delete` | Delete other players' homes | Operator (`op`) |
| `utilitystone.admin.inventory.view`| View player inventories | Operator (`op`) |
| `utilitystone.admin.inventory.edit`| Edit player inventories | Operator (`op`) |
| `utilitystone.admin.players.inventory.view` | View player inventories (alias) | Operator (`op`) |
| `utilitystone.admin.players.inventory.edit` | Edit player inventories (alias) | Operator (`op`) |
| `utilitystone.admin.enderchest.view` | View player ender chests | Operator (`op`) |
| `utilitystone.admin.enderchest.edit` | Edit player ender chests | Operator (`op`) |
| `utilitystone.admin.players.enderchest.view` | View player ender chests (alias) | Operator (`op`) |
| `utilitystone.admin.players.enderchest.edit` | Edit player ender chests (alias) | Operator (`op`) |
| `utilitystone.admin.ranks.view` | View rank configurations | Operator (`op`) |
| `utilitystone.admin.ranks.create` | Create new ranks | Operator (`op`) |
| `utilitystone.admin.ranks.edit` | Edit rank properties | Operator (`op`) |
| `utilitystone.admin.ranks.delete` | Delete ranks | Operator (`op`) |
| `utilitystone.admin.ranks.assign` | Assign ranks to players | Operator (`op`) |
| `utilitystone.admin.dailyrewards.view` | View player daily reward details | Operator (`op`) |
| `utilitystone.admin.dailyrewards.reset` | Reset player daily reward streaks | Operator (`op`) |
| `utilitystone.admin.dailyrewards.manage`| Manage reward milestone commands | Operator (`op`) |
| `utilitystone.safearea.bypass` | Bypass safe area protection | Operator (`op`) |
| `utilitystone.homes.unlimited` | Save unlimited homes | Operator (`op`) |
| `utilitystone.teleport.instant` | Skip teleport warmup delay | Operator (`op`) |
| `utilitystone.teleport.nocooldown` | Skip teleport cooldown timer | Operator (`op`) |
| `utilitystone.chat.color` | Use `&` color codes in chat | Operator (`op`) |
| `utilitystone.kit.tools` | Access example `tools` kit | Operator (`op`) |

---

## Configuration Guide (`config.toml`)

Configuration is auto-generated on first load at `plugins/utilitystone/config.toml`. Run `/utilitystone reload` to apply updates in real time.

```toml
[storage]
saveIntervalSeconds = 30     # Flush dirty data interval (5–900s)
playtimeSyncSeconds = 120    # Write playtime totals interval

[messages]
usePrefix = true             # Enable plugin prefix in chat replies
prefix = "&8[&bUtilityStone&8]&r "

[homes]
defaultLimit = 3            # Default homes per player
[homes.limits]
"utilitystone.homes.vip" = 8
"utilitystone.homes.staff" = 20

[warps]
requirePerWarpPermission = false # Enforce utilitystone.warp.<name> per warp

[spawn]
teleportOnFirstJoin = false  # Teleport new players to spawn on first join

[teleport]
warmupSeconds = 3            # Warmup delay before teleporting
cooldownSeconds = 5          # Cooldown between teleports
requestTimeoutSeconds = 60   # TPA request expiration
cancelOnMove = true          # Cancel warmup if player moves
moveTolerance = 0.75         # Allowed movement distance during warmup (blocks)
pollTicks = 10               # Warmup/request check interval
rememberDeathLocation = true # Enable /back to death spot
historySize = 5              # Max /back history entries per player

[chat]
manageFormat = true          # Enable chat formatting & ignore filtering
format = "<{name}> {message}"# Default chat format ({prefix}, {suffix}, {name}, {message})
afkTag = "&7[AFK] &r"        # Chat prefix for AFK players

[afk]
enabled = true               # Auto-AFK detection
timeoutSeconds = 300         # Idle seconds before auto-AFK
sampleSeconds = 5            # Position sampling interval
announce = true              # Announce AFK state changes in chat

[connection]
joinMessage = ""             # Custom join message ({name}). Empty = vanilla default
quitMessage = ""             # Custom quit message
welcomeMessage = ""          # Private message sent to joining player

[menuItem]
enabled = true               # Enable quick-access Server Menu item on join
itemType = "minecraft:written_book"
name = "Server Menu"
lore = "Right-click to open the menu"
slot = 8                     # Hotbar slot (0–35)

[safeareas]
enabled = true               # Safe area protection engine
scanIntervalSeconds = 5      # Location scan frequency
minRadius = 1                # Minimum radius
maxRadius = 10000            # Maximum radius
bypassPermission = "utilitystone.safearea.bypass"
bypassTag = "utilitystone.admin"

[dailyRewards]
enabled = true               # Daily login rewards engine
[dailyRewards.rewards]       # Streak milestone commands
1 = ["give {player} minecraft:bread 16"]
7 = ["give {player} minecraft:diamond 5"]
30 = ["give {player} minecraft:netherite_ingot 1"]

[kits.starter]
cooldown = "24h"
items = [
    { type = "minecraft:stone_sword", amount = 1 },
    { type = "minecraft:bread", amount = 16 }
]

[discord]
enabled = true               # Enable Discord relay module
relayChat = true             # Relay player chat
relayDeaths = true           # Relay death messages
relayJoinLeave = true        # Relay join/leave events
relayServerState = true      # Relay start/stop notices
sendIntervalSeconds = 1.5    # Queue post interval (batched)
inboundPollTicks = 10        # Inbound poll interval
maxInboundLength = 256       # Max inbound message length
chatFormat = "**{name}**: {message}"
eventFormat = "_{message}_"
inboundFormat = "&9[Discord] &b{name}&7: &f{message}"
```

---

## Development & Testing

### Project Layout

```
utilitystone-clean/
├── pyproject.toml
├── LICENSE
├── README.md
├── CHANGELOG.md
├── resource_pack/
│   ├── manifest.json
│   ├── textures/
│   │   ├── icons/            # 12 pixel-art menu icons
│   │   └── ui/               # Nine-slice cards, buttons, backgrounds
│   └── ui/
│       ├── utilitystone.json # Custom protocol renderer
│       ├── server_form.json  # Factory marker router
│       └── forms/community.json
├── src/endstone_utilitystone/
│   ├── __init__.py
│   ├── plugin.py             # Main plugin class, commands & permissions
│   ├── config.toml           # Default configuration
│   ├── core/                 # Sessions, router, storage, settings, messages
│   ├── services/             # Homes, warps, spawns, teleports, kits, afk, ranks, safeareas, daily rewards
│   ├── commands/             # Command group implementations
│   ├── listeners/            # Chat, connection, protection, safearea, menu_item
│   ├── ui/                   # Player menu, admin menu, inspector, rank menu, config editor
│   ├── integrations/         # USTBridge API & Discord relay (gateway, rest, bridge)
│   └── util/                 # Durations, locations, text, player actions
└── tests/                    # 700+ regression & unit test suite
```

### Running Tests & Code Validation

- **Run Pytest Suite**:
  ```bash
  python3 -m pytest tests/ -q
  ```
- **Bytecode Compilation Check**:
  ```bash
  python3 -m compileall -q src
  ```
- **Validate Resource Pack JSON**:
  ```bash
  find resource_pack -name '*.json' -print0 | xargs -0 -n1 jq empty
  ```
- **Git Diff & Whitespace Check**:
  ```bash
  git diff --check
  ```
- **Build Production Wheel**:
  ```bash
  python3 -m build --wheel
  ```

---

## License

UtilityStone Reloaded is released under the **MIT License**. See [LICENSE](LICENSE) for details.

*Original UtilityStone created by Ozz.*
*UtilityStone Reloaded maintained by Tigger02.*
