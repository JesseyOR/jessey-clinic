from flask import render_template, jsonify, request
from database.db import db
import logging
import traceback

logger = logging.getLogger(__name__)

def register_error_handlers(app):
    """
    Register global error handlers for the Flask app.
    """
    @app.errorhandler(400)
    def bad_request(e):
        logger.warning(f"400 error: {e}")
        if request.is_json:
            return jsonify({'error': 'Bad request', 'message': str(e)}), 400
        return render_template('errors/400.html'), 400
    
    @app.errorhandler(403)
    def forbidden(e):
        logger.warning(f"403 error: {e} from {request.remote_addr}")
        if request.is_json:
            return jsonify({'error': 'Forbidden', 'message': 'You do not have permission'}), 403
        return render_template('errors/403.html'), 403
    
    @app.errorhandler(404)
    def not_found(e):
        logger.info(f"404 error: {request.path}")
        if request.is_json:
            return jsonify({'error': 'Not found', 'message': 'Resource not found'}), 404
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(e):
        db.session.rollback()
        logger.error(f"500 error: {e}\n{traceback.format_exc()}")
        if request.is_json:
            return jsonify({'error': 'Internal server error', 'message': 'Please contact administrator'}), 500
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(Exception)
    def unhandled_exception(e):
        db.session.rollback()
        logger.critical(f"Unhandled exception: {e}\n{traceback.format_exc()}")
        if request.is_json:
            return jsonify({'error': 'Server error', 'message': str(e)}), 500
        return render_template('errors/500.html'), 500