from abc import ABC, abstractmethod
from app.domain.models import CodeSubmission, Finding



# Creating an Abstract Class of Unfinished Parts

class Analyzer(ABC):
    name: str = "base"

    @abstractmethod
    def analyze(self,submission: CodeSubmission) -> list[Finding]:
        raise NotImplementedError

   