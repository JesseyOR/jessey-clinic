from flask import Blueprint, render_template, request, flash, redirect, url_for, session, jsonify
from flask_login import login_required, current_user
from database.models import Drug, Sale, SaleItem, Patient, AuditLog
from services.sales_service import SalesService
from services.stock_service import StockService
from database.db import db, Transaction
from datetime import datetime
import uuid

sales_bp = Blueprint('sales', __name__)

@sales_bp.route('/checkout')
@login_required
def checkout():
    cart = session.get('cart', {})
    items = []
    total = 0
    for drug_id_str, qty in cart.items():
        drug = Drug.query.get(int(drug_id_str))
        if drug:
            subtotal = drug.selling_price * qty
            total += subtotal
            items.append({'drug': drug, 'quantity': qty, 'subtotal': subtotal})
    patients = Patient.query.all()
    return render_template('sales/quick_checkout.html', items=items, total=total, patients=patients)

@sales_bp.route('/cart')
@login_required
def view_cart():
    cart = session.get('cart', {})
    items = []
    subtotal = 0
    for drug_id_str, qty in cart.items():
        drug = Drug.query.get(int(drug_id_str))
        if drug:
            item_total = drug.selling_price * qty
            subtotal += item_total
            items.append({'drug': drug, 'quantity': qty, 'subtotal': item_total})
    tax = subtotal * 0.10
    total = subtotal + tax
    patients = Patient.query.all()
    return render_template('sales/cart.html', 
                         items=items, 
                         subtotal=subtotal, 
                         tax=tax, 
                         total=total,
                         patients=patients)

@sales_bp.route('/add-to-cart', methods=['POST'])
@login_required
def add_to_cart():
    data = request.get_json()
    drug_id = str(data.get('drug_id'))
    quantity = int(data.get('quantity', 1))
    drug = Drug.query.get(int(drug_id))
    if not drug:
        return jsonify({'error': 'Drug not found'}), 404
    if not drug.is_active:
        return jsonify({'error': 'Drug is inactive'}), 400
    if drug.is_expired:
        return jsonify({'error': f'Drug expired on {drug.expiry_date}'}), 400
    if drug.quantity < quantity:
        return jsonify({'error': f'Only {drug.quantity} in stock'}), 400
    cart = session.get('cart', {})
    cart[drug_id] = cart.get(drug_id, 0) + quantity
    session['cart'] = cart
    return jsonify({'success': True, 'cart_count': sum(cart.values())})

@sales_bp.route('/remove-from-cart', methods=['POST'])
@login_required
def remove_from_cart():
    data = request.get_json()
    drug_id = str(data.get('drug_id'))
    cart = session.get('cart', {})
    if drug_id in cart:
        del cart[drug_id]
        session['cart'] = cart
    return jsonify({'success': True})

@sales_bp.route('/remove-one-from-cart', methods=['POST'])
@login_required
def remove_one_from_cart():
    """Decrease quantity by 1, or remove if quantity becomes 0."""
    data = request.get_json()
    drug_id = str(data.get('drug_id'))
    cart = session.get('cart', {})
    if drug_id in cart:
        if cart[drug_id] > 1:
            cart[drug_id] -= 1
        else:
            del cart[drug_id]
        session['cart'] = cart
    return jsonify({'success': True})

@sales_bp.route('/complete-sale', methods=['POST'])
@login_required
def complete_sale():
    cart = session.get('cart', {})
    if not cart:
        flash('Cart is empty', 'warning')
        return redirect(url_for('sales.checkout'))
    
    payment_method = request.form.get('payment_method', 'cash')
    patient_id = request.form.get('patient_id') or None
    discount = float(request.form.get('discount', 0))
    
    try:
        invoice = f"INV-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:4].upper()}"
        with Transaction():
            sale = Sale(current_user.id, invoice, payment_method, patient_id)
            sale.discount = discount
            db.session.add(sale)
            db.session.flush()
            
            for drug_id_str, qty in cart.items():
                drug = Drug.query.get(int(drug_id_str))
                if not drug:
                    raise ValueError(f"Drug {drug_id_str} not found")
                if drug.quantity < qty:
                    raise ValueError(f"Insufficient stock for {drug.name}")
                if drug.is_expired:
                    raise ValueError(f"Cannot sell expired drug: {drug.name}")
                
                # Check prescription if required
                if drug.requires_prescription and patient_id:
                    from database.models import Prescription
                    valid_rx = Prescription.query.filter(
                        Prescription.patient_id == patient_id,
                        Prescription.drug_id == drug.id,
                        Prescription.expiry_date >= datetime.now().date()
                    ).first()
                    if not valid_rx:
                        raise ValueError(f"Valid prescription required for {drug.name}")
                elif drug.requires_prescription:
                    raise ValueError(f"Prescription required for {drug.name}. Please attach patient.")
                
                item = SaleItem(drug, qty)
                sale.items.append(item)
                drug.deduct_stock(qty)
                db.session.add(drug)
            
            from flask import current_app
            sale.calculate_totals(current_app.config['TAX_RATE'])
            db.session.add(sale)
            audit = AuditLog(
                current_user.id,
                'SALE_COMPLETED',
                f"Invoice {invoice} total ${sale.total:.2f}",
                request.remote_addr
            )
            db.session.add(audit)
        
        session.pop('cart', None)
        flash(f'Sale complete! Invoice: {invoice}', 'success')
        return jsonify({'success': True, 'invoice': invoice})
    
    except Exception as e:
        flash(f'Sale failed: {str(e)}', 'danger')
        return jsonify({'error': str(e)}), 400

@sales_bp.route('/receipt/<invoice>')
@login_required
def receipt(invoice):
    sale = Sale.query.filter_by(invoice_number=invoice).first_or_404()
    # Ensure user has permission (admin or own sale)
    if current_user.role != 'admin' and sale.cashier_id != current_user.id:
        flash('Access denied', 'danger')
        return redirect(url_for('sales.sales_history'))
    return render_template('sales/receipt.html', sale=sale)

@sales_bp.route('/history')
@login_required
def sales_history():
    if current_user.role == 'admin':
        sales = Sale.query.order_by(Sale.created_at.desc()).limit(100).all()
    else:
        sales = Sale.query.filter_by(cashier_id=current_user.id).order_by(Sale.created_at.desc()).limit(100).all()
    return render_template('sales/sales_history.html', sales=sales)

@sales_bp.route('/cart-data', methods=['GET'])
@login_required
def cart_data():
    cart = session.get('cart', {})
    return jsonify({'cart': cart})