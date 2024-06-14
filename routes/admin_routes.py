import logging
from flask import Blueprint, render_template, abort, flash, redirect, url_for, request, current_app as app
from functools import wraps
from flask_login import current_user, login_required
from flask_mail import Message
from datetime import datetime, timedelta
from models.log import ActivityLog
from models.user import User
from models.feedback import Feedback  # Import Feedback model
from config import db, mail
from utils.logging_config import log_activity

logger = logging.getLogger(__name__)

# Create the admin blueprint
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def init_app(app):
    app.register_blueprint(admin_bp)

# Define admin_required decorator before using it
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def ensure_admin():
    if not current_user.is_admin:
        abort(403)

@admin_bp.route('/', methods=['GET', 'POST'])
@login_required
def admin_dashboard():
    ensure_admin()
    logs = ActivityLog.query.order_by(ActivityLog.timestamp.desc()).all()
    return render_template('admin/admin.html', logs=logs)

@admin_bp.route('/adjust_user', methods=['POST'])
@login_required
def adjust_user():
    ensure_admin()
    return perform_user_adjustment()

@admin_bp.route('/view_users', methods=['GET'])
@login_required
def view_users():
    ensure_admin()
    users = User.query.all()
    current_time = datetime.utcnow()  # Get the current time in UTC
    return render_template('admin/view_users.html', users=users, current_time=current_time)

@admin_bp.route('/approve_user/<int:user_id>', methods=['POST'])
@login_required
def approve_user_by_id(user_id):
    ensure_admin()
    return toggle_user_approval(user_id, True)

@admin_bp.route('/disallow_user/<int:user_id>', methods=['POST'])
@login_required
def disallow_user(user_id):
    ensure_admin()
    return toggle_user_approval(user_id, False)

@admin_bp.route('/delete_user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    ensure_admin()
    return perform_user_deletion(user_id)

@admin_bp.route('/logs', methods=['GET'])
@login_required
def view_logs():
    ensure_admin()
    logs = ActivityLog.query.order_by(ActivityLog.timestamp.desc()).all()
    return render_template('admin/logs.html', logs=logs)

@admin_bp.route('/approve_user_by_username/<username>', methods=['POST'])
@login_required
def approve_user_by_username(username):
    ensure_admin()
    return approve_user_with_username(username)

# Add the new route to view feedback
@admin_bp.route('/view_feedback', methods=['GET'])
@login_required
@admin_required
def view_feedback():
    feedback_list = Feedback.query.all()
    return render_template('admin/view_feedback.html', feedback_list=feedback_list)

def perform_user_adjustment():
    username = request.form.get('username')
    tokens = request.form.get('tokens')
    days = request.form.get('days')

    user = User.query.filter_by(username=username).first()
    if not user:
        flash('User not found', 'danger')
        return redirect(url_for('admin.admin_dashboard'))

    try:
        if tokens:
            user.tokens = int(tokens)
        if days:
            user.token_expiry_date = datetime.utcnow() + timedelta(days=int(days))
        db.session.commit()
        flash('User attributes adjusted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f"An error occurred: {str(e)}", 'danger')
    
    return redirect(url_for('admin.admin_dashboard'))

def toggle_user_approval(user_id, approve=True):
    user = User.query.get(user_id)
    if not user:
        flash('User not found', 'danger')
        return redirect(url_for('admin_dashboard'))

    user.is_approved = approve
    db.session.commit()

    if approve:
        # Send approval email
        send_approval_email(user.email)
        # Capture the action
        ip_address = request.remote_addr
        user_agent = request.user_agent.string
        log_activity(current_user.id, "Approved account", f"Approved account for user {user.username}", ip_address=ip_address, user_agent=user_agent)
        flash('User approved successfully', 'success')
    else:
        log_activity(current_user.id, "Disallowed account", f"Disallowed account for user {user.username}", ip_address=request.remote_addr, user_agent=request.user_agent.string)
        flash('User disallowed successfully', 'success')

    return redirect(url_for('view_users'))

def perform_user_deletion(user_id):
    user = User.query.get(user_id)
    if not user:
        flash('User not found', 'danger')
        return redirect(url_for('admin_dashboard'))

    try:
        db.session.delete(user)
        db.session.commit()
        log_activity(current_user.id, "Deleted account", f"Deleted account for user {user.username}", ip_address=request.remote_addr, user_agent=request.user_agent.string)
        flash('User deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f"An error occurred: {str(e)}", 'danger')

    return redirect(url_for('view_users'))

def approve_user_with_username(username):
    user_to_approve = User.query.filter_by(username=username).first()
    
    if not user_to_approve:
        flash('User not found.', 'error')
        return redirect(url_for('view_users'))
    
    user_to_approve.is_approved = True
    db.session.commit()

    send_approval_email(user_to_approve.email)
    
    flash(f'User {username} has been approved and notified!', 'success')
    return redirect(url_for('view_users'))

def send_approval_email(recipient):
    msg = Message(app.config['MAIL_SUBJECT'], 
                  sender=app.config['MAIL_SENDER'],
                  recipients=[recipient])
    msg.body = app.config['MAIL_BODY'].format(url="https://ielts-bxsh.onrender.com/")
    
    try:
        mail.send(msg)
    except Exception as e:
        logger.error(f"Error sending approval mail: {e}")
        flash('Failed to send approval email.', 'error')
