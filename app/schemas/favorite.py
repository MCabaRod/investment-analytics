from pydantic import BaseModel, ConfigDict

from app.schemas.asset import AssetRead


class FavoriteCreate(BaseModel):
    asset_id: int


class FavoriteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    asset: AssetRead
