from flask import render_template, abort, flash, redirect, url_for, request
from flask_login import current_user, login_required
from flask_mail import Message
from datetime import datetime, timedelta
from models.log import ActivityLog
from models.user import User
from config import db, mail, MAIL_SENDER, MAIL_SUBJECT, MAIL_BODY
from utils.logging_config import log_activity
import logging

logger = logging.getLogger(__name__)

def init_app(app):

    @app.route('/admin/', methods=['GET', 'POST'])
    @login_required  
    def admin_dashboard():
        ensure_admin()
        return render_template('admin/admin.html')

    @app.route('/admin/adjust_user', methods=['POST'])
    @login_required  
    def adjust_user():
        ensure_admin()
        return perform_user_adjustment()

    @app.route('/admin/view_users', methods=['GET'])
    @login_required  
    def view_users():
        ensure_admin()
        users = User.query.all()
        return render_template('admin/view_users.html', users=users)

    @app.route('/admin/approve_user/<int:user_id>', methods=['POST'])
    @login_required  
    def approve_user_by_id(user_id):
        ensure_admin()
        return toggle_user_approval(user_id, True)

    @app.route('/admin/disallow_user/<int:user_id>', methods=['POST'])
    @login_required  
    def disallow_user(user_id):
        ensure_admin()
        return toggle_user_approval(user_id, False)

    @app.route('/admin/delete_user/<int:user_id>', methods=['POST'])
    @login_required  
    def delete_user(user_id):
        ensure_admin()
        return perform_user_deletion(user_id)

    @app.route('/admin/logs', methods=['GET'])
    @login_required  
    def view_logs():
        ensure_admin()
        logs = ActivityLog.query.order_by(ActivityLog.timestamp.desc()).all()
        return render_template('admin/logs.html', logs=logs)

    @app.route('/admin/approve_user_by_username/<username>', methods=['POST'])
    @login_required
    def approve_user_by_username(username):
        ensure_admin()
        return approve_user_with_username(username)


def ensure_admin():
    if not current_user.is_admin:
        abort(403)


def perform_user_adjustment():
    username = request.form.get('username')
    tokens = request.form.get('tokens')
    days = request.form.get('days')

    user = User.query.filter_by(username=username).first()
    if not user:
        flash('User not found', 'danger')
        return redirect(url_for('admin_dashboard'))

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
    
    return redirect(url_for('admin_dashboard'))


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
    msg = Message(MAIL_SUBJECT, 
                  sender=MAIL_SENDER,
                  recipients=[recipient])
    msg.body = MAIL_BODY.format(url="https://ielts-bxsh.onrender.com/")
    
    try:
        mail.send(msg)
    except Exception as e:
        logger.error(f"Error sending approval mail: {e}")
        flash('Failed to send approval email.', 'error')
