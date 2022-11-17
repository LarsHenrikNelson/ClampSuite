def startupFunction():
    p = Path.home()
    h = "EphysAnalysisProgram"
    file_name = "Preferences.yaml"

    if Path(p / h).exists():
        if Path(p / h / file_name).exists():
            pref_dict = YamlWorker.load_yaml(p / h / file_name)
        else:
            pass
    else:
        Path(p / h).mkdir()
