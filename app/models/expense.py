from app import db
from datetime import datetime, date
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import func


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
    frequency = db.Column(db.String(20))  # monthly, weekly, daily, yearly
    advance_days = db.Column(db.Integer, default=7)
    auto_renew = db.Column(db.Boolean, default=False)
    notes = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    category_ref = db.relationship('ExpenseCategory', backref='expenses', lazy='joined')
    creator = db.relationship('User', backref='expenses', lazy='joined')

    @hybrid_property
    def is_overdue(self):
        if self.is_paid:
            return False
        return self.due_date < date.today()

    @hybrid_property
    def days_until(self):
        if self.is_paid:
            return 0
        delta = self.due_date - date.today()
        return delta.days

    @hybrid_property
    def next_due_date(self):
        if not self.is_recurring or not self.due_date:
            return None

        next_date = self.due_date
        today = date.today()

        while next_date <= today:
            if self.frequency == 'daily':
                next_date = next_date.replace(day=next_date.day + 1)
            elif self.frequency == 'weekly':
                next_date = next_date.replace(day=next_date.day + 7)
            elif self.frequency == 'monthly':
                # Avanzar un mes
                if next_date.month == 12:
                    next_date = next_date.replace(year=next_date.year + 1, month=1)
                else:
                    next_date = next_date.replace(month=next_date.month + 1)
            elif self.frequency == 'yearly':
                next_date = next_date.replace(year=next_date.year + 1)
            else:
                break

        return next_date

    def __repr__(self):
        return f'<Expense {self.id}: {self.description}>'

    def to_dict(self):
        """Serializar a diccionario para APIs"""
        return {
            'id': self.id,
            'description': self.description,
            'amount': float(self.amount) if self.amount else 0,
            'category_id': self.category_id,
            'category': {
                'id': self.category_ref.id if self.category_ref else None,
                'name': self.category_ref.name if self.category_ref else None,
                'color': self.category_ref.color if self.category_ref else None
            },
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
            'next_due_date': self.next_due_date.isoformat() if self.next_due_date else None,
            'status': 'paid' if self.is_paid else ('overdue' if self.is_overdue else 'pending')
        }


class ExpenseCategory(db.Model):
    __tablename__ = 'expense_categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    color = db.Column(db.String(50))  # Para UI styling
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<ExpenseCategory {self.id}: {self.name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'color': self.color,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }