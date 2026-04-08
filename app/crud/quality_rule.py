from app.crud.base import Repository
from app.models.quality_rule import QualityRule


class QualityRuleRepository(Repository[QualityRule]):
    def __init__(self) -> None:
        super().__init__(QualityRule)
