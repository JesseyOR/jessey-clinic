from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from database.models import Supplier, Drug, AuditLog
from database.db import db, Transaction

supplier_bp = Blueprint('suppliers', __name__)

@supplier_bp.route('/')
@login_required
def list_suppliers():
    suppliers = Supplier.query.all()
    return render_template('suppliers/supplier_list.html', suppliers=suppliers)

@supplier_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_supplier():
    if current_user.role not in ['admin', 'pharmacist']:
        flash('Permission denied', 'danger')
        return redirect(url_for('suppliers.list_suppliers'))
    if request.method == 'POST':
        try:
            with Transaction():
                supplier = Supplier(
                    name=request.form['name'].strip(),
                    contact_person=request.form.get('contact_person'),
                    phone=request.form.get('phone'),
                    email=request.form.get('email'),
                    address=request.form.get('address')
                )
                db.session.add(supplier)
                audit = AuditLog(
                    current_user.id,
                    'SUPPLIER_ADDED',
                    f"Added supplier {supplier.name}",
                    request.remote_addr
                )
                db.session.add(audit)
            flash('Supplier added successfully', 'success')
            return redirect(url_for('suppliers.list_suppliers'))
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')
    return render_template('suppliers/add_supplier.html')