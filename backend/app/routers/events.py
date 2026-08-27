"""CRUD for events plus an 'upcoming occurrences' feed."""

from __future__ import annotations

from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from .. import crud, nepali_date
from ..database import get_db
from ..models import Event
from ..notifications.service import send_event_reminder
from ..recurrence import occurrences_in_range
from ..schemas import (
    BsDate,
    EventCreate,
    EventOccurrence,
    EventOut,
    EventUpdate,
    SendReminderRequest,
)

router = APIRouter(prefix="/api/events", tags=["events"])


def _occurrence(event: Event, occ) -> EventOccurrence:
    b = nepali_date.ad_to_bs(occ)
    return EventOccurrence(
        event=EventOut.model_validate(event),
        occurrence_ad=occ,
        occurrence_bs=BsDate(year=b.year, month=b.month, day=b.day),
        days_until=(occ - nepali_date.today_npt()).days,
    )


@router.get("", response_model=list[EventOut])
def list_events(db: Session = Depends(get_db)) -> list[Event]:
    return crud.list_events(db)


@router.get("/upcoming", response_model=list[EventOccurrence])
def upcoming(
    days: int = Query(default=30, ge=1, le=400),
    db: Session = Depends(get_db),
) -> list[EventOccurrence]:
    today = nepali_date.today_npt()
    end = today + timedelta(days=days)
    items: list[EventOccurrence] = []
    for event in crud.list_events(db):
        for occ in occurrences_in_range(event, today, end):
            items.append(_occurrence(event, occ))
    items.sort(key=lambda i: (i.occurrence_ad, i.event.title))
    return items


@router.get("/{event_id}", response_model=EventOut)
def get_event(event_id: int, db: Session = Depends(get_db)) -> Event:
    event = crud.get_event(db, event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


@router.post("", response_model=EventOut, status_code=201)
def create_event(payload: EventCreate, db: Session = Depends(get_db)) -> Event:
    try:
        return crud.create_event(db, payload)
    except nepali_date.DateOutOfRange as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.put("/{event_id}", response_model=EventOut)
def update_event(
    event_id: int, payload: EventUpdate, db: Session = Depends(get_db)
) -> Event:
    event = crud.get_event(db, event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    try:
        return crud.update_event(db, event, payload)
    except nepali_date.DateOutOfRange as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.delete("/{event_id}", status_code=204, response_class=Response)
def delete_event(event_id: int, db: Session = Depends(get_db)) -> Response:
    event = crud.get_event(db, event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    crud.delete_event(db, event)
    return Response(status_code=204)


@router.post("/{event_id}/send-reminder")
def send_reminder_now(
    event_id: int,
    payload: SendReminderRequest,
    db: Session = Depends(get_db),
) -> dict:
    """Email and/or text a reminder for this event right now."""
    event = crud.get_event(db, event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return send_event_reminder(db, event, payload.channels)
