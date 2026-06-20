import pytest
from pingcastle_mcp.config import Config, load_config
from pingcastle_mcp.errors import ConfigError


class FakeStore:
    def __init__(self, key=None):
        self._key = key

    def get_api_key(self):
        return self._key


def test_env_takes_precedence():
    env = {
        "PINGCASTLE_ENTERPRISE_URL": "https://env.example",
        "PINGCASTLE_API_KEY": "envkey",
        "PINGCASTLE_INSECURE_TLS": "1",
    }
    cfg = load_config(env=env, store=FakeStore(key="storekey"))
    assert cfg.enterprise_url == "https://env.example"
    assert cfg.api_key == "envkey"
    assert cfg.insecure_tls is True
    assert cfg.login_location == "pingcastle-mcp"


def test_missing_key_raises(monkeypatch):
    monkeypatch.setattr("pingcastle_mcp.config.read_saved_url", lambda: None)
    with pytest.raises(ConfigError):
        load_config(env={}, store=FakeStore(key=None))


def test_falls_back_to_store_and_saved_url(monkeypatch):
    monkeypatch.setattr("pingcastle_mcp.config.read_saved_url", lambda: "https://saved.example")
    cfg = load_config(env={}, store=FakeStore(key="storekey"))
    assert cfg.enterprise_url == "https://saved.example"
    assert cfg.api_key == "storekey"


def test_env_url_beats_saved_url(monkeypatch):
    monkeypatch.setattr("pingcastle_mcp.config.read_saved_url", lambda: "https://saved.example")
    cfg = load_config(
        env={"PINGCASTLE_ENTERPRISE_URL": "https://env.example", "PINGCASTLE_API_KEY": "k"},
        store=FakeStore(key="storekey"),
    )
    assert cfg.enterprise_url == "https://env.example"


def test_enterprise_url_trailing_slash_stripped(monkeypatch):
    monkeypatch.setattr("pingcastle_mcp.config.read_saved_url", lambda: None)
    cfg = load_config(
        env={"PINGCASTLE_ENTERPRISE_URL": "https://pc.test/", "PINGCASTLE_API_KEY": "k"},
        store=FakeStore(),
    )
    assert cfg.enterprise_url == "https://pc.test"


@pytest.mark.parametrize("value,expected", [
    ("1", True), ("true", True), ("yes", True),
    ("0", False), ("false", False), ("no", False), ("", False),
])
def test_insecure_tls_parsing(monkeypatch, value, expected):
    monkeypatch.setattr("pingcastle_mcp.config.read_saved_url", lambda: None)
    cfg = load_config(
        env={"PINGCASTLE_ENTERPRISE_URL": "https://pc.test", "PINGCASTLE_API_KEY": "k",
             "PINGCASTLE_INSECURE_TLS": value},
        store=FakeStore(),
    )
    assert cfg.insecure_tls is expected


def test_save_url_escapes_and_roundtrips(monkeypatch, tmp_path):
    cfgfile = tmp_path / "config.toml"
    monkeypatch.setattr("pingcastle_mcp.config.CONFIG_PATH", cfgfile)
    from pingcastle_mcp.config import save_url, read_saved_url
    tricky = 'https://pc.test/a"b'
    save_url(tricky)
    assert read_saved_url() == tricky
