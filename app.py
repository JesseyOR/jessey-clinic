from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, login_required, current_user
from flask_migrate import Migrate 
from config import ActiveConfig
from database.db import init_db, db
from database.models import User, AuditLog
import logging
import sys

def create_app():
    app = Flask(__name__)
    app.config.from_object(ActiveConfig)
    ActiveConfig.init_app(app)

    # Initialize database and migrations
    init_db(app)
    Migrate(app, db)

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = "Please log in to access this page."

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Logging for production
    if not app.debug:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.INFO)
        app.logger.addHandler(handler)

    # Register blueprints
    from routes.auth_routes import auth_bp
    from routes.dashboard_routes import dashboard_bp
    from routes.stock_routes import stock_bp
    from routes.sales_routes import sales_bp
    from routes.report_routes import report_bp
    from routes.supplier_routes import supplier_bp
    from routes.prescription_routes import prescription_bp
    from routes.branch_routes import branch_bp
    from routes.audit_routes import audit_bp
    from routes.api.mobile_api import mobile_api_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(stock_bp, url_prefix='/stock')
    app.register_blueprint(sales_bp, url_prefix='/sales')
    app.register_blueprint(report_bp, url_prefix='/reports')
    app.register_blueprint(supplier_bp, url_prefix='/suppliers')
    app.register_blueprint(prescription_bp, url_prefix='/prescriptions')
    app.register_blueprint(branch_bp, url_prefix='/branches')
    app.register_blueprint(audit_bp, url_prefix='/audit')
    app.register_blueprint(mobile_api_bp)

    # Error handlers
    @app.errorhandler(404)
    def not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403

    @app.errorhandler(500)
    def internal_error(e):
        db.session.rollback()
        return render_template('errors/500.html'), 500

    @app.route('/')
    @login_required
    def index():
        if current_user.role == 'admin':
            return redirect(url_for('dashboard.admin_dashboard'))
        elif current_user.role == 'pharmacist':
            return redirect(url_for('dashboard.pharmacist_dashboard'))
        else:
            return redirect(url_for('dashboard.cashier_dashboard'))

    @app.context_processor
    def inject_now():
        from datetime import datetime
        return {'now': datetime.now()}

    return app

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=app.config['DEBUG'])