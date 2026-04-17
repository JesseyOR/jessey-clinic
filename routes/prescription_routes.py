from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from database.models import Prescription, Patient, Drug, Sale
from database.db import db, Transaction

prescription_bp = Blueprint('prescriptions', __name__)

@prescription_bp.route('/attach', methods=['GET', 'POST'])
@login_required
def attach():
    patients = Patient.query.all()
    drugs = Drug.query.filter_by(is_active=True).all()
    if request.method == 'POST':
        try:
            patient_id = request.form['patient_id']
            drug_id = request.form['drug_id']
            doctor_name = request.form.get('doctor_name')
            expiry_date_str = request.form.get('expiry_date')
            expiry_date = None
            if expiry_date_str:
                from datetime import datetime
                expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%d').date()
            with Transaction():
                rx = Prescription(
                    patient_id=patient_id,
                    drug_id=drug_id,
                    doctor_name=doctor_name,
                    expiry_date=expiry_date
                )
                db.session.add(rx)
            flash('Prescription attached successfully', 'success')
            return redirect(url_for('prescriptions.patient_history', patient_id=patient_id))
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')
    return render_template('prescriptions/attach_prescription.html', patients=patients, drugs=drugs)

@prescription_bp.route('/patient/<int:patient_id>')
@login_required
def patient_history(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    prescriptions = Prescription.query.filter_by(patient_id=patient_id).all()
    sales = Sale.query.filter_by(patient_id=patient_id).all()
    return render_template('prescriptions/patient_history.html', patient=patient, prescriptions=prescriptions, sales=sales)

@prescription_bp.route('/patient/profile/<int:patient_id>')
@login_required
def patient_profile(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    return render_template('prescriptions/patient_profile.html', patient=patient)