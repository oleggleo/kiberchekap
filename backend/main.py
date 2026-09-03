import asyncio
from contextlib import asynccontextmanager
from datetime import timedelta
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Request, Form, BackgroundTasks, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy.orm import Session

from db import get_db, session_scope
from models import Lead, EmailLog, Reply, User, utcnow
import okved_search
from config import settings
from notifications.service import notification_service, sent_events
from notifications import chain, templates
import auth
import pages
import admin_pages
import scheduler
import imap_poller
from env_store import read_env, write_env


@asynccontextmanager
async def lifespan(app: FastAPI):
    tasks = [
        asyncio.create_task(scheduler.loop()),
        asyncio.create_task(imap_poller.loop()),
    ]
    yield
    for task in tasks:
        task.cancel()


app = FastAPI(title="Kiberchekap CRM API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["POST", "GET", "PATCH"],
    allow_headers=["*"],
)

FILES_DIR = Path(__file__).resolve().parent.parent / "frontend" / "files"
FILES_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/files", StaticFiles(directory=str(FILES_DIR)), name="files")


class LeadCreate(BaseModel):
    name: str
    phone: str
    email: str
    inn: Optional[str] = None
    segment: Optional[str] = None
    okved_code: Optional[str] = None
    okved_name: Optional[str] = None


class LeadUpdate(BaseModel):
    cyber_problem: Optional[str] = None


def _send_lead_created_email(lead_id: int):
    with session_scope() as db:
        try:
            lead = db.query(Lead).filter(Lead.id == lead_id).first()
            if lead:
                notification_service.send_event(db, lead, "lead_created")
        except Exception as e:
            print(f"[create_lead:bg] lead {lead_id}: {e}")


def _get_lead_or_404(db: Session, lead_id: int) -> Lead:
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Лид не найден")
    return lead


@app.get("/okved/suggest")
def okved_suggest(q: str = "", limit: int = 5, db: Session = Depends(get_db)):
    limit = max(1, min(limit, 10))
    return {"items": okved_search.search(db, q, limit)}


@app.post("/leads")
def create_lead(
    lead_data: LeadCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    new_lead = Lead(**lead_data.model_dump())
    db.add(new_lead)
    db.commit()
    db.refresh(new_lead)
    background_tasks.add_task(_send_lead_created_email, new_lead.id)
    return {"message": "Заявка сохранена", "lead_id": new_lead.id}


@app.patch("/leads/{lead_id}")
def update_lead(lead_id: int, lead_data: LeadUpdate, db: Session = Depends(get_db)):
    lead = _get_lead_or_404(db, lead_id)
    if lead_data.cyber_problem is not None:
        lead.cyber_problem = lead_data.cyber_problem
    db.commit()
    return {"message": "Обновлено"}


def _role(request):
    session = auth.read_session(request)
    return session["role"] if session else None


def _guard_login(request):
    if not settings.is_configured():
        return RedirectResponse(url="/setup", status_code=303)
    if not auth.is_logged_in(request):
        return RedirectResponse(url="/login", status_code=303)
    return None


def _guard_admin(request):
    if not settings.is_configured():
        return None
    if not auth.is_logged_in(request):
        return RedirectResponse(url="/login", status_code=303)
    if not auth.is_admin(request):
        return RedirectResponse(url="/admin?msg=Раздел доступен только администратору", status_code=303)
    return None


@app.get("/login", response_class=HTMLResponse)
def login_form():
    if not settings.is_configured():
        return RedirectResponse(url="/setup", status_code=303)
    return HTMLResponse(pages.login_page())


@app.post("/login")
def login_submit(login: str = Form(""), password: str = Form("")):
    role = auth.authenticate(login, password)
    if not role:
        return HTMLResponse(pages.login_page("Неверный логин или пароль"), status_code=401)
    resp = RedirectResponse(url="/admin", status_code=303)
    resp.set_cookie(auth.COOKIE_NAME, auth.make_session_value(login, role), httponly=True, samesite="lax")
    return resp


@app.get("/logout")
def logout():
    resp = RedirectResponse(url="/login", status_code=303)
    resp.delete_cookie(auth.COOKIE_NAME)
    return resp


@app.get("/setup", response_class=HTMLResponse)
def setup_form(request: Request, msg: str = "", db: Session = Depends(get_db)):
    guard = _guard_admin(request)
    if guard:
        return guard
    managers = db.query(User).order_by(User.created_at).all()
    return HTMLResponse(
        pages.setup_page(
            read_env(), managers,
            first_run=not settings.is_configured(), message=msg,
        )
    )


@app.post("/setup", response_class=HTMLResponse)
async def setup_submit(request: Request):
    guard = _guard_admin(request)
    if guard:
        return guard

    form = await request.form()
    new_values = {}
    text_keys = [
        "SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SENDER_NAME", "SENDER_EMAIL",
        "CORS_ORIGINS", "SITE_URL", "IMAP_HOST", "IMAP_PORT", "IMAP_USER",
        "SCHEDULE_INTERVAL_DAYS", "ADMIN_LOGIN",
    ]
    for key in text_keys:
        new_values[key] = (form.get(key) or "").strip()

    for key in ["SMTP_PASSWORD", "IMAP_PASSWORD", "ADMIN_PASSWORD"]:
        value = (form.get(key) or "").strip()
        if value:
            new_values[key] = value

    write_env(new_values)
    settings.reload()
    return HTMLResponse(pages.saved_page())


@app.post("/setup/users")
def setup_add_user(
    request: Request,
    login: str = Form(""),
    password: str = Form(""),
    db: Session = Depends(get_db),
):
    guard = _guard_admin(request)
    if guard:
        return guard
    login = login.strip()
    if not login or not password:
        return RedirectResponse(url="/setup?msg=Заполните логин и пароль", status_code=303)
    if db.query(User).filter(User.login == login).first():
        return RedirectResponse(url="/setup?msg=Такой логин уже есть", status_code=303)
    db.add(User(login=login, password_hash=auth.hash_password(password), role="manager"))
    db.commit()
    return RedirectResponse(url="/setup?msg=Менеджер добавлен", status_code=303)


@app.post("/setup/users/delete")
def setup_delete_user(request: Request, user_id: int = Form(...), db: Session = Depends(get_db)):
    guard = _guard_admin(request)
    if guard:
        return guard
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        db.delete(user)
        db.commit()
    return RedirectResponse(url="/setup?msg=Менеджер удалён", status_code=303)


@app.get("/", response_class=HTMLResponse)
def root():
    return RedirectResponse(url="/admin", status_code=303)


@app.get("/admin", response_class=HTMLResponse)
def admin_leads(request: Request, msg: str = "", db: Session = Depends(get_db)):
    guard = _guard_login(request)
    if guard:
        return guard
    leads = db.query(Lead).order_by(Lead.created_at.desc()).all()
    return HTMLResponse(admin_pages.leads_list(leads, _role(request), message=msg))


@app.get("/admin/leads/{lead_id}", response_class=HTMLResponse)
def admin_lead_detail(lead_id: int, request: Request, msg: str = "", db: Session = Depends(get_db)):
    guard = _guard_login(request)
    if guard:
        return guard
    lead = _get_lead_or_404(db, lead_id)
    logs = db.query(EmailLog).filter(EmailLog.lead_id == lead.id).order_by(EmailLog.created_at).all()
    replies = db.query(Reply).filter(Reply.lead_id == lead.id).order_by(Reply.received_at).all()
    sent = sent_events(db, lead)
    return HTMLResponse(
        admin_pages.lead_detail(
            lead, sent, logs, replies, settings.schedule_interval_days,
            _role(request), message=msg,
        )
    )


@app.post("/admin/leads/{lead_id}/update", response_class=HTMLResponse)
def admin_lead_update(
    lead_id: int,
    request: Request,
    cyber_problem: str = Form(""),
    db: Session = Depends(get_db),
):
    guard = _guard_login(request)
    if guard:
        return guard
    lead = _get_lead_or_404(db, lead_id)
    lead.cyber_problem = cyber_problem.strip()
    db.commit()
    return RedirectResponse(url=f"/admin/leads/{lead_id}?msg=Сохранено", status_code=303)


@app.post("/admin/leads/{lead_id}/send", response_class=HTMLResponse)
def admin_lead_send(
    lead_id: int,
    request: Request,
    event: str = Form(""),
    db: Session = Depends(get_db),
):
    guard = _guard_login(request)
    if guard:
        return guard
    lead = _get_lead_or_404(db, lead_id)

    sent = sent_events(db, lead)
    if event not in chain.available_events(sent):
        return RedirectResponse(url=f"/admin/leads/{lead_id}?msg=Это письмо сейчас недоступно", status_code=303)

    if event == "lead_approved" and lead.status != "approved":
        lead.status = "approved"
        lead.approved_at = utcnow()
        db.commit()
        db.refresh(lead)

    log = notification_service.send_event(db, lead, event)

    if lead.auto_active and event in chain.SCHEDULED:
        lead.next_send_at = utcnow() + timedelta(days=settings.schedule_interval_days)
        db.commit()

    msg = "Письмо отправлено" if log.status == "sent" else f"Ошибка: {log.error}"
    return RedirectResponse(url=f"/admin/leads/{lead_id}?msg={msg}", status_code=303)


@app.post("/admin/leads/{lead_id}/auto", response_class=HTMLResponse)
def admin_lead_auto(
    lead_id: int,
    request: Request,
    action: str = Form(""),
    db: Session = Depends(get_db),
):
    guard = _guard_login(request)
    if guard:
        return guard
    lead = _get_lead_or_404(db, lead_id)

    if action == "start":
        sent = sent_events(db, lead)
        if "check_started" in sent and chain.next_scheduled(sent) is not None:
            lead.auto_active = True
            lead.next_send_at = utcnow() + timedelta(days=settings.schedule_interval_days)
    else:
        lead.auto_active = False
        lead.next_send_at = None
    db.commit()
    return RedirectResponse(url=f"/admin/leads/{lead_id}", status_code=303)


@app.get("/admin/leads/{lead_id}/preview/{event}", response_class=HTMLResponse)
def admin_lead_preview(lead_id: int, event: str, request: Request, db: Session = Depends(get_db)):
    guard = _guard_login(request)
    if guard:
        return guard
    if event not in chain.SUBJECTS:
        raise HTTPException(status_code=404, detail="Письмо не найдено")
    lead = _get_lead_or_404(db, lead_id)
    _subject, html = templates.render(event, lead)
    return HTMLResponse(html)
