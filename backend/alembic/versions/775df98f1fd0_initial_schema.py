"""Начальная схема: лиды, письма, ответы, пользователи

Revision ID: 775df98f1fd0
Revises: 
Create Date: 2026-09-02 15:57:51.326041

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '775df98f1fd0'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('email_logs',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('lead_id', sa.Integer(), nullable=False),
    sa.Column('event', sa.String(length=60), nullable=False),
    sa.Column('subject', sa.String(length=300), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('error', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_email_logs_lead_id'), 'email_logs', ['lead_id'], unique=False)
    op.create_table('leads',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('phone', sa.String(length=30), nullable=False),
    sa.Column('email', sa.String(length=200), nullable=False),
    sa.Column('inn', sa.String(length=12), nullable=True),
    sa.Column('segment', sa.String(length=120), nullable=True),
    sa.Column('cyber_problem', sa.String(length=300), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('auto_active', sa.Boolean(), nullable=False),
    sa.Column('next_send_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('replies',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('lead_id', sa.Integer(), nullable=False),
    sa.Column('from_email', sa.String(length=200), nullable=True),
    sa.Column('subject', sa.String(length=300), nullable=True),
    sa.Column('body', sa.Text(), nullable=True),
    sa.Column('message_id', sa.String(length=300), nullable=True),
    sa.Column('received_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('message_id')
    )
    op.create_index(op.f('ix_replies_lead_id'), 'replies', ['lead_id'], unique=False)
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('login', sa.String(length=80), nullable=False),
    sa.Column('password_hash', sa.String(length=200), nullable=False),
    sa.Column('role', sa.String(length=20), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('login')
    )


def downgrade() -> None:
    op.drop_table('users')
    op.drop_index(op.f('ix_replies_lead_id'), table_name='replies')
    op.drop_table('replies')
    op.drop_table('leads')
    op.drop_index(op.f('ix_email_logs_lead_id'), table_name='email_logs')
    op.drop_table('email_logs')
