from .acq import Acq


class AcqManager:
    """
    This class creates new acquisition objects and final analysis objects.
    It is a convience class to keep all the data for an analysis session
    organized. This class also makes it easier to deal with ephys files that
    contain several arrays and files that contain only a single array that need
    to be analyzed since each array needs to be analyzed separately.
    """

    def __init__(self, analysis):
        self.analysis = analysis
        self.acq_dict = {}

    def load_file(self):
        path_obj = PurePath(self.path)
        if path_obj.suffix == ".mat":
            acq_components = load_scanimage_file(path_obj)
        elif path_obj.suffix == ".json":
            with open(path) as file:
                data = json.load(file)
        else:
            print("File type not recognized!")
