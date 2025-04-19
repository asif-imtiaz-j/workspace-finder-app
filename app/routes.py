from app.forms import RegistrationForm
from flask import Blueprint, render_template, redirect, url_for, flash, Response
from flask_login import login_user, logout_user, current_user, login_required
from app.models import User, Workspace
from app.forms import LoginForm, WorkspaceForm
from app import db
from io import StringIO
import csv

main = Blueprint('main', __name__)

@main.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    form = RegistrationForm()
    if form.validate_on_submit():
        existing_user = User.query.filter_by(username=form.username.data).first()
        if existing_user:
            flash('Username already exists. Please choose another.', 'danger')
            return redirect(url_for('main.register'))
        user = User(username=form.username.data, role=form.role.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        flash('Account created successfully!', 'success')
        return redirect(url_for('main.dashboard'))
    return render_template('register.html', form=form)

@main.route('/', methods=['GET', 'POST'], endpoint='login')
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect(url_for('main.dashboard'))
        else:
            flash('Login Failed. Check username and password.', 'danger')
    return render_template('login.html', form=form)

@main.route('/dashboard')
@login_required
def dashboard():
    workspaces = Workspace.query.all()
    return render_template('dashboard.html', workspaces=workspaces)

@main.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.login'))

@main.route('/add', methods=['GET', 'POST'])
@login_required
def add_workspace():
    if not current_user.is_admin():
        flash("Access denied: Viewers cannot add workspaces.", "danger")
        return redirect(url_for('main.dashboard'))
    form = WorkspaceForm()
    if form.validate_on_submit():
        workspace = Workspace(
            name=form.name.data,
            location=form.location.data,
            is_available=form.is_available.data,
            description=form.description.data
        )
        db.session.add(workspace)
        db.session.commit()
        flash('Workspace added successfully!', 'success')
        return redirect(url_for('main.dashboard'))
    return render_template('workspace_form.html', form=form, title='Add Workspace')

@main.route('/edit/<int:workspace_id>', methods=['GET', 'POST'])
@login_required
def edit_workspace(workspace_id):
    if not current_user.is_admin():
        flash("Access denied: Viewers cannot edit workspaces.", "danger")
        return redirect(url_for('main.dashboard'))
    workspace = Workspace.query.get_or_404(workspace_id)
    form = WorkspaceForm(obj=workspace)
    if form.validate_on_submit():
        workspace.name = form.name.data
        workspace.location = form.location.data
        workspace.is_available = form.is_available.data
        workspace.description = form.description.data
        db.session.commit()
        flash('Workspace updated successfully!', 'success')
        return redirect(url_for('main.dashboard'))
    return render_template('workspace_form.html', form=form, title='Edit Workspace')

@main.route('/delete/<int:workspace_id>')
@login_required
def delete_workspace(workspace_id):
    if not current_user.is_admin():
        flash("Access denied: Viewers cannot delete workspaces.", "danger")
        return redirect(url_for('main.dashboard'))
    workspace = Workspace.query.get_or_404(workspace_id)
    db.session.delete(workspace)
    db.session.commit()
    flash('Workspace deleted successfully!', 'info')
    return redirect(url_for('main.dashboard'))

@main.route('/export')
@login_required
def export_workspaces():
    if not current_user.is_admin():
        flash("Access denied: Viewers cannot export data.", "danger")
        return redirect(url_for('main.dashboard'))
    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(['ID', 'Name', 'Location', 'Available', 'Description'])
    workspaces = Workspace.query.all()
    for ws in workspaces:
        cw.writerow([ws.id, ws.name, ws.location, 'Yes' if ws.is_available else 'No', ws.description or ''])
    output = si.getvalue()
    si.close()
    return Response(
        output,
        mimetype='text/csv',
        headers={"Content-Disposition": "attachment;filename=workspaces.csv"}
    )
