from flask import Flask, render_template, redirect
from flask_migrate import Migrate 
from config import ActiveConfig
from database.db import init_db, db
import logging
import sys

def create_app():
    app = Flask(__name__)
    app.config.from_object(ActiveConfig)
    ActiveConfig.init_app(app)

    # Initialize database and migrations
    init_db(app)
    Migrate(app, db)

    # Logging for production
    if not app.debug:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.INFO)
        app.logger.addHandler(handler)

    # ✅ Register only the necessary blueprints (NO auth_bp)
    from routes.dashboard_routes import dashboard_bp
    from routes.stock_routes import stock_bp
    from routes.sales_routes import sales_bp
    from routes.report_routes import report_bp
    from routes.supplier_routes import supplier_bp
    from routes.prescription_routes import prescription_bp
    from routes.branch_routes import branch_bp
    from routes.audit_routes import audit_bp
    from routes.api.mobile_api import mobile_api_bp

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

    # ✅ Direct open access – no login, no user checks
    @app.route('/')
    def index():
        # Make sure 'dashboard.admin_dashboard' exists.
        # If not, change to a known good route, e.g. 'dashboard.index'
        return redirect('/dashboard')

    @app.context_processor
    def inject_now():
        from datetime import datetime
        return {'now': datetime.now()}

    return app

app = create_app()

if __name__ == "__main__":
    app.run()
