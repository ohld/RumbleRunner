from sqlalchemy import Column, Integer, Float, String, ForeignKey
from sqlalchemy.orm import relationship

from app.public.models import BaseDBModel


class Player(BaseDBModel):
    __tablename__ = 'player'

    id = Column(Integer, autoincrement=True, primary_key=True)

    name = Column(String, unique=True, nullable=False)
    mu = Column(Float, nullable=False, default=0.0)
    sigma = Column(Float, nullable=False, default=0.0)

    game_session_id = Column(ForeignKey('game_session.id'), nullable=True)
    game_session = relationship("GameSession")
