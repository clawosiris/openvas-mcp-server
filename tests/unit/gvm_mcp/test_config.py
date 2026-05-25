from gvm_mcp.config import ConnectionStyle, load_config


def test_load_config_from_env_local(monkeypatch) -> None:
    monkeypatch.setenv("GVM_STYLE", "local")
    monkeypatch.setenv("GVM_SOCKET_PATH", "/tmp/gvmd.sock")
    monkeypatch.setenv("GVM_USERNAME", "admin")
    monkeypatch.setenv("GVM_PASSWORD", "secret")

    cfg = load_config()

    assert cfg.style == ConnectionStyle.LOCAL
    assert cfg.socket_path == "/tmp/gvmd.sock"
    assert cfg.username == "admin"
    assert cfg.password == "secret"


def test_load_config_requires_credentials(monkeypatch) -> None:
    monkeypatch.delenv("GVM_USERNAME", raising=False)
    monkeypatch.delenv("GVM_PASSWORD", raising=False)
    monkeypatch.setenv("GVM_STYLE", "local")

    try:
        load_config()
        raise AssertionError("Expected ValueError")
    except ValueError:
        pass
