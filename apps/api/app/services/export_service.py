import csv
import io

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.candidate import Candidate
from app.models.interview import Interview


async def export_candidates_csv(db: AsyncSession) -> bytes:
    result = await db.execute(select(Candidate).order_by(Candidate.created_at.desc()))
    candidates = result.scalars().all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Name", "Email", "Skills", "Created At"])
    for c in candidates:
        writer.writerow([
            str(c.id), c.name, c.email,
            ", ".join(c.extracted_skills) if c.extracted_skills else "",
            c.created_at.isoformat() if c.created_at else "",
        ])
    return output.getvalue().encode("utf-8")


async def export_interviews_csv(
    db: AsyncSession, status: str | None = None,
    date_from: str | None = None, date_to: str | None = None,
) -> bytes:
    query = select(Interview).order_by(Interview.created_at.desc())
    if status:
        query = query.where(Interview.status == status)
    result = await db.execute(query)
    interviews = result.scalars().all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Candidate ID", "Status", "Score", "Questions", "Created At"])
    for iv in interviews:
        writer.writerow([
            str(iv.id), str(iv.candidate_id), iv.status,
            iv.total_score or 0, iv.question_count,
            iv.created_at.isoformat() if iv.created_at else "",
        ])
    return output.getvalue().encode("utf-8")
