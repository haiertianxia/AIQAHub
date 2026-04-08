from app.crud.base import Repository
from app.models.suite import TestSuite


class SuiteRepository(Repository[TestSuite]):
    def __init__(self) -> None:
        super().__init__(TestSuite)

