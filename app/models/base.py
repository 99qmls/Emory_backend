# 基础类
from sqlalchemy import DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from datetime import datetime

class Base(DeclarativeBase):
    """
    继承基础模型
    """
    pass

class TimestampMixin:
    """
    创建，更新时间字段
    """
    created_at: Mapped[datetime] = mapped_column(DateTime,default=datetime.utcnow())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class SoftDeleteMixin:
    """
    删除类
    """
    deleted_at: Mapped[datetime]= mapped_column(DateTime,nullable=True)

class BaseModel(Base,TimestampMixin):
    """
    混合基类
    """
    __abstract__ = True
