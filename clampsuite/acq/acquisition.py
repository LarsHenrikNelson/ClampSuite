
class Acquisition:
    def __init__(self, acquisition_data: dict):
        self.acquisition_data = acquisition_data
        self.analyses = []

    def add_analysis(self, analysis):
        self.analyses.append(analysis)
