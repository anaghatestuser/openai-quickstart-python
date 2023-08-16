from flask import render_template, abort, flash, redirect, url_for, request
from flask_login import current_user, login_required
from datetime import datetime, timedelta
from models.log import ActivityLog
from models.user import User
from config import db

def init_app(app):

    @app.route('/admin/', methods=['GET', 'POST'])
    @login_required  
    def admin_dashboard():
        # Ensure the user is an admin
        if not current_user.is_admin:
            abort(403)
        return render_template('admin/admin.html')

    @app.route('/admin/adjust_user', methods=['POST'])
    @login_required  
    def adjust_user():
        # Ensure the user is an admin
        if not current_user.is_admin:
            abort(403)
        
        # Extract the form data
        username = request.form.get('username')
        tokens = request.form.get('tokens')
        days = request.form.get('days')

        # Find the user by username
        user = User.query.filter_by(username=username).first()
        if not user:
            flash('User not found', 'danger')
            return redirect(url_for('admin_dashboard'))

        # Adjust tokens and expiry date if provided
        try:
            if tokens:
                user.tokens = int(tokens)
            if days:
                user.token_expiry_date = datetime.utcnow() + timedelta(days=int(days))
            
            # Save changes to the database
            db.session.commit()
            flash('User attributes adjusted successfully', 'success')
            return redirect(url_for('admin_dashboard'))
        
        except Exception as e:
            db.session.rollback()
            flash(f"An error occurred: {str(e)}", 'danger')
            return redirect(url_for('admin_dashboard'))

    @app.route('/admin/view_users', methods=['GET'])
    @login_required  
    def view_users():
        # Ensure the user is an admin
        if not current_user.is_admin:
            abort(403)

        users = User.query.all()
        return render_template('admin/view_users.html', users=users)

    @app.route('/admin/approve_user/<int:user_id>', methods=['POST'])
    @login_required  
    def approve_user(user_id):
        if not current_user.is_admin:
            abort(403)

        user = User.query.get(user_id)
        if not user:
            flash('User not found', 'danger')
            return redirect(url_for('admin_dashboard'))

        user.is_approved = True
        db.session.commit()

        # Capturing IP address and user agent
        ip_address = request.remote_addr
        user_agent = request.user_agent.string

        # Log the action
        log_activity(current_user.id, "Approved account", f"Approved account for user {user.username}", ip_address=ip_address, user_agent=user_agent)

        flash('User approved successfully', 'success')
        return redirect(url_for('view_users'))


    @app.route('/admin/disallow_user/<int:user_id>', methods=['POST'])
    @login_required  
    def disallow_user(user_id):
        # Ensure the user is an admin
        if not current_user.is_admin:
            abort(403)

        user = User.query.get(user_id)
        if not user:
            flash('User not found', 'danger')
            return redirect(url_for('admin_dashboard'))

        user.is_approved = False
        db.session.commit()
        flash('User disallowed successfully', 'success')
        return redirect(url_for('view_users'))
    
    @app.route('/admin/logs', methods=['GET'])
    @login_required  
    def view_logs():
        if not current_user.is_admin:
            abort(403)
        logs = ActivityLog.query.order_by(ActivityLog.timestamp.desc()).all()
        return render_template('admin/logs.html', logs=logs)

