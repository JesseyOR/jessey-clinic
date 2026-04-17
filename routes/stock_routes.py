from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from database.models import Drug, Supplier, AuditLog
from services.stock_service import StockService
from database.db import db, Transaction
from datetime import datetime

stock_bp = Blueprint('stock', __name__)

@stock_bp.route('/')
@login_required
def list_stock():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    category = request.args.get('category', '')
    
    query = Drug.query.filter_by(is_active=True)
    if search:
        query = query.filter(
            Drug.name.contains(search) | 
            Drug.generic_name.contains(search) | 
            Drug.barcode.contains(search)
        )
    if category:
        query = query.filter_by(category=category)
    
    drugs = query.order_by(Drug.name).paginate(page=page, per_page=20, error_out=False)
    
    # Get distinct categories for filter
    categories = db.session.query(Drug.category).distinct().all()
    categories = [c[0] for c in categories if c[0]]
    
    return render_template('stock/current_stock.html', drugs=drugs, search=search, 
                         category=category, categories=categories)

@stock_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_drug():
    if current_user.role not in ['admin', 'pharmacist']:
        flash('Permission denied. Only admin or pharmacist can add drugs.', 'danger')
        return redirect(url_for('stock.list_stock'))
    
    suppliers = Supplier.query.all()
    
    if request.method == 'POST':
        try:
            name = request.form.get('name', '').strip()
            generic_name = request.form.get('generic_name', '').strip() or None
            category = request.form.get('category', '').strip() or None
            barcode = request.form.get('barcode', '').strip() or None
            quantity = int(request.form.get('quantity', 0))
            buying_price = float(request.form.get('buying_price', 0))
            selling_price = float(request.form.get('selling_price', 0))
            expiry_date_str = request.form.get('expiry_date', '')
            reorder_level = int(request.form.get('reorder_level', 20))
            supplier_id = request.form.get('supplier_id')
            requires_prescription = 'requires_prescription' in request.form
            batch_number = request.form.get('batch_number', '').strip() or None
            manufactured_date_str = request.form.get('manufactured_date', '')
            
            # Validation
            if not name:
                flash('Drug name is required.', 'danger')
                return render_template('stock/add_drug.html', suppliers=suppliers)
            if selling_price <= 0:
                flash('Selling price must be greater than zero.', 'danger')
                return render_template('stock/add_drug.html', suppliers=suppliers)
            if not expiry_date_str:
                flash('Expiry date is required.', 'danger')
                return render_template('stock/add_drug.html', suppliers=suppliers)
            
            expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%d').date()
            if expiry_date < datetime.now().date():
                flash('Expiry date cannot be in the past.', 'danger')
                return render_template('stock/add_drug.html', suppliers=suppliers)
            
            manufactured_date = None
            if manufactured_date_str:
                manufactured_date = datetime.strptime(manufactured_date_str, '%Y-%m-%d').date()
            
            with Transaction():
                drug = Drug(
                    name=name,
                    generic_name=generic_name,
                    category=category,
                    barcode=barcode,
                    quantity=quantity,
                    buying_price=buying_price,
                    selling_price=selling_price,
                    expiry_date=expiry_date,
                    reorder_level=reorder_level,
                    supplier_id=int(supplier_id) if supplier_id and supplier_id.isdigit() else None,
                    requires_prescription=requires_prescription,
                    batch_number=batch_number,
                    manufactured_date=manufactured_date
                )
                db.session.add(drug)
                db.session.flush()
                
                audit = AuditLog(
                    user_id=current_user.id,
                    action='DRUG_ADDED',
                    details=f"Added drug {name} (ID:{drug.id}) with stock {quantity}",
                    ip_address=request.remote_addr
                )
                db.session.add(audit)
            
            flash(f'Drug "{name}" added successfully.', 'success')
            return redirect(url_for('stock.list_stock'))
            
        except ValueError as e:
            flash(f'Validation error: {str(e)}', 'danger')
        except Exception as e:
            flash(f'Error adding drug: {str(e)}', 'danger')
    
    return render_template('stock/add_drug.html', suppliers=suppliers)

@stock_bp.route('/edit/<int:drug_id>', methods=['GET', 'POST'])
@login_required
def edit_drug(drug_id):
    if current_user.role not in ['admin', 'pharmacist']:
        flash('Access denied.', 'danger')
        return redirect(url_for('stock.list_stock'))
    
    drug = Drug.query.get_or_404(drug_id)
    suppliers = Supplier.query.all()
    
    if request.method == 'POST':
        try:
            drug.name = request.form.get('name', '').strip()
            drug.generic_name = request.form.get('generic_name', '').strip() or None
            drug.category = request.form.get('category', '').strip() or None
            drug.barcode = request.form.get('barcode', '').strip() or None
            drug.buying_price = float(request.form.get('buying_price', 0))
            drug.selling_price = float(request.form.get('selling_price', 0))
            drug.reorder_level = int(request.form.get('reorder_level', 20))
            drug.supplier_id = int(request.form.get('supplier_id')) if request.form.get('supplier_id') and request.form.get('supplier_id').isdigit() else None
            drug.requires_prescription = 'requires_prescription' in request.form
            drug.batch_number = request.form.get('batch_number', '').strip() or None
            
            expiry_date_str = request.form.get('expiry_date', '')
            if expiry_date_str:
                drug.expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%d').date()
                if drug.expiry_date < datetime.now().date():
                    flash('Expiry date cannot be in the past.', 'danger')
                    return render_template('stock/edit.html', drug=drug, suppliers=suppliers)
            
            manufactured_date_str = request.form.get('manufactured_date', '')
            if manufactured_date_str:
                drug.manufactured_date = datetime.strptime(manufactured_date_str, '%Y-%m-%d').date()
            else:
                drug.manufactured_date = None
            
            with Transaction():
                db.session.add(drug)
                audit = AuditLog(
                    user_id=current_user.id,
                    action='DRUG_EDITED',
                    details=f"Edited drug {drug.name} (ID:{drug.id})",
                    ip_address=request.remote_addr
                )
                db.session.add(audit)
            
            flash('Drug updated successfully.', 'success')
            return redirect(url_for('stock.list_stock'))
            
        except ValueError as e:
            flash(f'Error: {str(e)}', 'danger')
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')
    
    return render_template('stock/edit.html', drug=drug, suppliers=suppliers)

@stock_bp.route('/low-stock')
@login_required
def low_stock():
    drugs = StockService.get_low_stock_items()
    suppliers = Supplier.query.all()
    return render_template('stock/low_stock_alerts.html', drugs=drugs, suppliers=suppliers)

@stock_bp.route('/expiring-soon')
@login_required
def expiring_soon():
    drugs = StockService.get_expiring_soon_items()
    expired = StockService.get_expired_items()
    return render_template('stock/expiring_soon.html', drugs=drugs, expired=expired)

@stock_bp.route('/adjust/<int:drug_id>', methods=['POST'])
@login_required
def adjust_stock(drug_id):
    if current_user.role not in ['admin', 'pharmacist']:
        return jsonify({'error': 'Permission denied'}), 403
    
    data = request.get_json()
    adjustment = data.get('adjustment', 0)
    supplier_id = data.get('supplier_id')
    reason = data.get('reason', 'MANUAL_ADJUST')
    
    try:
        if adjustment > 0:
            # Adding stock
            StockService.add_stock(drug_id, adjustment, current_user.id, supplier_id, reason=reason)
        elif adjustment < 0:
            # Deducting stock (if large negative, treat as dispose all)
            drug = Drug.query.get(drug_id)
            if drug and -adjustment >= drug.quantity:
                # Dispose all
                StockService.deduct_stock(drug_id, drug.quantity, current_user.id, reason='DISPOSAL')
            else:
                StockService.deduct_stock(drug_id, -adjustment, current_user.id, reason=reason)
        
        drug = Drug.query.get(drug_id)
        return jsonify({'success': True, 'new_quantity': drug.quantity})
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@stock_bp.route('/update-price/<int:drug_id>', methods=['POST'])
@login_required
def update_price(drug_id):
    """Update selling price of a drug (for markdowns)."""
    if current_user.role not in ['admin', 'pharmacist']:
        return jsonify({'error': 'Permission denied'}), 403
    
    data = request.get_json()
    new_price = data.get('selling_price')
    
    if new_price is None or new_price <= 0:
        return jsonify({'error': 'Invalid price. Must be greater than zero.'}), 400
    
    with Transaction():
        drug = Drug.query.get_or_404(drug_id)
        old_price = drug.selling_price
        drug.selling_price = float(new_price)
        db.session.add(drug)
        
        audit = AuditLog(
            user_id=current_user.id,
            action='PRICE_UPDATED',
            details=f"Updated {drug.name} price from ${old_price:.2f} to ${new_price:.2f}",
            ip_address=request.remote_addr
        )
        db.session.add(audit)
    
    return jsonify({'success': True, 'new_price': drug.selling_price})

@stock_bp.route('/alerts-data', methods=['GET'])
@login_required
def alerts_data():
    """Return JSON with low stock and expiring counts for real-time updates."""
    low_stock_count = len(StockService.get_low_stock_items())
    expiring_count = len(StockService.get_expiring_soon_items())
    return jsonify({
        'low_stock_count': low_stock_count,
        'expiring_count': expiring_count
    })

@stock_bp.route('/low-stock-count', methods=['GET'])
@login_required
def low_stock_count():
    count = len(StockService.get_low_stock_items())
    return jsonify({'count': count})