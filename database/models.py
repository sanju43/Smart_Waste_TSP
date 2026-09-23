from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass

class Project(Base):
    __tablename__ = "projects"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    locations: Mapped[list["Location"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    routes: Mapped[list["Route"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    distance_matrices: Mapped[list["DistanceMatrix"]] = relationship(back_populates="project", cascade="all, delete-orphan")

class Location(Base):
    __tablename__ = "locations"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))
    name: Mapped[str] = mapped_column(String(100))
    type: Mapped[str] = mapped_column(String(30), default="Collection")
    x: Mapped[float] = mapped_column(Float)
    y: Mapped[float] = mapped_column(Float)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    waste_kg: Mapped[float] = mapped_column(Float, default=0)
    priority: Mapped[int] = mapped_column(Integer, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=lambda: datetime.now(timezone.utc))
    project: Mapped[Project] = relationship(back_populates="locations")

class Route(Base):
    __tablename__ = "routes"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))
    algorithm: Mapped[str] = mapped_column(String(50))
    start_location_id: Mapped[int] = mapped_column(Integer)
    total_distance: Mapped[float] = mapped_column(Float, default=0)
    estimated_minutes: Mapped[float] = mapped_column(Float, default=0)
    total_stops: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(30), default="completed")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    project: Mapped[Project] = relationship(back_populates="routes")
    points: Mapped[list["RoutePoint"]] = relationship(back_populates="route", cascade="all, delete-orphan")

class RoutePoint(Base):
    __tablename__ = "route_points"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    route_id: Mapped[int] = mapped_column(ForeignKey("routes.id"))
    location_id: Mapped[int] = mapped_column(Integer)
    sequence_no: Mapped[int] = mapped_column(Integer)
    distance_from_previous: Mapped[float] = mapped_column(Float, default=0)
    cumulative_distance: Mapped[float] = mapped_column(Float, default=0)
    route: Mapped[Route] = relationship(back_populates="points")

class DistanceMatrix(Base):
    __tablename__ = "distance_matrix"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))
    from_location_id: Mapped[int] = mapped_column(Integer)
    to_location_id: Mapped[int] = mapped_column(Integer)
    distance: Mapped[float] = mapped_column(Float)
    project: Mapped[Project] = relationship(back_populates="distance_matrices")

class DemoDataset(Base):
    __tablename__ = "demo_datasets"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    payload: Mapped[str] = mapped_column(Text)

class Setting(Base):
    __tablename__ = "settings"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    key: Mapped[str] = mapped_column(String(100), unique=True)
    value: Mapped[str] = mapped_column(Text)
