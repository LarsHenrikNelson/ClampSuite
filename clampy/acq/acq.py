import copy


class Acq:
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

    def __new__(cls, analysis: str, path: str, *args):
        subclass = cls._class_type[analysis]
        obj = object.__new__(subclass)
        obj.analysis = analysis
        obj.path = path
        obj.version = "0.0.1"
        return obj

    def __copy__(self):
        return self

    def __deepcopy__(self, memo):
        """
        Seems to work. Needs more testing. __deepcopy__ needs to work if
        someone wants to pickle a file.
        """
        new_acq = Acq(
            copy.deepcopy(self.analysis, memo), copy.deepcopy(self.path, memo)
        )
        new_acq.__dict__.update(copy.deepcopy(self.__dict__, memo))
        return new_acq

    def __repr__(self):
        return f"({self.analysis}, {self.name})"

    def deep_copy(self):
        new_acq = Acq(copy.deepcopy(self.analysis), copy.deepcopy(self.path))
        new_acq.__dict__.update(copy.deepcopy(self.__dict__))
        return new_acq
