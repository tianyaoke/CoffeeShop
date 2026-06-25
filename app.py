from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)
app.secret_key = 'daily_brew_tester_key'
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = True

# DATABASE CONNECTION
def get_db_connection():
    return psycopg2.connect(
        host="localhost",
        database="coffeeshop",  
        user="postgres",        
        password="208802"
    )

# --- CORE ROUTES ---
@app.route('/')
def index():
    return render_template('home.html')

@app.route('/menu')
def menu_page():
    return render_template('menu.html')

@app.route('/order')
def order_page():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM coffee_items WHERE is_available = TRUE ORDER BY item_id ASC;")
    items = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('order.html', items=items)

# --- AUTHENTICATION ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO users (username, email, password, role) VALUES (%s, %s, %s, 'customer')",
            (request.form.get('username'), request.form.get('email'), request.form.get('password'))
        )
        conn.commit()
        cur.close()
        conn.close()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM users WHERE email = %s AND password = %s",
                    (request.form.get('email'), request.form.get('password')))
        user = cur.fetchone()
        cur.close()
        conn.close()
        if user:
            session.permanent = True
            session['user_id'] = user['id']
            session['user'] = user['username']
            session['role'] = user['role']
            return redirect(url_for('admin_dashboard') if user['role'] == 'admin' else url_for('index'))
        return "Invalid email or password."
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# --- ORDERING ---
@app.route('/submit_order', methods=['POST'])
def submit_order():
    print(f"DEBUG - Current Session: {session}")
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json
    items = data.get('items', [])
    user_id = session['user_id']

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    try:
        item_ids = [item['item_id'] for item in items]
        cur.execute(
            "SELECT item_id, name, price FROM coffee_items WHERE item_id = ANY(%s)",
            (item_ids,)
        )
        db_items = {str(row['item_id']): row for row in cur.fetchall()}

        total = sum(
            db_items[str(i['item_id'])]['price'] * i['quantity']
            for i in items
        )

        cur.execute(
            "INSERT INTO orders (user_id, total_amount, status) VALUES (%s, %s, 'pending') RETURNING order_id",
            (user_id, total)
        )
        order_id = cur.fetchone()['order_id']

        for item in items:
            db_item = db_items[str(item['item_id'])]
            cur.execute(
                """INSERT INTO order_items (order_id, item_id, item_name, unit_price, quantity)
                   VALUES (%s, %s, %s, %s, %s)""",
                (order_id, item['item_id'], db_item['name'], db_item['price'], item['quantity'])
            )

        conn.commit()
        return jsonify({"success": True, "order_id": order_id})

    except Exception as e:
        conn.rollback()
        print(f"DEBUG - Order Error: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cur.close()
        conn.close()

# --- ADMIN ROUTES ---
@app.route('/admin/orders')
def admin_view_orders():
    if session.get('role') != 'admin':
        return "Unauthorized", 403
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # We join: orders -> order_items -> coffee_items
    query = """
        SELECT o.order_id, u.username, c.name as item_name, oi.quantity, o.created_at 
        FROM orders o
        JOIN users u ON o.user_id = u.id
        JOIN order_items oi ON o.order_id = oi.order_id
        JOIN coffee_items c ON oi.item_id = c.item_id
        ORDER BY o.created_at DESC;
    """
    cur.execute(query)
    orders = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('admin_orders.html', orders=orders)

@app.route('/admin')
def admin_dashboard():
    if session.get('role') != 'admin':
        return "Unauthorized", 403
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM coffee_items ORDER BY item_id DESC;")
    items = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('admin.html', items=items)

@app.route('/admin/add', methods=['POST'])
def admin_add_item():
    if session.get('role') != 'admin':
        return "Unauthorized", 403
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO coffee_items (name, description, price, category, image_url, is_available) VALUES (%s, %s, %s, %s, %s, TRUE)",
        (request.form.get('name'), request.form.get('description'), float(request.form.get('price')),
         request.form.get('category').lower(), f"images/{request.form.get('image_filename')}")
    )
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete/<int:item_id>', methods=['POST'])
def admin_delete_item(item_id):
    if session.get('role') != 'admin':
        return "Unauthorized", 403
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM coffee_items WHERE item_id = %s;", (item_id,))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    app.run(debug=True)