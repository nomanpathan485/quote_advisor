from pydantic import BaseModel, ConfigDict, Field


class HotelOffer(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    name: str | None
    address: str | None
    price_display: str | None
    currency_symbol: str | None
    room_description: str | None
    room_description_truncated: bool | None
    date_display: str | None
    nights: int | None = Field(gt=0)
    meal_plan: str | None
    cancellation_wording: str | None


class Quote(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    hotels: list[HotelOffer] = Field(min_length=1)