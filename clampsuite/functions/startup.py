from pathlib import Path


def startup_function():
    p = Path.home()
    h = "ClampSuite"
    file_name = "Preferences.yaml"

    if Path(p / h).exists():
        if Path(p / h / file_name).exists():
            pass
            # pref_dict = YamlWorker.load_yaml(p / h / file_name)
        else:
            pass
    else:
        prog_dir = Path(p / h)
        prog_dir.mkdir()
