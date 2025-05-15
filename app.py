from flask import Flask, render_template, request, redirect, url_for, session
import pyodbc
from functools import wraps
from base64 import b64encode

app = Flask(__name__)
app.secret_key = 'tu_clave_secreta'

# Decorador para proteger rutas que requieren autenticación
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def conectar_bd(usuario, contrasena):
    server = 'CHALI\SQLEXPRESS'
    database = 'bdFlorycell'
    try:
        conexion = pyodbc.connect(
            f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={usuario};PWD={contrasena}'
        )
        return conexion
    except Exception as e:
        return None

@app.route('/')
def index():
    try:
        conexion = conectar_bd('sa', '1234')
        if conexion:
            cursor = conexion.cursor()
            cursor.execute("SELECT id, nombre, descripcion, precio, imagen FROM Productos")
            # Convertir los resultados a una lista de diccionarios con nombres de columnas
            columns = [column[0] for column in cursor.description]
            productos = []
            for row in cursor.fetchall():
                # Convertir la imagen a base64 si existe
                producto = dict(zip(columns, row))
                if producto['imagen']:
                    producto['imagen'] = b64encode(producto['imagen']).decode('utf-8')
                productos.append(producto)
            conexion.close()
            print(f"Productos encontrados: {len(productos)}")  # Para debugging
            return render_template('index.html', productos=productos)
        return render_template('index.html', productos=[])
    except Exception as e:
        print(f"Error en index: {str(e)}")  # Para debugging
        return render_template('index.html', productos=[])

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['nombre']
        contrasena = request.form['contrasena']
        conexion = conectar_bd(usuario, contrasena)
        if conexion:
            session['usuario'] = usuario
            session['contrasena'] = contrasena  # Agregamos esta línea
            return redirect(url_for('admin_panel'))
        else:
            return "Usuario o contraseña incorrectos"
    return render_template('login.html')

@app.route('/admin')
@login_required
def admin_panel():
    try:
        # Obtener lista de productos de la base de datos
        conexion = conectar_bd(session.get('usuario'), session.get('contrasena'))
        if conexion:
            cursor = conexion.cursor()
            cursor.execute("SELECT id, nombre, descripcion, precio FROM Productos")
            productos = cursor.fetchall()
            conexion.close()
            return render_template('admin.html', productos=productos)
        else:
            return redirect(url_for('login'))
    except Exception as e:
        # Si hay algún error, redirigir al login
        return redirect(url_for('login'))

@app.route('/agregar_producto', methods=['POST'])
@login_required
def agregar_producto():
    if request.method == 'POST':
        nombre = request.form['nombre']
        descripcion = request.form['descripcion']
        precio = request.form['precio']
        imagen = request.files['imagen'].read() if 'imagen' in request.files else None
        
        conexion = conectar_bd(session['usuario'], session['contrasena'])
        cursor = conexion.cursor()
        cursor.execute("""
            INSERT INTO Productos (nombre, descripcion, precio, imagen)
            VALUES (?, ?, ?, ?)
        """, (nombre, descripcion, precio, imagen))
        conexion.commit()
        conexion.close()
        return redirect(url_for('admin_panel'))

@app.route('/modificar_producto/<int:id>', methods=['POST'])
@login_required
def modificar_producto(id):
    nombre = request.form['nombre']
    descripcion = request.form['descripcion']
    precio = request.form['precio']
    imagen = request.files['imagen'].read() if 'imagen' in request.files else None
    
    conexion = conectar_bd(session['usuario'], session['contrasena'])
    cursor = conexion.cursor()
    if imagen:
        cursor.execute("""
            UPDATE Productos 
            SET nombre=?, descripcion=?, precio=?, imagen=?
            WHERE id=?
        """, (nombre, descripcion, precio, imagen, id))
    else:
        cursor.execute("""
            UPDATE Productos 
            SET nombre=?, descripcion=?, precio=?
            WHERE id=?
        """, (nombre, descripcion, precio, id))
    conexion.commit()
    conexion.close()
    return redirect(url_for('admin_panel'))

@app.route('/eliminar_producto/<int:id>')
@login_required
def eliminar_producto(id):
    conexion = conectar_bd(session['usuario'], session['contrasena'])
    cursor = conexion.cursor()
    cursor.execute("DELETE FROM Productos WHERE id=?", (id,))
    conexion.commit()
    conexion.close()
    return redirect(url_for('admin_panel'))

if __name__ == '__main__':
    app.run(debug=True)