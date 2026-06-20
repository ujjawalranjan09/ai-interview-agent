"""Feature flag service."""
from typing import List, Optional, Dict, Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.feature_flag import FeatureFlag


async def get_all_flags(db: AsyncSession) -> List[FeatureFlag]:
    result = await db.execute(select(FeatureFlag).order_by(FeatureFlag.key))
    return list(result.scalars().all())


async def get_flag(db: AsyncSession, key: str) -> Optional[FeatureFlag]:
    result = await db.execute(
        select(FeatureFlag).where(FeatureFlag.key == key)
    )
    return result.scalar_one_or_none()


async def is_enabled(
    db: AsyncSession,
    key: str,
    user_role: Optional[str] = None,
) -> bool:
    flag = await get_flag(db, key)
    if not flag:
        return False
    if not flag.enabled:
        return False
    if flag.enabled_for_roles and user_role:
        allowed_roles = [r.strip() for r in flag.enabled_for_roles.split(",")]
        if user_role not in allowed_roles:
            return False
    return True


async def create_flag(
    db: AsyncSession,
    key: str,
    name: str,
    description: str = "",
    enabled: bool = False,
    enabled_for_roles: str = "",
) -> FeatureFlag:
    flag = FeatureFlag(
        key=key,
        name=name,
        description=description,
        enabled=enabled,
        enabled_for_roles=enabled_for_roles,
    )
    db.add(flag)
    await db.flush()
    return flag


async def update_flag(
    db: AsyncSession,
    key: str,
    data: Dict[str, Any],
) -> Optional[FeatureFlag]:
    flag = await get_flag(db, key)
    if not flag:
        return None
    for field, value in data.items():
        if hasattr(flag, field):
            setattr(flag, field, value)
    await db.flush()
    return flag


async def delete_flag(db: AsyncSession, key: str) -> bool:
    flag = await get_flag(db, key)
    if not flag:
        return False
    await db.delete(flag)
    await db.flush()
    return True
