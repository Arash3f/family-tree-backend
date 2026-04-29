from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from app.core.config import setting

engine = create_async_engine(
    setting.database_url_asy,
    echo=False,
)

async_session = async_sessionmaker(
    engine,
    expire_on_commit=False,
)
