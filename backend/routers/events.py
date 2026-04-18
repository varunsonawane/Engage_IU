"""
Events CRUD, check-in endpoint, and student search.
"""
from __future__ import annotations

import asyncio
import secrets
import string
import urllib.request
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import get_db
from models import Attendance, Event, EventCode, Student
from routers.auth import try_get_admin, verify_admin_token
from utils.stats import full_stats

router = APIRouter()

ALPHANUMERIC = string.ascii_uppercase + string.digits


def generate_code(length: int = 8) -> str:
    """Cryptographically secure random alphanumeric code (uppercase)."""
    return "".join(secrets.choice(ALPHANUMERIC) for _ in range(length))


def normalize_url(url: Optional[str]) -> Optional[str]:
    """Ensure URL has a scheme; prepend https:// if missing."""
    if not url or not url.strip():
        return None
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url


def _sync_check_url(url: str) -> bool:
    """Synchronous URL reachability check (HEAD then GET fallback). Returns True if reachable."""
    headers = {"User-Agent": "EngageIU/1.0"}
    for method in ("HEAD", "GET"):
        try:
            req = urllib.request.Request(url, method=method, headers=headers)
            with urllib.request.urlopen(req, timeout=5) as resp:
                return resp.status < 400
        except Exception:
            continue
    return False


async def _check_url(url: str) -> bool:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _sync_check_url, url)


def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _week_bounds(ref: Optional[datetime] = None):
    if ref is None:
        ref = utcnow()
    days_since_sunday = (ref.weekday() + 1) % 7
    week_start = (ref - timedelta(days=days_since_sunday)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    week_end = week_start + timedelta(days=7) - timedelta(seconds=1)
    return week_start, week_end


def _upsert_event_code(db: Session, event: Event, set_by: str = "admin") -> None:
    """Insert or update the event_codes row for a given event."""
    existing = db.query(EventCode).filter(EventCode.event_id == event.id).first()
    if existing:
        existing.code = event.check_in_code
        existing.event_name = event.title
        existing.updated_at = utcnow()
        existing.set_by = set_by
    else:
        db.add(EventCode(
            event_id=event.id,
            event_name=event.title,
            code=event.check_in_code,
            set_by=set_by,
            updated_at=utcnow(),
        ))



class EventCreate(BaseModel):
    title: str
    description: Optional[str] = None
    category: Optional[str] = None   # e.g. Academic, Career, Social, Health, Cultural, Tech
    campus: str
    event_url: Optional[str] = None
    points: int = 10
    event_date: str  # ISO 8601 string


class EventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    campus: Optional[str] = None
    event_url: Optional[str] = None
    points: Optional[int] = None
    event_date: Optional[str] = None
    regenerate_code: bool = False


class CheckInBody(BaseModel):
    iu_username: str
    name: str
    campus: str
    check_in_code: str


class BonusPointsBody(BaseModel):
    bonus_points: int



@router.get("/events", summary="List events")
async def list_events(
    campus: Optional[str] = Query(None),
    upcoming_only: bool = Query(True, description="Only return future events"),
    db: Session = Depends(get_db),
    admin: Optional[str] = Depends(try_get_admin),
):
    q = db.query(Event)
    if campus:
        q = q.filter(Event.campus == campus)
    if upcoming_only:
        q = q.filter(Event.event_date >= utcnow())
    q = q.order_by(Event.event_date.asc())
    events = q.all()

    result = []
    for e in events:
        attendee_count = db.query(func.count(Attendance.id)).filter(
            Attendance.event_id == e.id
        ).scalar() or 0
        item = {
            "id": e.id,
            "title": e.title,
            "description": e.description,
            "category": e.category or "General",
            "campus": e.campus,
            "event_url": e.event_url,
            "points": e.points,
            "event_date": e.event_date.isoformat() + "Z",
            "attendees": attendee_count,
        }
        if admin:
            item["check_in_code"] = e.check_in_code
        result.append(item)
    return result



@router.post("/events", status_code=201, summary="Create event (admin)")
async def create_event(
    body: EventCreate,
    db: Session = Depends(get_db),
    _admin: str = Depends(verify_admin_token),
):
    try:
        event_date = datetime.fromisoformat(body.event_date.replace("Z", ""))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid event_date format. Use ISO 8601.")

    event_url = normalize_url(body.event_url)
    if event_url and not await _check_url(event_url):
        raise HTTPException(status_code=400, detail=f"Event URL is not reachable: {event_url}")

    # Ensure unique code
    for _ in range(10):
        code = generate_code()
        if not db.query(Event).filter(Event.check_in_code == code).first():
            break

    event = Event(
        title=body.title,
        description=body.description,
        category=body.category,
        campus=body.campus,
        event_url=event_url,
        check_in_code=code,
        points=body.points,
        event_date=event_date,
    )
    db.add(event)
    db.flush()

    _upsert_event_code(db, event, set_by="admin")
    db.commit()
    db.refresh(event)
    return {
        "id": event.id,
        "title": event.title,
        "description": event.description,
        "category": event.category or "General",
        "campus": event.campus,
        "event_url": event.event_url,
        "check_in_code": event.check_in_code,
        "points": event.points,
        "event_date": event.event_date.isoformat() + "Z",
    }



@router.patch("/events/{event_id}", summary="Update event (admin)")
async def update_event(
    event_id: int,
    body: EventUpdate,
    db: Session = Depends(get_db),
    _admin: str = Depends(verify_admin_token),
):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    if body.title is not None:
        event.title = body.title
    if body.description is not None:
        event.description = body.description
    if body.category is not None:
        event.category = body.category
    if body.campus is not None:
        event.campus = body.campus
    if body.event_url is not None:
        event_url = normalize_url(body.event_url)
        if event_url and not await _check_url(event_url):
            raise HTTPException(status_code=400, detail=f"Event URL is not reachable: {event_url}")
        event.event_url = event_url
    if body.points is not None:
        event.points = body.points
    if body.event_date is not None:
        try:
            event.event_date = datetime.fromisoformat(body.event_date.replace("Z", ""))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid event_date format.")
    if body.regenerate_code:
        for _ in range(10):
            code = generate_code()
            if not db.query(Event).filter(Event.check_in_code == code).first():
                break
        event.check_in_code = code
        _upsert_event_code(db, event, set_by="admin")

    db.commit()
    db.refresh(event)
    return {
        "id": event.id,
        "title": event.title,
        "description": event.description,
        "category": event.category or "General",
        "campus": event.campus,
        "event_url": event.event_url,
        "check_in_code": event.check_in_code,
        "points": event.points,
        "event_date": event.event_date.isoformat() + "Z",
    }



@router.delete("/events/{event_id}", summary="Delete event (admin)")
async def delete_event(
    event_id: int,
    db: Session = Depends(get_db),
    _admin: str = Depends(verify_admin_token),
):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    db.delete(event)
    db.commit()
    return {"message": "Event {} deleted".format(event_id)}



@router.get("/events/{event_id}/code", summary="Get check-in code for event (admin)")
async def get_event_code(
    event_id: int,
    db: Session = Depends(get_db),
    _admin: str = Depends(verify_admin_token),
):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return {"event_id": event_id, "check_in_code": event.check_in_code}



@router.post("/events/{event_id}/regenerate-code", summary="Regenerate check-in code (admin)")
async def regenerate_event_code(
    event_id: int,
    db: Session = Depends(get_db),
    _admin: str = Depends(verify_admin_token),
):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    for _ in range(10):
        code = generate_code()
        if not db.query(Event).filter(Event.check_in_code == code).first():
            break

    event.check_in_code = code
    _upsert_event_code(db, event, set_by="admin")
    db.commit()
    db.refresh(event)
    return {
        "event_id": event.id,
        "check_in_code": event.check_in_code,
    }



@router.get("/admin/students", summary="List all students (admin)")
async def admin_list_students(
    db: Session = Depends(get_db),
    _admin: str = Depends(verify_admin_token),
):
    week_start, week_end = _week_bounds()

    students = db.query(Student).all()

    today_start = utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)
    checkins_today = (
        db.query(func.count(Attendance.id))
        .filter(
            Attendance.checked_in_at >= today_start,
            Attendance.checked_in_at < today_end,
        )
        .scalar()
        or 0
    )

    result = []
    for s in students:
        weekly_pts = (
            db.query(func.sum(Attendance.points_earned))
            .filter(
                Attendance.student_id == s.id,
                Attendance.checked_in_at >= week_start,
                Attendance.checked_in_at <= week_end,
            )
            .scalar()
            or 0
        )
        events_attended = (
            db.query(func.count(Attendance.id))
            .filter(Attendance.student_id == s.id)
            .scalar()
            or 0
        )
        result.append({
            "id": s.id,
            "name": s.name,
            "iu_username": s.iu_username,
            "campus": s.campus,
            "major": s.major,
            "year": s.year,
            "bonus_points": s.bonus_points,
            "weekly_points": int(weekly_pts),
            "events_attended": int(events_attended),
            "created_at": s.created_at.isoformat() + "Z",
        })

    result.sort(key=lambda x: x["weekly_points"], reverse=True)

    return {
        "total_students": len(result),
        "checkins_today": int(checkins_today),
        "students": result,
    }



@router.delete("/admin/students/{student_id}", summary="Delete student (admin)")
async def admin_delete_student(
    student_id: int,
    db: Session = Depends(get_db),
    _admin: str = Depends(verify_admin_token),
):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    db.delete(student)
    db.commit()
    return {"message": "Student {} deleted".format(student_id)}



@router.patch("/admin/students/{student_id}", summary="Update student bonus points (admin)")
async def admin_update_student(
    student_id: int,
    body: BonusPointsBody,
    db: Session = Depends(get_db),
    _admin: str = Depends(verify_admin_token),
):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    student.bonus_points = body.bonus_points
    db.commit()
    return {"id": student.id, "bonus_points": student.bonus_points}



@router.post("/admin/verify-event-urls", summary="Check all event URLs and remove broken ones (admin)")
async def verify_event_urls(
    db: Session = Depends(get_db),
    _admin: str = Depends(verify_admin_token),
):
    events = db.query(Event).filter(Event.event_url.isnot(None)).all()
    removed = []
    kept = []
    for event in events:
        url = normalize_url(event.event_url)
        if not url:
            event.event_url = None
            removed.append({"id": event.id, "title": event.title, "url": event.event_url})
            continue
        ok = await _check_url(url)
        if ok:
            event.event_url = url  # normalize in place
            kept.append({"id": event.id, "title": event.title, "url": url})
        else:
            removed.append({"id": event.id, "title": event.title, "url": url})
            event.event_url = None
    db.commit()
    return {
        "checked": len(events),
        "valid": len(kept),
        "removed": len(removed),
        "removed_events": removed,
    }


@router.get("/admin/event-codes", summary="List all event codes (admin)")
async def admin_list_event_codes(
    db: Session = Depends(get_db),
    _admin: str = Depends(verify_admin_token),
):
    rows = db.query(EventCode).order_by(EventCode.updated_at.desc()).all()
    return [
        {
            "event_id": r.event_id,
            "event_name": r.event_name,
            "code": r.code,
            "set_by": r.set_by,
            "updated_at": r.updated_at.isoformat() + "Z",
        }
        for r in rows
    ]



@router.get("/admin/stats", summary="Public analytics stats (extended)")
async def admin_stats(
    db: Session = Depends(get_db),
):
    week_start, week_end = _week_bounds()

    score_rows = (
        db.query(
            Student.id,
            Student.campus,
            func.sum(Attendance.points_earned).label("total"),
        )
        .join(Attendance, Attendance.student_id == Student.id)
        .filter(
            Attendance.checked_in_at >= week_start,
            Attendance.checked_in_at <= week_end,
        )
        .group_by(Student.id)
        .all()
    )

    scores = [float(r.total) for r in score_rows]
    total_students = db.query(func.count(Student.id)).scalar() or 0
    total_events = db.query(func.count(Event.id)).scalar() or 0

    stats = full_stats(scores)

    # Top campus by total weekly points
    campus_row = (
        db.query(
            Student.campus,
            func.sum(Attendance.points_earned).label("campus_total"),
        )
        .join(Attendance, Attendance.student_id == Student.id)
        .filter(
            Attendance.checked_in_at >= week_start,
            Attendance.checked_in_at <= week_end,
        )
        .group_by(Student.campus)
        .order_by(func.sum(Attendance.points_earned).desc())
        .first()
    )
    top_campus = campus_row.campus if campus_row else None

    # Most attended event this week
    event_row = (
        db.query(
            Event.title,
            func.count(Attendance.id).label("cnt"),
        )
        .join(Attendance, Attendance.event_id == Event.id)
        .filter(
            Attendance.checked_in_at >= week_start,
            Attendance.checked_in_at <= week_end,
        )
        .group_by(Event.id)
        .order_by(func.count(Attendance.id).desc())
        .first()
    )
    most_attended = event_row.title if event_row else None

    # Weekly growth rate
    prev_start = week_start - timedelta(days=7)
    prev_end = week_start - timedelta(seconds=1)
    this_week_count = (
        db.query(func.count(Attendance.id))
        .filter(
            Attendance.checked_in_at >= week_start,
            Attendance.checked_in_at <= week_end,
        )
        .scalar()
        or 0
    )
    last_week_count = (
        db.query(func.count(Attendance.id))
        .filter(
            Attendance.checked_in_at >= prev_start,
            Attendance.checked_in_at <= prev_end,
        )
        .scalar()
        or 0
    )
    if last_week_count > 0:
        growth = round((this_week_count - last_week_count) / last_week_count * 100, 1)
    else:
        growth = None

    students_with_points = len(scores)

    # avg_events_per_student: total attendance records this week / students_with_points
    total_attendance_this_week = (
        db.query(func.count(Attendance.id))
        .filter(
            Attendance.checked_in_at >= week_start,
            Attendance.checked_in_at <= week_end,
        )
        .scalar()
        or 0
    )
    if students_with_points > 0:
        avg_events = round(total_attendance_this_week / students_with_points, 2)
    else:
        avg_events = 0.0

    std_dev = stats["std_deviation"]
    variance = round(std_dev ** 2, 2)
    q1 = stats["q1"]
    q3 = stats["q3"]
    iqr = round(q3 - q1, 2)
    score_min = stats["min"]
    score_max = stats["max"]
    range_val = round(score_max - score_min, 2)

    return {
        "total_students": total_students,
        "total_events": total_events,
        "students_with_points_this_week": students_with_points,
        "mean": stats["mean"],
        "median": stats["median"],
        "q1": q1,
        "q3": q3,
        "min": score_min,
        "max": score_max,
        "std_deviation": std_dev,
        "percentile_ranks": stats["percentile_ranks"],
        "score_distribution": stats["score_distribution"],
        "top_campus": top_campus,
        "most_attended_event": most_attended,
        "weekly_growth_rate_pct": growth,
        "avg_events_per_student": avg_events,
        "variance": variance,
        "iqr": iqr,
        "range_val": range_val,
    }



@router.post("/checkin", summary="Student self check-in")
async def student_checkin(
    body: CheckInBody,
    db: Session = Depends(get_db),
):
    """
    Public endpoint: student enters check-in code to earn points.
    Creates the student record if they're new to the system.
    """
    event = (
        db.query(Event)
        .filter(Event.check_in_code == body.check_in_code.upper().strip())
        .first()
    )
    if not event:
        raise HTTPException(status_code=404, detail="Invalid check-in code. Please double-check and try again.")

    student = db.query(Student).filter(Student.iu_username == body.iu_username.lower().strip()).first()
    if not student:
        student = Student(
            name=body.name.strip(),
            iu_username=body.iu_username.lower().strip(),
            campus=body.campus,
        )
        db.add(student)
        db.flush()

    existing = (
        db.query(Attendance)
        .filter(Attendance.student_id == student.id, Attendance.event_id == event.id)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=409,
            detail="You've already checked in to this event. Each event can only be claimed once.",
        )

    record = Attendance(
        student_id=student.id,
        event_id=event.id,
        points_earned=event.points,
    )
    db.add(record)
    db.commit()

    week_start, week_end = _week_bounds()
    total_points = (
        db.query(func.sum(Attendance.points_earned))
        .filter(
            Attendance.student_id == student.id,
            Attendance.checked_in_at >= week_start,
            Attendance.checked_in_at <= week_end,
        )
        .scalar()
        or 0
    )

    # Rank = number of students with MORE points this week + 1
    subq = (
        db.query(func.sum(Attendance.points_earned).label("s"))
        .filter(
            Attendance.checked_in_at >= week_start,
            Attendance.checked_in_at <= week_end,
        )
        .group_by(Attendance.student_id)
        .subquery()
    )
    rank = (
        db.query(func.count()).filter(subq.c.s > total_points).scalar() or 0
    ) + 1

    return {
        "success": True,
        "points_earned": event.points,
        "total_points": int(total_points),
        "current_rank": rank,
        "event": {
            "title": event.title,
            "campus": event.campus,
        },
    }



@router.get("/students/search", summary="Search students by name or username")
async def search_students(
    q: str = Query("", description="Partial name or IU username"),
    campus: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    week_start, week_end = _week_bounds()

    query = db.query(Student)
    if q:
        query = query.filter(
            (Student.name.ilike("%" + q + "%")) | (Student.iu_username.ilike("%" + q + "%"))
        )
    if campus:
        query = query.filter(Student.campus == campus)

    students = query.limit(20).all()
    result = []
    for s in students:
        total = (
            db.query(func.sum(Attendance.points_earned))
            .filter(
                Attendance.student_id == s.id,
                Attendance.checked_in_at >= week_start,
                Attendance.checked_in_at <= week_end,
            )
            .scalar()
            or 0
        )
        result.append(
            {
                "id": s.id,
                "name": s.name,
                "iu_username": s.iu_username,
                "campus": s.campus,
                "weekly_points": int(total),
            }
        )
    # Sort by weekly points descending
    result.sort(key=lambda x: x["weekly_points"], reverse=True)
    return result
