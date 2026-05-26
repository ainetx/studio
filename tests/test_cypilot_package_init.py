from unittest.mock import patch


def test_package_main_is_lazy_import_wrapper():
    # Ensure skills.studio.scripts.studio.main calls through to cli.main
    # without importing cli at package import time.
    from skills.studio.scripts import studio

    with patch("skills.studio.scripts.studio.cli.main", return_value=0) as m:
        assert studio.main(["validate", "--skip-code"]) == 0
        m.assert_called_once()
