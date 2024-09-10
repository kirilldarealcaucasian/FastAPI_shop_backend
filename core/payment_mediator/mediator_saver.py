

class InstanceMediatorSaver:
    """Saves instance of the mediator in each mediator component"""
    def __init__(self, mediator=None):
        self._mediator = mediator

    @property
    def mediator(self):
        return self._mediator

    @mediator.setter
    def mediator(self, val) -> None:
        self._mediator = val