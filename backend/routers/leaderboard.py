from __future__ import annotations

import asyncio
import csv
import io
import json
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel, field_validator
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import SessionLocal, get_db
from models import Attendance, EndpointPerformance, Event, Student
from routers.auth import try_get_admin, verify_admin_token
from utils.stats import full_stats

router = APIRouter()

VALID_CAMPUSES = {
    "IU Bloomington", "IU Indianapolis", "IU East", "IU Kokomo",
    "IU Northwest", "IU South Bend", "IU Southeast", "IU Columbus", "IU Fort Wayne",
}


def _week_bounds(ref: datetime | None = None) -> tuple[datetime, datetime]:
    if ref is None:
        ref = datetime.now(timezone.utc).replace(tzinfo=None)
    days_since_sunday = (ref.weekday() + 1) % 7
    week_start = (ref - timedelta(days=days_since_sunday)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    week_end = week_start + timedelta(days=7) - timedelta(seconds=1)
    return week_start, week_end


def _student_rank(db: Session, student_id: int, week_start: datetime, week_end: datetime) -> int:
    student_total = (
        db.query(func.sum(Attendance.points_earned))
        .filter(
            Attendance.student_id == student_id,
            Attendance.checked_in_at >= week_start,
            Attendance.checked_in_at <= week_end,
        )
        .scalar()
        or 0
    )
    higher_count = (
        db.query(func.count(func.distinct(Attendance.student_id)))
        .filter(
            Attendance.checked_in_at >= week_start,
            Attendance.checked_in_at <= week_end,
        )
        .group_by(Attendance.student_id)
        .having(func.sum(Attendance.points_earned) > student_total)
        .count()
    )
    return higher_count + 1


def _leaderboard_rows(
    db: Session,
    week_start: datetime,
    week_end: datetime,
    campus: Optional[str] = None,
    limit: int = 10,
) -> list[dict]:
    q = (
        db.query(
            Student.id,
            Student.name,
            Student.iu_username,
            Student.campus,
            func.sum(Attendance.points_earned).label("total_points"),
            func.count(Attendance.id).label("events_attended"),
        )
        .join(Attendance, Attendance.student_id == Student.id)
        .filter(
            Attendance.checked_in_at >= week_start,
            Attendance.checked_in_at <= week_end,
        )
        .group_by(Student.id)
        .order_by(func.sum(Attendance.points_earned).desc())
    )
    if campus:
        q = q.filter(Student.campus == campus)

    rows = q.limit(limit).all()
    result = []
    dense_rank = 0
    prev_points = None
    for row in rows:
        pts = int(row.total_points)
        if pts != prev_points:
            dense_rank += 1
            prev_points = pts
        result.append({
            "rank": dense_rank,
            "student_id": row.id,
            "name": row.name,
            "iu_username": row.iu_username,
            "campus": row.campus,
            "total_points": pts,
            "events_attended": int(row.events_attended),
        })
    return result


def _enrich_rows(rows: list[dict], prev_ranks: dict[int, int]) -> list[dict]:
    rank_improvements = []
    for r in rows:
        sid = r["student_id"]
        prev = prev_ranks.get(sid)
        if prev is not None:
            change = prev - r["rank"]
            r["rank_change"] = change
            rank_improvements.append((sid, change))
        else:
            r["rank_change"] = None

    best_improver_id = None
    if rank_improvements:
        best = max(rank_improvements, key=lambda x: x[1])
        if best[1] > 0:
            best_improver_id = best[0]

    for r in rows:
        sid = r["student_id"]
        badges = []
        if r["rank"] == 1:
            badges.append("top")
        if sid == best_improver_id:
            badges.append("rising")
        if r["events_attended"] >= 3:
            badges.append("dedicated")
        if sid in prev_ranks:
            badges.append("consistent")
        r["badges"] = badges
        del r["student_id"]

    return rows


class AddEntryBody(BaseModel):
    iu_username: str
    name: str
    campus: str
    event_id: int
    check_in_code: str

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Name cannot be empty")
        return v.strip()

    @field_validator("iu_username")
    @classmethod
    def username_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("IU username cannot be empty")
        return v.strip().lower()

    @field_validator("campus")
    @classmethod
    def campus_valid(cls, v: str) -> str:
        if v not in VALID_CAMPUSES:
            raise ValueError(f"Invalid campus. Valid options: {', '.join(sorted(VALID_CAMPUSES))}")
        return v


@router.post("/add", summary="Add a leaderboard entry (admin)")
async def add_entry(
    body: AddEntryBody,
    db: Session = Depends(get_db),
    _admin: str = Depends(verify_admin_token),
):
    event = db.query(Event).filter(Event.id == body.event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    if event.check_in_code.upper() != body.check_in_code.upper():
        raise HTTPException(status_code=400, detail="Invalid check-in code for this event")

    student = db.query(Student).filter(Student.iu_username == body.iu_username).first()
    if not student:
        student = Student(
            name=body.name,
            iu_username=body.iu_username,
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
        raise HTTPException(status_code=409, detail="Student already checked in to this event")

    record = Attendance(
        student_id=student.id,
        event_id=event.id,
        points_earned=event.points,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    week_start, week_end = _week_bounds()
    new_total = (
        db.query(func.sum(Attendance.points_earned))
        .filter(
            Attendance.student_id == student.id,
            Attendance.checked_in_at >= week_start,
            Attendance.checked_in_at <= week_end,
        )
        .scalar()
        or 0
    )
    rank = _student_rank(db, student.id, week_start, week_end)

    return {
        "student": {
            "id": student.id,
            "name": student.name,
            "iu_username": student.iu_username,
            "campus": student.campus,
        },
        "points_earned": event.points,
        "new_total": int(new_total),
        "rank": rank,
    }


class RemoveEntryBody(BaseModel):
    iu_username: str
    event_id: int


@router.delete("/remove", summary="Remove a leaderboard entry (admin)")
async def remove_entry(
    body: RemoveEntryBody,
    db: Session = Depends(get_db),
    _admin: str = Depends(verify_admin_token),
):
    student = db.query(Student).filter(Student.iu_username == body.iu_username).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    record = (
        db.query(Attendance)
        .filter(Attendance.student_id == student.id, Attendance.event_id == body.event_id)
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="Attendance record not found")

    db.delete(record)
    db.commit()
    return {
        "message": "removed",
        "student": {
            "id": student.id,
            "name": student.name,
            "iu_username": student.iu_username,
            "campus": student.campus,
        },
    }


@router.get("/leaderboard/export", summary="Export leaderboard as CSV")
async def export_leaderboard(
    campus: Optional[str] = Query(None, description="Filter by campus"),
    week: Optional[str] = Query(None, description="ISO date within the desired week"),
    db: Session = Depends(get_db),
):
    ref = None
    if week:
        try:
            ref = datetime.fromisoformat(week)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid week date. Use YYYY-MM-DD.")

    week_start, week_end = _week_bounds(ref)
    rows = _leaderboard_rows(db, week_start, week_end, campus=campus, limit=500)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Rank", "Name", "IU Username", "Campus", "Events Attended", "Total Points"])
    for r in rows:
        writer.writerow([r["rank"], r["name"], r["iu_username"], r["campus"], r["events_attended"], r["total_points"]])
    output.seek(0)

    filename = f"engageiu_leaderboard_{week_start.strftime('%Y-%m-%d')}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/leaderboard", summary="Top 10 weekly leaderboard")
async def get_leaderboard(
    campus: Optional[str] = Query(None, description="Filter by IU campus"),
    week: Optional[str] = Query(None, description="ISO date within desired week (e.g. 2025-04-14)"),
    format: Optional[str] = Query(None, description="Response format: json (default) or html"),
    db: Session = Depends(get_db),
):
    ref = None
    if week:
        try:
            ref = datetime.fromisoformat(week)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid week date format. Use YYYY-MM-DD.")

    week_start, week_end = _week_bounds(ref)
    rows = _leaderboard_rows(db, week_start, week_end, campus=campus, limit=100)

    prev_start = week_start - timedelta(days=7)
    prev_end = week_start - timedelta(seconds=1)
    prev_rows = _leaderboard_rows(db, prev_start, prev_end, limit=200)
    prev_ranks = {r["student_id"]: r["rank"] for r in prev_rows}

    enriched = _enrich_rows(rows, prev_ranks)

    if format == "html":
        week_label = f"{week_start.strftime('%b %d')} to {week_end.strftime('%b %d, %Y')}"
        campus_label = campus or "All Campuses"
        rows_html = ""
        medal = {1: "🥇", 2: "🥈", 3: "🥉"}

        def trend_cell(rc):
            if rc is None:
                return ""
            if rc > 0:
                return f"<span style='color:#16a34a;font-size:0.75rem;font-weight:600'>+{rc}</span>"
            if rc < 0:
                return f"<span style='color:#dc2626;font-size:0.75rem;font-weight:600'>{rc}</span>"
            return ""

        def rising_tag(badges):
            if "rising" in badges:
                return "<span style='color:#16a34a;font-size:0.7rem;margin-left:4px'>rising</span>"
            return ""

        for r in enriched:
            icon = medal.get(r["rank"], "")
            trend = trend_cell(r.get("rank_change"))
            rising = rising_tag(r.get("badges", []))
            rows_html += (
                f"<tr class='rank-{r['rank']}'>"
                f"<td style='white-space:nowrap'>{icon} {r['rank']} {trend}</td>"
                f"<td>{r['name']}{rising}</td>"
                f"<td style='color:#666'>@{r['iu_username']}</td>"
                f"<td>{r['campus']}</td>"
                f"<td style='text-align:center'>{r['events_attended']}</td>"
                f"<td style='text-align:center'><strong>{r['total_points']}</strong></td>"
                f"</tr>"
            )
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta http-equiv="refresh" content="2">
<link rel="icon" type="image/png" href="https://assets.iu.edu/brand/3.3.x/trident-large.png">
<title>EngageIU · Weekly Leaderboard</title>
<style>
  body {{ font-family: 'Segoe UI', sans-serif; background: #f5f5f5; padding: 2rem; margin: 0; }}
  h1 {{ color: #990000; margin-bottom: 0.25rem; }}
  .meta {{ color: #555; font-size: 0.95rem; margin-bottom: 1.5rem; }}
  .live-pill {{ display: inline-flex; align-items: center; gap: 5px; background: #f0fdf4;
               border: 1px solid #bbf7d0; border-radius: 99px; padding: 2px 10px;
               font-size: 0.75rem; font-weight: 600; color: #16a34a; margin-left: 12px; }}
  .dot {{ width: 7px; height: 7px; background: #16a34a; border-radius: 50%;
          animation: pulse 1.5s infinite; }}
  @keyframes pulse {{ 0%,100%{{opacity:1}} 50%{{opacity:0.3}} }}
  table {{ border-collapse: collapse; width: 100%; max-width: 900px; background: #fff;
           box-shadow: 0 2px 8px rgba(0,0,0,0.1); border-radius: 8px; overflow: hidden; }}
  th {{ background: #990000; color: #fff; padding: 12px 16px; text-align: left; font-size: 0.9rem; }}
  td {{ padding: 11px 16px; border-bottom: 1px solid #eee; vertical-align: middle; }}
  tr.rank-1 td {{ background: #fff8f8; font-weight: 600; }}
  tr:hover td {{ background: #fafafa; }}
  .refresh-note {{ margin-top: 0.75rem; color: #9ca3af; font-size: 0.8rem; }}
</style>
</head>
<body>
<h1>EngageIU Weekly Leaderboard<span class="live-pill"><span class="dot"></span> LIVE</span></h1>
<p class="meta">Week of {week_label} &nbsp;&bull;&nbsp; {campus_label}</p>
<table>
  <thead><tr>
    <th>Rank</th><th>Name</th><th>IU Username</th>
    <th>Campus</th><th>Events</th><th>Points</th>
  </tr></thead>
  <tbody>{rows_html}</tbody>
</table>
<p class="refresh-note">Auto-refreshes every 2 seconds</p>
</body></html>"""
        return HTMLResponse(content=html)

    return {
        "week_start": week_start.isoformat(),
        "week_end": week_end.isoformat(),
        "campus_filter": campus,
        "leaderboard": enriched,
    }


@router.get("/leaderboard/stream", summary="Live leaderboard via Server-Sent Events")
async def leaderboard_stream(
    request: Request,
    campus: Optional[str] = Query(None),
):
    async def generate():
        last_payload = None
        while True:
            if await request.is_disconnected():
                break
            db = SessionLocal()
            try:
                week_start, week_end = _week_bounds()
                rows = _leaderboard_rows(db, week_start, week_end, campus=campus, limit=100)
                prev_start = week_start - timedelta(days=7)
                prev_end = week_start - timedelta(seconds=1)
                prev_rows = _leaderboard_rows(db, prev_start, prev_end, limit=200)
                prev_ranks = {r["student_id"]: r["rank"] for r in prev_rows}
                enriched = _enrich_rows(rows, prev_ranks)
                payload = json.dumps({
                    "week_start": week_start.isoformat(),
                    "week_end": week_end.isoformat(),
                    "leaderboard": enriched,
                })
            finally:
                db.close()

            if payload != last_payload:
                last_payload = payload
                yield "data: " + payload + "\n\n"

            await asyncio.sleep(2)

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@router.get("/info", summary="Score statistics (always full extended stats)")
async def get_info(
    db: Session = Depends(get_db),
    admin: Optional[str] = Depends(try_get_admin),
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

    campus_rows = (
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
    top_campus = campus_rows.campus if campus_rows else None

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

    cat_rows = (
        db.query(
            Event.category,
            func.count(Attendance.id).label("checkin_count"),
        )
        .join(Attendance, Attendance.event_id == Event.id)
        .filter(
            Attendance.checked_in_at >= week_start,
            Attendance.checked_in_at <= week_end,
        )
        .group_by(Event.category)
        .order_by(func.count(Attendance.id).desc())
        .all()
    )
    category_breakdown = [
        {"category": r.category or "General", "count": r.checkin_count}
        for r in cat_rows
    ]
    top_category = category_breakdown[0]["category"] if category_breakdown else None

    all_checkins = (
        db.query(Attendance.checked_in_at)
        .filter(
            Attendance.checked_in_at >= week_start,
            Attendance.checked_in_at <= week_end,
        )
        .all()
    )
    day_counts = {}
    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    for (ts,) in all_checkins:
        d = day_names[ts.weekday()]
        day_counts[d] = day_counts.get(d, 0) + 1
    most_active_day = max(day_counts, key=day_counts.get) if day_counts else None

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
    total_attendance_this_week = (
        db.query(func.count(Attendance.id))
        .filter(
            Attendance.checked_in_at >= week_start,
            Attendance.checked_in_at <= week_end,
        )
        .scalar()
        or 0
    )
    avg_events = round(total_attendance_this_week / students_with_points, 2) if students_with_points > 0 else 0.0

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
        "category_breakdown": category_breakdown,
        "top_category": top_category,
        "most_active_day": most_active_day,
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


@router.get("/performance", summary="Average endpoint execution times (admin)")
async def get_performance(
    db: Session = Depends(get_db),
    _admin: str = Depends(verify_admin_token),
):
    rows = (
        db.query(
            EndpointPerformance.endpoint,
            EndpointPerformance.method,
            func.avg(EndpointPerformance.response_time_ms).label("avg_ms"),
            func.min(EndpointPerformance.response_time_ms).label("min_ms"),
            func.max(EndpointPerformance.response_time_ms).label("max_ms"),
            func.count(EndpointPerformance.id).label("call_count"),
        )
        .group_by(EndpointPerformance.endpoint, EndpointPerformance.method)
        .order_by(func.avg(EndpointPerformance.response_time_ms).desc())
        .all()
    )
    return {
        "endpoints": [
            {
                "endpoint": r.endpoint,
                "method": r.method,
                "avg_ms": round(float(r.avg_ms), 3),
                "min_ms": round(float(r.min_ms), 3),
                "max_ms": round(float(r.max_ms), 3),
                "call_count": r.call_count,
            }
            for r in rows
        ]
    }


@router.get("/history", summary="Score submission history with filtering (admin, grad requirement)")
async def get_history(
    name: Optional[str] = Query(None, description="Filter by student name (partial match)"),
    iu_username: Optional[str] = Query(None, description="Filter by IU username (partial match)"),
    event_id: Optional[int] = Query(None, description="Filter by exact event ID"),
    category: Optional[str] = Query(None, description="Filter by event category"),
    start_date: Optional[str] = Query(None, description="ISO date filter start (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="ISO date filter end (YYYY-MM-DD)"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _admin: str = Depends(verify_admin_token),
):
    q = (
        db.query(Attendance)
        .join(Student, Student.id == Attendance.student_id)
        .join(Event, Event.id == Attendance.event_id)
        .order_by(Attendance.checked_in_at.desc())
    )

    if name:
        q = q.filter(Student.name.ilike(f"%{name}%"))
    if iu_username:
        q = q.filter(Student.iu_username.ilike(f"%{iu_username}%"))
    if event_id:
        q = q.filter(Attendance.event_id == event_id)
    if category:
        q = q.filter(Event.category.ilike(f"%{category}%"))
    if start_date:
        try:
            q = q.filter(Attendance.checked_in_at >= datetime.fromisoformat(start_date))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid start_date. Use YYYY-MM-DD.")
    if end_date:
        try:
            q = q.filter(Attendance.checked_in_at < datetime.fromisoformat(end_date) + timedelta(days=1))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid end_date. Use YYYY-MM-DD.")

    total = q.count()
    records = q.offset((page - 1) * page_size).limit(page_size).all()

    items = [
        {
            "checkin_id": r.id,
            "student_name": r.student.name,
            "iu_username": r.student.iu_username,
            "campus": r.student.campus,
            "event_name": r.event.title,
            "event_id": r.event.id,
            "event_category": r.event.category or "General",
            "points_earned": r.points_earned,
            "checked_in_at": r.checked_in_at.isoformat() + "Z",
        }
        for r in records
    ]

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
        "filters_applied": {
            "iu_username": iu_username,
            "event_id": event_id,
            "category": category,
            "start_date": start_date,
            "end_date": end_date,
        },
        "items": items,
    }
