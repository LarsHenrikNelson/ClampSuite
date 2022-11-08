class FinalAnalysis:
    """
    This class is used to create any acquisition object type.
    The classes are stored in _class_type and are automatically
    created by passing the analysis method and a file path. All
    the rest of the attributes for the object are created when
    the
    """

    _class_type = {}

    def __init_subclass__(cls, analysis, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._class_type[analysis] = cls

    def __new__(cls, analysis: str, *args):
        subclass = cls._class_type[analysis]
        obj = object.__new__(subclass)
        obj.analysis = analysis
        obj.version = "0.0.2"
        return obj

    def save_data(self):
        raise NotImplementedError

    def load_data(self):
        raise NotImplementedError
