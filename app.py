from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, Department, Equipment, Personnel, Area, Assignment
from forms import LoginForm, RegisterForm, DepartmentForm, EquipmentForm, PersonnelForm, AreaForm, AssignmentForm
from config import Config
from datetime import datetime
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config.from_object(Config)

# Crear directorio de uploads si no existe
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Por favor inicia sesión para acceder a esta página.'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def create_tables():
    with app.app_context():
        try:
            # Crear todas las tablas si no existen (no eliminar en producción)
            db.create_all()
            # Crear usuario admin por defecto si no existe
            if not User.query.filter_by(username='admin').first():
                admin = User(username='admin', email='admin@example.com')
                admin.set_password('admin123')
                db.session.add(admin)
                db.session.commit()
                print("Base de datos inicializada correctamente")
        except Exception as e:
            print(f"Error al crear tablas: {e}")
            db.session.rollback()

# Crear tablas al iniciar
create_tables()

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        flash('Usuario o contraseña incorrectos', 'danger')
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(username=form.username.data).first():
            flash('El usuario ya existe', 'danger')
            return render_template('register.html', form=form)
        if User.query.filter_by(email=form.email.data).first():
            flash('El email ya está registrado', 'danger')
            return render_template('register.html', form=form)
        
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Registro exitoso. Por favor inicia sesión.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Sesión cerrada exitosamente', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    total_departments = Department.query.count()
    total_areas = Area.query.count()
    total_equipment = Equipment.query.count()
    total_personnel = Personnel.query.count()
    available_equipment = Equipment.query.filter_by(status='Disponible').count()
    
    return render_template('dashboard.html', 
                         total_departments=total_departments,
                         total_areas=total_areas,
                         total_equipment=total_equipment,
                         total_personnel=total_personnel,
                         available_equipment=available_equipment)

# Rutas para Departamentos
@app.route('/departments')
@login_required
def departments():
    departments_list = Department.query.order_by(Department.name).all()
    return render_template('departments.html', departments=departments_list)

@app.route('/departments/add', methods=['GET', 'POST'])
@login_required
def add_department():
    form = DepartmentForm()
    if form.validate_on_submit():
        if Department.query.filter_by(name=form.name.data).first():
            flash('El departamento ya existe', 'danger')
            return render_template('department_form.html', form=form, title='Agregar Departamento')
        
        department = Department(name=form.name.data, description=form.description.data)
        db.session.add(department)
        db.session.commit()
        flash('Departamento agregado exitosamente', 'success')
        return redirect(url_for('departments'))
    return render_template('department_form.html', form=form, title='Agregar Departamento')

@app.route('/departments/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_department(id):
    department = Department.query.get_or_404(id)
    form = DepartmentForm(obj=department)
    if form.validate_on_submit():
        if Department.query.filter(Department.name == form.name.data, Department.id != id).first():
            flash('El departamento ya existe', 'danger')
            return render_template('department_form.html', form=form, title='Editar Departamento', department=department)
        
        department.name = form.name.data
        department.description = form.description.data
        db.session.commit()
        flash('Departamento actualizado exitosamente', 'success')
        return redirect(url_for('departments'))
    return render_template('department_form.html', form=form, title='Editar Departamento', department=department)

@app.route('/departments/delete/<int:id>', methods=['POST'])
@login_required
def delete_department(id):
    department = Department.query.get_or_404(id)
    db.session.delete(department)
    db.session.commit()
    flash('Departamento eliminado exitosamente', 'success')
    return redirect(url_for('departments'))

# Rutas para Equipos
@app.route('/equipment')
@login_required
def equipment():
    equipment_list = Equipment.query.order_by(Equipment.created_at.desc()).all()
    return render_template('equipment.html', equipment=equipment_list)

@app.route('/equipment/add', methods=['GET', 'POST'])
@login_required
def add_equipment():
    # Verificar que existan departamentos
    if Department.query.count() == 0:
        flash('Debe crear al menos un departamento antes de agregar equipos', 'warning')
        return redirect(url_for('add_department'))
    
    form = EquipmentForm()
    if form.validate_on_submit():
        try:
            if Equipment.query.filter_by(code=form.code.data).first():
                flash('El código ya existe', 'danger')
                return render_template('equipment_form.html', form=form, title='Agregar Equipo')
            if Equipment.query.filter_by(serial=form.serial.data).first():
                flash('El serial ya existe', 'danger')
                return render_template('equipment_form.html', form=form, title='Agregar Equipo')
            
            # Manejar imagen
            image_filename = None
            if form.image.data:
                file = form.image.data
                if file and allowed_file(file.filename):
                    filename = secure_filename(f"{form.code.data}_{file.filename}")
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(filepath)
                    image_filename = filename
            
            equipment = Equipment(
                code=form.code.data,
                serial=form.serial.data,
                equipment_type=form.equipment_type.data,
                brand=form.brand.data or None,
                model=form.model.data or None,
                status=form.status.data,
                department_id=form.department_id.data,
                area_id=form.area_id.data if form.area_id.data else None,
                assigned_to_id=form.assigned_to_id.data if form.assigned_to_id.data else None,
                image_filename=image_filename,
                ip_address=form.ip_address.data or None,
                physical_address=form.physical_address.data or None,
                specifications=form.specifications.data or None,
                registration_date=form.registration_date.data,
                assignment_date=form.assignment_date.data if form.assignment_date.data else None,
                purchase_date=form.purchase_date.data if form.purchase_date.data else None,
                warranty_expiry=form.warranty_expiry.data if form.warranty_expiry.data else None,
                notes=form.notes.data or None
            )
            db.session.add(equipment)
            db.session.commit()
            flash('Equipo agregado exitosamente', 'success')
            return redirect(url_for('equipment'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al agregar equipo: {str(e)}', 'danger')
            return render_template('equipment_form.html', form=form, title='Agregar Equipo')
    elif request.method == 'POST':
        # Si el formulario no es válido, mostrar errores
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'Error en {getattr(form, field).label.text}: {error}', 'danger')
    return render_template('equipment_form.html', form=form, title='Agregar Equipo')

@app.route('/equipment/view/<int:id>')
@login_required
def view_equipment(id):
    equipment = Equipment.query.get_or_404(id)
    return render_template('equipment_view.html', equipment=equipment)

@app.route('/equipment/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_equipment(id):
    equipment = Equipment.query.get_or_404(id)
    form = EquipmentForm(obj=equipment)
    form.registration_date.data = equipment.registration_date.date() if equipment.registration_date else None
    form.assignment_date.data = equipment.assignment_date.date() if equipment.assignment_date else None
    form.purchase_date.data = equipment.purchase_date.date() if equipment.purchase_date else None
    form.warranty_expiry.data = equipment.warranty_expiry.date() if equipment.warranty_expiry else None
    # Inicializar área si existe
    if equipment.area_id:
        form.area_id.data = equipment.area_id
    
    if form.validate_on_submit():
        if Equipment.query.filter(Equipment.code == form.code.data, Equipment.id != id).first():
            flash('El código ya existe', 'danger')
            return render_template('equipment_form.html', form=form, title='Editar Equipo', equipment=equipment)
        if Equipment.query.filter(Equipment.serial == form.serial.data, Equipment.id != id).first():
            flash('El serial ya existe', 'danger')
            return render_template('equipment_form.html', form=form, title='Editar Equipo', equipment=equipment)
        
        # Manejar imagen si se sube una nueva
        if form.image.data:
            file = form.image.data
            if file and allowed_file(file.filename):
                # Eliminar imagen anterior si existe
                if equipment.image_filename:
                    old_filepath = os.path.join(app.config['UPLOAD_FOLDER'], equipment.image_filename)
                    if os.path.exists(old_filepath):
                        os.remove(old_filepath)
                # Guardar nueva imagen
                filename = secure_filename(f"{form.code.data}_{file.filename}")
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                equipment.image_filename = filename
        
        equipment.code = form.code.data
        equipment.serial = form.serial.data
        equipment.equipment_type = form.equipment_type.data
        equipment.brand = form.brand.data
        equipment.model = form.model.data
        equipment.status = form.status.data
        equipment.department_id = form.department_id.data
        equipment.area_id = form.area_id.data if form.area_id.data else None
        equipment.assigned_to_id = form.assigned_to_id.data if form.assigned_to_id.data else None
        equipment.ip_address = form.ip_address.data or None
        equipment.physical_address = form.physical_address.data or None
        equipment.specifications = form.specifications.data or None
        equipment.registration_date = form.registration_date.data
        equipment.assignment_date = form.assignment_date.data if form.assignment_date.data else None
        equipment.purchase_date = form.purchase_date.data if form.purchase_date.data else None
        equipment.warranty_expiry = form.warranty_expiry.data if form.warranty_expiry.data else None
        equipment.notes = form.notes.data
        equipment.updated_at = datetime.utcnow()
        
        db.session.commit()
        flash('Equipo actualizado exitosamente', 'success')
        return redirect(url_for('equipment'))
    return render_template('equipment_form.html', form=form, title='Editar Equipo', equipment=equipment)

@app.route('/equipment/delete/<int:id>', methods=['POST'])
@login_required
def delete_equipment(id):
    equipment = Equipment.query.get_or_404(id)
    # Eliminar imagen si existe
    if equipment.image_filename:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], equipment.image_filename)
        if os.path.exists(filepath):
            os.remove(filepath)
    db.session.delete(equipment)
    db.session.commit()
    flash('Equipo eliminado exitosamente', 'success')
    return redirect(url_for('equipment'))

@app.route('/uploads/<filename>')
@login_required
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Rutas para Áreas
@app.route('/areas')
@login_required
def areas():
    areas_list = Area.query.order_by(Area.name).all()
    return render_template('areas.html', areas=areas_list)

@app.route('/areas/add', methods=['GET', 'POST'])
@login_required
def add_area():
    form = AreaForm()
    if form.validate_on_submit():
        if Area.query.filter_by(name=form.name.data).first():
            flash('El área ya existe', 'danger')
            return render_template('area_form.html', form=form, title='Agregar Área')
        
        area = Area(name=form.name.data, description=form.description.data, location=form.location.data)
        db.session.add(area)
        db.session.commit()
        flash('Área agregada exitosamente', 'success')
        return redirect(url_for('areas'))
    return render_template('area_form.html', form=form, title='Agregar Área')

@app.route('/areas/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_area(id):
    area = Area.query.get_or_404(id)
    form = AreaForm(obj=area)
    if form.validate_on_submit():
        if Area.query.filter(Area.name == form.name.data, Area.id != id).first():
            flash('El área ya existe', 'danger')
            return render_template('area_form.html', form=form, title='Editar Área', area=area)
        
        area.name = form.name.data
        area.description = form.description.data
        area.location = form.location.data
        db.session.commit()
        flash('Área actualizada exitosamente', 'success')
        return redirect(url_for('areas'))
    return render_template('area_form.html', form=form, title='Editar Área', area=area)

@app.route('/areas/delete/<int:id>', methods=['POST'])
@login_required
def delete_area(id):
    area = Area.query.get_or_404(id)
    db.session.delete(area)
    db.session.commit()
    flash('Área eliminada exitosamente', 'success')
    return redirect(url_for('areas'))

# Rutas para Personal
@app.route('/personnel')
@login_required
def personnel():
    personnel_list = Personnel.query.order_by(Personnel.name).all()
    return render_template('personnel.html', personnel=personnel_list)

@app.route('/personnel/add', methods=['GET', 'POST'])
@login_required
def add_personnel():
    form = PersonnelForm()
    if form.validate_on_submit():
        if form.employee_id.data and Personnel.query.filter_by(employee_id=form.employee_id.data).first():
            flash('El ID de empleado ya existe', 'danger')
            return render_template('personnel_form.html', form=form, title='Agregar Personal')
        
        personnel = Personnel(
            name=form.name.data,
            last_name=form.last_name.data,
            email=form.email.data,
            phone=form.phone.data,
            position=form.position.data,
            employee_id=form.employee_id.data,
            department_id=form.department_id.data,
            area_id=form.area_id.data if form.area_id.data else None
        )
        db.session.add(personnel)
        db.session.commit()
        flash('Personal agregado exitosamente', 'success')
        return redirect(url_for('personnel'))
    return render_template('personnel_form.html', form=form, title='Agregar Personal')

@app.route('/personnel/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_personnel(id):
    personnel = Personnel.query.get_or_404(id)
    form = PersonnelForm(obj=personnel)
    # Inicializar área si existe
    if personnel.area_id:
        form.area_id.data = personnel.area_id
    if form.validate_on_submit():
        if form.employee_id.data and Personnel.query.filter(Personnel.employee_id == form.employee_id.data, Personnel.id != id).first():
            flash('El ID de empleado ya existe', 'danger')
            return render_template('personnel_form.html', form=form, title='Editar Personal', personnel=personnel)
        
        personnel.name = form.name.data
        personnel.last_name = form.last_name.data
        personnel.email = form.email.data
        personnel.phone = form.phone.data
        personnel.position = form.position.data
        personnel.employee_id = form.employee_id.data
        personnel.department_id = form.department_id.data
        personnel.area_id = form.area_id.data if form.area_id.data else None
        
        db.session.commit()
        flash('Personal actualizado exitosamente', 'success')
        return redirect(url_for('personnel'))
    return render_template('personnel_form.html', form=form, title='Editar Personal', personnel=personnel)

@app.route('/personnel/delete/<int:id>', methods=['POST'])
@login_required
def delete_personnel(id):
    personnel = Personnel.query.get_or_404(id)
    db.session.delete(personnel)
    db.session.commit()
    flash('Personal eliminado exitosamente', 'success')
    return redirect(url_for('personnel'))

# Rutas para Asignaciones
@app.route('/assignments')
@login_required
def assignments():
    assignments_list = Assignment.query.order_by(Assignment.assignment_date.desc()).all()
    return render_template('assignments.html', assignments=assignments_list)

@app.route('/assignments/add', methods=['GET', 'POST'])
@login_required
def add_assignment():
    form = AssignmentForm()
    if form.validate_on_submit():
        try:
            equipment = Equipment.query.get_or_404(form.equipment_id.data)
            
            # Verificar si el equipo ya está asignado activamente
            active_assignment = Assignment.query.filter_by(
                equipment_id=form.equipment_id.data,
                status='Activa'
            ).first()
            
            if active_assignment:
                flash('Este equipo ya tiene una asignación activa', 'warning')
                return render_template('assignment_form.html', form=form, title='Agregar Asignación')
            
            assignment = Assignment(
                equipment_id=form.equipment_id.data,
                personnel_id=form.personnel_id.data,
                assignment_date=form.assignment_date.data,
                return_date=form.return_date.data if form.return_date.data else None,
                status=form.status.data,
                notes=form.notes.data or None,
                assigned_by=current_user.username
            )
            
            # Actualizar el equipo
            equipment.assigned_to_id = form.personnel_id.data
            equipment.assignment_date = form.assignment_date.data
            if form.status.data == 'Activa':
                equipment.status = 'Asignado'
            
            db.session.add(assignment)
            db.session.commit()
            flash('Asignación creada exitosamente', 'success')
            return redirect(url_for('assignments'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear asignación: {str(e)}', 'danger')
            return render_template('assignment_form.html', form=form, title='Agregar Asignación')
    elif request.method == 'POST':
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'Error en {getattr(form, field).label.text}: {error}', 'danger')
    return render_template('assignment_form.html', form=form, title='Agregar Asignación')

@app.route('/assignments/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_assignment(id):
    assignment = Assignment.query.get_or_404(id)
    form = AssignmentForm(obj=assignment)
    form.assignment_date.data = assignment.assignment_date.date() if assignment.assignment_date else None
    form.return_date.data = assignment.return_date.date() if assignment.return_date else None
    
    if form.validate_on_submit():
        try:
            equipment = Equipment.query.get_or_404(form.equipment_id.data)
            
            # Si se marca como devuelta, actualizar el equipo
            if form.status.data == 'Devuelta' and assignment.status != 'Devuelta':
                equipment.assigned_to_id = None
                equipment.assignment_date = None
                equipment.status = 'Disponible'
                if not form.return_date.data:
                    form.return_date.data = datetime.utcnow().date()
            elif form.status.data == 'Activa' and assignment.status != 'Activa':
                equipment.assigned_to_id = form.personnel_id.data
                equipment.assignment_date = form.assignment_date.data
                equipment.status = 'Asignado'
            
            assignment.equipment_id = form.equipment_id.data
            assignment.personnel_id = form.personnel_id.data
            assignment.assignment_date = form.assignment_date.data
            assignment.return_date = form.return_date.data if form.return_date.data else None
            assignment.status = form.status.data
            assignment.notes = form.notes.data or None
            assignment.updated_at = datetime.utcnow()
            
            db.session.commit()
            flash('Asignación actualizada exitosamente', 'success')
            return redirect(url_for('assignments'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar asignación: {str(e)}', 'danger')
            return render_template('assignment_form.html', form=form, title='Editar Asignación', assignment=assignment)
    return render_template('assignment_form.html', form=form, title='Editar Asignación', assignment=assignment)

@app.route('/assignments/return/<int:id>', methods=['POST'])
@login_required
def return_assignment(id):
    assignment = Assignment.query.get_or_404(id)
    if assignment.status == 'Devuelta':
        flash('Esta asignación ya fue devuelta', 'warning')
        return redirect(url_for('assignments'))
    
    try:
        equipment = assignment.equipment
        assignment.status = 'Devuelta'
        assignment.return_date = datetime.utcnow()
        assignment.updated_at = datetime.utcnow()
        
        # Actualizar el equipo
        equipment.assigned_to_id = None
        equipment.assignment_date = None
        equipment.status = 'Disponible'
        
        db.session.commit()
        flash('Equipo devuelto exitosamente', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al devolver equipo: {str(e)}', 'danger')
    
    return redirect(url_for('assignments'))

@app.route('/assignments/delete/<int:id>', methods=['POST'])
@login_required
def delete_assignment(id):
    assignment = Assignment.query.get_or_404(id)
    try:
        # Si la asignación está activa, actualizar el equipo
        if assignment.status == 'Activa':
            equipment = assignment.equipment
            equipment.assigned_to_id = None
            equipment.assignment_date = None
            equipment.status = 'Disponible'
        
        db.session.delete(assignment)
        db.session.commit()
        flash('Asignación eliminada exitosamente', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar asignación: {str(e)}', 'danger')
    
    return redirect(url_for('assignments'))

# API para obtener la IP de un equipo
@app.route('/api/equipment/<int:id>/ip')
@login_required
def get_equipment_ip(id):
    from flask import jsonify
    equipment = Equipment.query.get_or_404(id)
    return jsonify({
        'ip_address': equipment.ip_address or ''
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

