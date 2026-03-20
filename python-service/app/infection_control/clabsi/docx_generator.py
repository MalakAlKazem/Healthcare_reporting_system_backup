from app.infection_control.ic_docx_generator import InfectionControlDocxGenerator as _Gen


class CLABSIDocxGenerator:
    def __init__(self):
        self._gen = _Gen('clabsi')

    def generate_report(self, history: list, targets: dict, current: dict = None) -> dict:
        return self._gen.generate_report(history=history, targets=targets, current=current)
