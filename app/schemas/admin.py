from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class AdminAnalytics(BaseModel):
    on_date: date
    total_rooms: int
    occupied_rooms: int
    available_rooms: int
    pending_booking_count: int
    confirmed_booking_count: int
    cancelled_booking_count: int
    total_confirmed_revenue: Decimal
    revenue_booking_count: int
