# ============================================
# MODELO DE GASTOS
# ============================================

from app import db
from datetime import datetime, date
from sqlalchemy.orm import validates
from flask import render_template



class ExpenseCategory(db.Model):
    __tablename__ = 'expense_categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    color = db.Column(db.String(50), default='bg-blue-100 text-blue-800')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relación con gastos
    expenses = db.relationship('Expense', backref='category_ref', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<ExpenseCategory {self.name}>'

    def to_dict(self):
        """Serializar a diccionario"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'color': self.color,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class Expense(db.Model):
    __tablename__ = 'expenses'

    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(200), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('expense_categories.id'), nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    is_paid = db.Column(db.Boolean, default=False)
    paid_date = db.Column(db.Date)
    is_recurring = db.Column(db.Boolean, default=False)
    frequency = db.Column(db.Enum('daily', 'weekly', 'monthly', 'quarterly', 'yearly', name='expense_frequency'))
    advance_days = db.Column(db.Integer, default=7)
    auto_renew = db.Column(db.Boolean, default=True)
    notes = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # CORREGIDO: 'user.id' no 'users.id'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relación con usuario - CORREGIDO: Usar el nombre correcto del modelo
    creator = db.relationship('User', backref='expenses_created', lazy=True)

    def __repr__(self):
        return f'<Expense {self.description}: ${self.amount}>'

    @property
    def is_overdue(self):
        return not self.is_paid and self.due_date < date.today()

    @property
    def next_due_date(self):
        if not self.is_recurring or not self.frequency:
            return None

        import datetime as dt
        next_date = self.due_date
        today = date.today()

        while next_date <= today:
            if self.frequency == 'daily':
                next_date = self.add_days(next_date, 1)
            elif self.frequency == 'weekly':
                next_date = self.add_days(next_date, 7)
            elif self.frequency == 'monthly':
                next_date = self.add_months(next_date, 1)
            elif self.frequency == 'quarterly':
                next_date = self.add_months(next_date, 3)
            elif self.frequency == 'yearly':
                next_date = self.add_months(next_date, 12)

        return next_date

    @property
    def days_until(self):
        if self.is_paid:
            return 0
        delta = (self.due_date - date.today()).days
        return max(delta, 0)

    @staticmethod
    def add_days(dt, days):
        import datetime as dt_module
        return dt + dt_module.timedelta(days=days)

    @staticmethod
    def add_months(dt, months):
        import datetime as dt_module
        month = dt.month - 1 + months
        year = dt.year + month // 12
        month = month % 12 + 1
        day = min(dt.day, [31,
                           29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28,
                           31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1])
        return date(year, month, day)

    @validates('amount')
    def validate_amount(self, key, amount):
        if amount <= 0:
            raise ValueError('El monto debe ser mayor a 0')
        return amount

    def to_dict(self):
        """Serializar a diccionario"""
        return {
            'id': self.id,
            'description': self.description,
            'amount': float(self.amount) if self.amount else 0,
            'category_id': self.category_id,
            'category_name': self.category_ref.name if self.category_ref else None,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'is_paid': self.is_paid,
            'paid_date': self.paid_date.isoformat() if self.paid_date else None,
            'is_recurring': self.is_recurring,
            'frequency': self.frequency,
            'advance_days': self.advance_days,
            'auto_renew': self.auto_renew,
            'notes': self.notes,
            'created_by': self.created_by,
            'created_by_name': self.creator.username if self.creator else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_overdue': self.is_overdue,
            'days_until': self.days_until,
            'next_due_date': self.next_due_date.isoformat() if self.next_due_date else None
        }