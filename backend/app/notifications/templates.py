"""Render the reminder digest to plain text + HTML."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from .. import nepali_date
from ..config import get_settings
from ..models import Event


@dataclass
class DueItem:
    event: Event
    occurrence: date
    days_until: int


def _lead_phrase(days: int) -> str:
    if days <= 0:
        return "today"
    if days == 1:
        return "tomorrow"
    return f"in {days} days"


def render_digest(items: list[DueItem], on_date: date) -> tuple[str, str, str]:
    settings = get_settings()
    count = len(items)
    subject = (
        f"Reminder: {items[0].event.title} {_lead_phrase(items[0].days_until)}"
        if count == 1
        else f"{count} upcoming dates on your Nepali Calendar"
    )

    lines = [f"Upcoming important dates (as of {on_date.isoformat()}):", ""]
    rows_html = []
    for item in items:
        bs = nepali_date.ad_to_bs(item.occurrence)
        bs_txt = nepali_date.bs_label(bs.year, bs.month, bs.day)
        ad_txt = item.occurrence.strftime("%A, %B %d, %Y")
        lead = _lead_phrase(item.days_until).capitalize()
        lines.append(f"- {item.event.title} - {lead}")
        lines.append(f"    {bs_txt} (BS)  /  {ad_txt} (AD)")
        if item.event.description:
            lines.append(f"    {item.event.description}")
        lines.append("")
        rows_html.append(
            f"""
            <tr>
              <td style="padding:12px 16px;border-bottom:1px solid #eee;">
                <div style="font-weight:600;color:#111;">{_esc(item.event.title)}</div>
                <div style="color:#666;font-size:13px;margin-top:2px;">{_esc(bs_txt)} BS &nbsp;&middot;&nbsp; {_esc(ad_txt)}</div>
                {f'<div style="color:#888;font-size:13px;margin-top:4px;">{_esc(item.event.description)}</div>' if item.event.description else ''}
              </td>
              <td style="padding:12px 16px;border-bottom:1px solid #eee;text-align:right;white-space:nowrap;color:#dc143c;font-weight:600;">{_esc(lead)}</td>
            </tr>"""
        )

    text = "\n".join(lines).rstrip() + "\n"
    html = f"""\
<!doctype html>
<html>
  <body style="margin:0;background:#f5f5f7;font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;">
    <div style="max-width:560px;margin:0 auto;padding:24px 16px;">
      <div style="background:#dc143c;color:#fff;border-radius:12px 12px 0 0;padding:18px 20px;">
        <div style="font-size:18px;font-weight:700;">Nepali Calendar</div>
        <div style="font-size:13px;opacity:.9;">Reminder digest &middot; {on_date.isoformat()}</div>
      </div>
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0"
             style="background:#fff;border-radius:0 0 12px 12px;border-collapse:collapse;">
        {''.join(rows_html)}
      </table>
      <p style="color:#999;font-size:12px;margin-top:16px;text-align:center;">
        <a href="{_esc(settings.app_base_url)}" style="color:#999;">Open the calendar</a>
      </p>
    </div>
  </body>
</html>"""
    return subject, text, html


def _esc(value: str) -> str:
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
