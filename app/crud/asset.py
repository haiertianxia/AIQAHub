from app.crud.base import Repository
from app.models.asset import Asset


class AssetRepository(Repository[Asset]):
    def __init__(self) -> None:
        super().__init__(Asset)
