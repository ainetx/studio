from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def test_update_forwards_migration_flags_and_project_root(monkeypatch):
    from studio_proxy import cli
    import studio_proxy.cache as cache
    import studio_proxy.telemetry as telemetry

    captured = {}

    def fake_download_and_cache(*, version=None, force=False, url=None):
        captured["cache"] = {"version": version, "force": force, "url": url}
        return True, "cached"

    def fake_forward(skill_path, args):
        captured["forward"] = {"skill_path": skill_path, "args": list(args)}
        return 0

    monkeypatch.setattr(cache, "download_and_cache", fake_download_and_cache)
    monkeypatch.setattr(telemetry, "track_invocation", lambda _args: None)
    monkeypatch.setattr(cli, "find_cached_skill", lambda: Path("/tmp/studio.py"))
    monkeypatch.setattr(cli, "_forward_to_skill", fake_forward)

    rc = cli.main([
        "update",
        "--project-root",
        "/repo",
        "--migrate-from-cypilot=yes",
        "--from-dir",
        "cypilot",
        "--update-legacy-studio=yes",
        "--yes",
    ])

    assert rc == 0
    assert captured["cache"]["version"] is None
    assert captured["forward"]["args"] == [
        "update",
        "--project-root",
        "/repo",
        "--migrate-from-cypilot=yes",
        "--from-dir",
        "cypilot",
        "--update-legacy-studio=yes",
        "--yes",
    ]


def test_update_strips_only_positional_cache_version(monkeypatch):
    from studio_proxy import cli
    import studio_proxy.cache as cache
    import studio_proxy.telemetry as telemetry

    captured = {}

    def fake_download_and_cache(*, version=None, force=False, url=None):
        captured["cache"] = {"version": version, "force": force, "url": url}
        return True, "cached"

    def fake_forward(_skill_path, args):
        captured["forward_args"] = list(args)
        return 0

    monkeypatch.setattr(cache, "download_and_cache", fake_download_and_cache)
    monkeypatch.setattr(telemetry, "track_invocation", lambda _args: None)
    monkeypatch.setattr(cli, "find_cached_skill", lambda: Path("/tmp/studio.py"))
    monkeypatch.setattr(cli, "_forward_to_skill", fake_forward)

    rc = cli.main(["update", "v1.2.3", "--project-root", "/repo", "--yes"])

    assert rc == 0
    assert captured["cache"]["version"] == "v1.2.3"
    assert captured["forward_args"] == ["update", "--project-root", "/repo", "--yes"]
