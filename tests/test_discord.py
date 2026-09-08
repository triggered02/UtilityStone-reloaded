import os
from pathlib import Path
from endstone_utilitystone.integrations.discord.env import parseEnvText, readEnvFile, loadEnvironment
from endstone_utilitystone.integrations.discord.bridge import DiscordBridge, STATE_DISABLED, STATE_UNCONFIGURED


def test_parse_env_text():
    text = """
    # Comment line
    DISCORD_BOT_TOKEN=sample_token_123 # inline comment
    DISCORD_CHANNEL_ID="123456789012345678"
    export UNUSED_VAR='hello'
    """
    data = parseEnvText(text)
    assert data["DISCORD_BOT_TOKEN"] == "sample_token_123"
    assert data["DISCORD_CHANNEL_ID"] == "123456789012345678"
    assert data["UNUSED_VAR"] == "hello"


def test_read_env_file(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("DISCORD_BOT_TOKEN=token_abc\nDISCORD_CHANNEL_ID=987654321\n", encoding="utf-8")

    data = readEnvFile(env_file)
    assert data["DISCORD_BOT_TOKEN"] == "token_abc"
    assert data["DISCORD_CHANNEL_ID"] == "987654321"

    non_existent = tmp_path / "non_existent.env"
    assert readEnvFile(non_existent) == {}


def test_load_environment_fallback(tmp_path, monkeypatch):
    monkeypatch.delenv("DISCORD_BOT_TOKEN", raising=False)
    monkeypatch.delenv("DISCORD_CHANNEL_ID", raising=False)

    plugin_env = tmp_path / "plugin" / ".env"
    plugin_env.parent.mkdir(parents=True, exist_ok=True)
    plugin_env.write_text("DISCORD_BOT_TOKEN=token_from_plugin\nDISCORD_CHANNEL_ID=1111\n", encoding="utf-8")

    cwd_env = tmp_path / "cwd" / ".env"
    cwd_env.parent.mkdir(parents=True, exist_ok=True)
    cwd_env.write_text("DISCORD_BOT_TOKEN=token_from_cwd\nDISCORD_CHANNEL_ID=2222\n", encoding="utf-8")

    res = loadEnvironment([plugin_env, cwd_env])
    assert res["DISCORD_BOT_TOKEN"] == "token_from_plugin"
    assert res["DISCORD_CHANNEL_ID"] == "1111"


def test_load_environment_os_override(tmp_path, monkeypatch):
    monkeypatch.setenv("DISCORD_BOT_TOKEN", "override_token")
    monkeypatch.setenv("DISCORD_CHANNEL_ID", "9999")

    plugin_env = tmp_path / ".env"
    plugin_env.write_text("DISCORD_BOT_TOKEN=file_token\nDISCORD_CHANNEL_ID=1111\n", encoding="utf-8")

    res = loadEnvironment([plugin_env])
    assert res["DISCORD_BOT_TOKEN"] == "override_token"
    assert res["DISCORD_CHANNEL_ID"] == "9999"


class DummySettings:
    discordEnabled = True


class DummyPlugin:
    def __init__(self, data_folder):
        self.data_folder = data_folder
        self.settings = DummySettings()
        self.logger = self

    def warning(self, msg):
        pass


def test_discord_bridge_env_paths(tmp_path):
    plugin = DummyPlugin(data_folder=str(tmp_path / "plugin_data"))
    bridge = DiscordBridge(plugin)
    paths = bridge.envPaths()
    assert Path(tmp_path / "plugin_data" / ".env") in paths
    assert Path.cwd() / ".env" in paths


def test_discord_bridge_unconfigured(tmp_path, monkeypatch):
    monkeypatch.delenv("DISCORD_BOT_TOKEN", raising=False)
    monkeypatch.delenv("DISCORD_CHANNEL_ID", raising=False)

    plugin = DummyPlugin(data_folder=str(tmp_path))
    bridge = DiscordBridge(plugin)
    state = bridge.configure()
    assert state == STATE_UNCONFIGURED
