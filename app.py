from flask import Flask, render_template,url_for,redirect,request, session, Response
from flask import flash
from werkzeug.security import check_password_hash, generate_password_hash
import sqlite3
import csv
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv
import os
#===========================================================================

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

#database path
BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "supermarket.db"

#connection to database
def get_db_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection

# ====================================
# UPDATE WAREHOUSE STOCK
# ====================================
def update_warehouse_stock(conn, order_id):

    # get all order items
    items = conn.execute("""
        SELECT
            product_id,
            quantity
        FROM order_items
        WHERE order_id=?
    """, (order_id,)).fetchall()

    # update stock for each item
    for item in items:

        conn.execute("""

            UPDATE warehouse_stock
            SET quantity = quantity - ?
            WHERE product_id=?
        """, (

            item["quantity"],
            item["product_id"]
        ))

# ====================================
# ROUTES
# ====================================
#link to home.html
@app.route("/")
def home():
    connection = get_db_connection()
    stores = connection.execute("SELECT * FROM stores").fetchall()
    connection.close()

    return render_template("home.html", stores=stores)

#link to login.html
@app.route("/login", methods=["GET","POST"])
def login():
    message = "Please login to access the ERP system."

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        #connect to database
        connection = get_db_connection()
        #fetch data
        user = connection.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        #close connection to db
        connection.close()

        if user and user["is_active"] == 1 and check_password_hash(user["password"], password):
            session["user"] = username   #ποιος έκανε login
            session["role"] = user["role"] #manager / assistant
            session["store_id"] = user["store_id"] #store_id

            #admin role
            if user["role"] == "admin":
                flash("Welcome to the Admin Panel", "success")
                return redirect(url_for("admin_panel"))

            #warehouse role
            elif user["role"] == "warehouse":
                flash("Welcome to Central Warehouse Management", "success")
                return redirect(url_for("products"))

            #manager / assistant manager role
            elif user["role"] == "manager" or user["role"] == "assistant_manager":
                flash("Welcome to the Manager Panel", "success")
                return redirect(url_for("dashboard"))
        else:
            message = "Login Unsuccessful. Please check username and password"

    return render_template("login.html", message=message)



#admin login
@app.route("/admin")
def admin_panel():

    #user must be logged in
    if "user" not in session:
        return redirect(url_for("login"))

    #check if user is admin
    if session.get("role") != "admin":
        flash("You do not have permission to access the admin panel", "error")
        return redirect(url_for("home"))

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row

    cursor = connection.cursor()

    #total users
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]

    # total products
    cursor.execute("SELECT COUNT(*) FROM products")
    total_products = cursor.fetchone()[0]

    # total stores
    cursor.execute("SELECT COUNT(*) FROM stores")
    total_stores = cursor.fetchone()[0]

    # low stock products
    cursor.execute("""
        SELECT COUNT(*)
        FROM warehouse_stock
        WHERE quantity < 300
    """)

    low_stock = cursor.fetchone()[0]

    connection.close()

    return render_template(
        "admin.html",
        total_users=total_users,
        total_products=total_products,
        total_stores=total_stores,
        low_stock=low_stock
    )

#admin users
@app.route("/admin/users")
def manage_users():

    # check login
    if "user" not in session:
        return redirect(url_for("login"))

    # admin only
    if session.get("role") != "admin":
        flash("Access denied", "error")
        return redirect(url_for("home"))

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row

    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            user_id,
            username,
            role,
            store_id,
            is_active
        FROM users
        ORDER BY role
    """)

    users = cursor.fetchall()
    connection.close()

    return render_template("manage_users.html", users=users)

#disable user
@app.route("/admin/disable_user/<int:user_id>")
def disable_user(user_id):

    # admin only
    if "user" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "admin":
        return redirect(url_for("home"))

    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE users
        SET is_active = 0
        WHERE user_id = ?
    """, (user_id,))

    connection.commit()
    connection.close()

    flash("User disabled successfully", "success")
    return redirect(url_for("manage_users"))

#enable user
@app.route("/admin/enable_user/<int:user_id>")
def enable_user(user_id):

    # admin only
    if "user" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "admin":
        return redirect(url_for("home"))

    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE users
        SET is_active = 1
        WHERE user_id = ?
    """, (user_id,))

    connection.commit()
    connection.close()

    flash("User enabled successfully", "success")

    return redirect(url_for("manage_users"))

#add user
@app.route("/admin/add_user", methods=["GET", "POST"])
def add_user():

    #admin only
    if "user" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "admin":
        return redirect(url_for("home"))

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row

    cursor = connection.cursor()

    #get stores for dropdown
    cursor.execute("SELECT * FROM stores")
    stores = cursor.fetchall()

    #submit form
    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]
        role = request.form["role"]
        store_id = request.form["store_id"]

        #hash password
        hashed_password = generate_password_hash(password)

        #insert user
        cursor.execute("""
            INSERT INTO users
            (username, password, role, store_id, is_active)
            VALUES (?, ?, ?, ?, 1)
        """, (username, hashed_password, role, store_id))

        connection.commit()
        connection.close()

        flash("User added successfully!", "success")
        return redirect(url_for("manage_users"))

    connection.close()

    return render_template(
        "add_user.html",
        stores=stores
    )


#edit user
@app.route("/admin/edit_user/<int:user_id>", methods=["GET", "POST"])
def edit_user(user_id):

    #admin only
    if "user" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "admin":
        return redirect(url_for("home"))

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row

    cursor = connection.cursor()

    #get selected user
    cursor.execute("""
        SELECT *
        FROM users
        WHERE user_id = ?
    """, (user_id,))

    user = cursor.fetchone()

    #get stores
    cursor.execute("""
        SELECT *
        FROM stores
    """)

    stores = cursor.fetchall()

    #update form
    if request.method == "POST":

        username = request.form["username"]
        role = request.form["role"]
        store_id = request.form["store_id"]

        cursor.execute("""
            UPDATE users
            SET
                username = ?,
                role = ?,
                store_id = ?
            WHERE user_id = ?
        """, (username, role, store_id, user_id))

        connection.commit()
        connection.close()

        flash("User updated successfully", "success")

        return redirect(url_for("manage_users"))

    connection.close()

    return render_template(
        "edit_user.html",
        user=user,
        stores=stores
    )

#control panel
@app.route("/dashboard")
def dashboard():

    # user not logged in
    if "user" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    store_id = session["store_id"]
    store = conn.execute("""
        SELECT store_name
        FROM stores
        WHERE store_id = ?
    """, (store_id,)).fetchone()

    store_name = store["store_name"]

    # ====================================
    # TOTAL ORDERS
    # ====================================

    total_orders = conn.execute("""
        SELECT COUNT(*) AS total
        FROM orders
        WHERE store_id=?
    """, (store_id,)).fetchone()["total"]


    # ====================================
    # MONTHLY TOTAL VALUE
    # ====================================

    monthly_value = conn.execute("""
        SELECT COALESCE(SUM(total), 0) AS total_value
        FROM orders
        WHERE store_id=?
        AND strftime('%Y-%m', order_date)
            = strftime('%Y-%m', 'now')
    """, (store_id,)).fetchone()["total_value"]


    # ====================================
    # PENDING ORDERS
    # ====================================

    pending_orders = conn.execute("""
        SELECT COUNT(*) AS pending
        FROM orders
        WHERE store_id=?
        AND order_status='Pending'
    """, (store_id,)).fetchone()["pending"]


    # ====================================
    # LAST ORDER
    # ====================================

    last_order = conn.execute("""
        SELECT order_date, order_status
        FROM orders
        WHERE store_id=?
        ORDER BY order_date DESC
        LIMIT 1
    """, (store_id,)).fetchone()


    # ====================================
    # RECENT ORDERS
    # ====================================

    recent_orders = conn.execute("""
        SELECT
            order_id,
            order_date,
            total,
            order_status
        FROM orders
        WHERE store_id=?
        ORDER BY order_date DESC
        LIMIT 5
    """, (store_id,)).fetchall()


    conn.close()

    return render_template(
        "control_panel.html",
        store_name=store_name,
        total_orders=total_orders,
        monthly_value=round(monthly_value, 2),
        pending_orders=pending_orders,
        last_order=last_order,
        recent_orders=recent_orders
    )

#manager submits pending orders
@app.route("/submit_order/<int:order_id>")
def approve_order(order_id):

    # security check
    if session.get("role") != "manager":
        flash("You do not have permission to submit orders")
        return redirect(url_for("dashboard"))

    conn = get_db_connection()

    conn.execute("""
        UPDATE orders
        SET order_status='Submitted'
        WHERE order_id=?
    """, (order_id,))

    # update warehouse stock
    update_warehouse_stock(conn, order_id)

    conn.commit()
    conn.close()

    flash("Order submitted successfully")

    return redirect(url_for("dashboard"))

#clear order
@app.route("/clear_order")
def clear_order():

    session["cart"] = []
    session.modified = True

    flash("Order cleared successfully", "success")

    return redirect(url_for("orders"))


#order history
@app.route("/order_history")
def order_history():

    conn = get_db_connection()
    store_id = session.get("store_id")

    orders = conn.execute("""

        SELECT
            order_id,
            order_date,
            order_status,
            total

        FROM orders
        WHERE store_id=?
        ORDER BY order_date DESC
    """, (store_id,)).fetchall()

    conn.close()

    return render_template(
        "order_history.html",
        orders=orders
    )


#order details
@app.route("/order_details/<int:order_id>")
def order_details(order_id):

    conn = get_db_connection()

    # ====================================
    # ORDER HEADER
    # ====================================
    order = conn.execute("""
        SELECT
            order_id,
            order_date,
            order_status,
            total
        FROM orders
        WHERE order_id=?
    """, (order_id,)).fetchone()


    # ====================================
    # ORDER ITEMS
    # ====================================

    items = conn.execute("""

        SELECT
            p.product_name,
            oi.quantity,
            p.product_price,
            (oi.quantity * p.product_price)
                AS line_total
        FROM order_items oi
        JOIN products p
        ON oi.product_id = p.product_id
        WHERE oi.order_id=?
    """, (order_id,)).fetchall()

    conn.close()

    return render_template(
        "order_details.html",
        order=order,
        items=items
    )


#download csv file
@app.route("/export_orders_csv")
def export_orders_csv():

    conn = get_db_connection()
    store_id = session.get("store_id")

    orders = conn.execute("""
        SELECT
            order_id,
            order_date,
            total,
            order_status
        FROM orders
        WHERE store_id=?
        ORDER BY order_date DESC
    """, (store_id,)).fetchall()

    conn.close()

    # ====================================
    # CREATE CSV
    # ====================================
    def generate():
        data = csv.writer(
            open("temp.csv", "w", newline="", encoding="utf-8")
        )

        # headers
        yield "Order ID,Date,Total,Status\n"

        # rows
        for order in orders:
            row = (
                f"{order['order_id']},"
                f"{order['order_date']},"
                f"{order['total']},"
                f"{order['order_status']}\n"
            )
            yield row

    return Response(
        generate(),
        mimetype="text/csv",
        headers={
            "Content-Disposition":
            "attachment; filename=orders_export.csv"
        }
    )


#link to products
@app.route("/products")
def products():

    # connect to database
    connection = get_db_connection()

    #security check
    if session.get("role") != "warehouse":
        flash("You do not have permission to access this page")
        return redirect(url_for("control_panel"))

    # get values from URL
    search = request.args.get("search")
    category = request.args.get("category")

    #create query
    query = """
    SELECT 
        p.product_id,
        p.product_name,
        p.product_category,
        p.product_unit,
        p.product_price,
        p.is_active,
        w.quantity
    FROM products p
    JOIN warehouse_stock w
        ON p.product_id = w.product_id
    WHERE 1=1
    """
    #list to hold search results
    params = []

    #Search by product name
    if search:
        query += " AND p.product_name LIKE ?"
        params.append(f"%{search}%")

    #Filter by category
    if category:
        query += " AND p.product_category = ?"
        params.append(category)

    products = connection.execute(query, params).fetchall()

    categories = connection.execute("""
        SELECT *
        FROM categories
        ORDER BY category_name
    """).fetchall()

    connection.close()

    return render_template("products.html", products=products, categories=categories)

#link to add product
@app.route("/add_product", methods=["GET", "POST"])
def add_product():
    conn = get_db_connection()

    categories = conn.execute("""
        SELECT *
        FROM categories
        ORDER BY category_name
    """).fetchall()

    if request.method == "POST":

        # get data from form
        product_name = request.form.get("product_name")
        category = request.form.get("category")
        unit = request.form.get("unit")
        quantity = request.form.get("quantity")
        price = request.form.get("price")

        if not product_name or not category or not unit or not quantity or not price:
            return render_template("add_product.html", error="Συμπληρώστε όλα τα πεδία", categories=categories)

        price = float(price)

        # insert στο products
        cursor = conn.execute(
            """
            INSERT INTO products (product_name, product_category, product_unit, product_price)
            VALUES (?, ?, ?, ?)
            """,
            (product_name, category, unit, price)
        )

        # get id of new product
        product_id = cursor.lastrowid

        # insert στο warehouse_stock
        conn.execute(
            """
            INSERT INTO warehouse_stock (product_id, quantity)
            VALUES (?, ?)
            """,
            (product_id, quantity)
        )

        conn.commit()
        conn.close()

        # redirect πίσω στη σελίδα products
        flash("Product added successfully!")
        return redirect(url_for("products"))

    conn.close()
    return render_template("add_product.html", categories=categories)


#link to edit product
@app.route("/edit_product/<int:product_id>", methods=["GET", "POST"])
def edit_product(product_id):
    conn = get_db_connection()

    if request.method == "POST":
        product_name = request.form["product_name"]
        category = request.form["category"]
        unit = request.form["unit"]
        quantity = request.form["quantity"]

        conn.execute("""
            UPDATE products
            SET product_name=?, product_category=?, product_unit=?
            WHERE product_id=?
        """, (product_name, category, unit, product_id))

        conn.execute("""
            UPDATE warehouse_stock
            SET quantity=?
            WHERE product_id=?
        """, (quantity, product_id))

        conn.commit()
        conn.close()

        flash("Product updated successfully!")
        return redirect(url_for("products"))

    # GET
    product = conn.execute("""
        SELECT p.*, w.quantity
        FROM products p
        JOIN warehouse_stock w ON p.product_id = w.product_id
        WHERE p.product_id=?
    """, (product_id,)).fetchone()

    conn.close()

    return render_template("edit_product.html", product=product)


#disable product
@app.route("/toggle_product/<int:product_id>")
def toggle_product(product_id):
    conn = get_db_connection()

    #current status
    product = conn.execute(
        "SELECT is_active FROM products WHERE product_id=?",
        (product_id,)
    ).fetchone()

    new_status = 0 if product["is_active"] == 1 else 1

    conn.execute(
        "UPDATE products SET is_active=? WHERE product_id=?",
        (new_status, product_id)
    )

    conn.commit()
    conn.close()

    return redirect(url_for("products"))

#add category
@app.route("/add_category", methods=["GET", "POST"])
def add_category():

    conn = get_db_connection()

    if request.method == "POST":
        category_name = request.form.get("category_name")

        # validation
        if not category_name:
            flash("Please enter category name", "error")
            return redirect(url_for("add_category"))
        try:

            conn.execute("""
                INSERT INTO categories (category_name)
                VALUES (?)
            """, (category_name,))

            conn.commit()
            flash("Category added successfully!", "success")
        except:
            flash("Category already exists!", "error")
        conn.close()

        return redirect(url_for("add_category"))

    # GET ALL CATEGORIES
    categories = conn.execute("""
        SELECT
            c.category_id,
            c.category_name,
            COUNT(p.product_id) AS product_count

        FROM categories c

        LEFT JOIN products p
            ON c.category_name = p.product_category

        GROUP BY c.category_id, c.category_name

        ORDER BY c.category_name
    """).fetchall()

    conn.close()

    return render_template(
        "add_category.html",
        categories=categories
    )


#orders
@app.route("/orders", methods=["GET", "POST"])
def orders():

    conn = get_db_connection()

    # =========================
    # SESSION CART
    # =========================

    if "cart" not in session:
        session["cart"] = []

    # =========================
    # POST (ADD ITEM TO CART)
    # =========================

    if request.method == "POST":

        product_id = request.form.get("product_id")
        quantity = request.form.get("quantity")

        # validation
        if not product_id or not quantity:
            return redirect(url_for("orders"))

        # get product data
        product = conn.execute("""
            SELECT 
                product_name,
                product_price
            FROM products
            WHERE product_id=?
        """, (product_id,)).fetchone()

        # product data
        product_name = product["product_name"]
        price = product["product_price"]

        # calculate item total
        item_total = price * float(quantity)

        # create cart item
        cart_item = {
            "product_id": product_id,
            "product_name": product_name,
            "quantity": quantity,
            "price": price,
            "total": item_total
        }

        # get current cart
        cart = session["cart"]

        # add item to cart
        cart.append(cart_item)

        # save updated cart
        session["cart"] = cart
        session.modified = True

        conn.close()

        return redirect(url_for("orders"))

    # =========================
    # GET (LOAD PAGE)
    # =========================

    products = conn.execute("""
        SELECT 
            product_id,
            product_name,
            product_price,
            product_category
        FROM products
        WHERE is_active = 1
    """).fetchall()

    stock = conn.execute("""
        SELECT 
            p.product_name,
            p.product_unit,
            p.product_price,
            w.quantity
        FROM products p

        JOIN warehouse_stock w
        ON p.product_id = w.product_id

        WHERE p.is_active = 1
    """).fetchall()

    categories = conn.execute("""
        SELECT DISTINCT product_category
        FROM products
        WHERE is_active = 1
    """).fetchall()

    conn.close()

    # calculate grand total
    grand_total = sum(item["total"] for item in session.get("cart", []))

    return render_template(
        "orders.html",
        products=products,
        stock=stock,
        cart=session.get("cart", []),
        grand_total = grand_total,
        categories=categories
    )

#submit order
@app.route("/submit_order", methods=["POST"])
def submit_order():
    conn = get_db_connection()
    cursor = conn.cursor()

    #get cart items
    cart = session.get("cart", [])

    #if its empty cart
    if not cart:
        flash("Your cart is empty.", "warning")
        return redirect(url_for("orders"))

    #user data
    user_role = session.get("role")
    store_id = session.get("store_id")

    #role logic
    if user_role == "manager":
        status = "Submitted"
    else:
        status = "Pending"

    # calculate grand total
    grand_total = sum(item["total"] for item in cart)

    # create order
    cursor.execute("""
        INSERT INTO orders (
            store_id,
            order_date,
            order_status,
            total
        )
        VALUES (?, ?, ?, ?)
    """, (
        store_id,
        datetime.now(),
        status,
        grand_total
    ))

    # get new order id
    order_id = cursor.lastrowid

    # insert order items
    for item in cart:
        requested_qty = float(item["quantity"])

        # get current warehouse stock
        stock = conn.execute("""
            SELECT quantity
            FROM warehouse_stock
            WHERE product_id = ?
        """, (item["product_id"],)).fetchone()

        # not enough stock
        if requested_qty > stock["quantity"]:
            flash(
                f"Not enough stock for {item['product_name']}. Available stock: {stock['quantity']}",
                "error"
            )

            conn.close()

            # clear invalid cart
            session["cart"] = []
            session.modified = True

            return redirect(url_for("orders"))

        cursor.execute("""
            INSERT INTO order_items (
                order_id,
                product_id,
                quantity
            )
            VALUES (?, ?, ?)
        """, (
            order_id,
            item["product_id"],
            item["quantity"]
        ))

    # update warehouse stock ONLY for submitted
    if status == "Submitted":
        update_warehouse_stock(conn, order_id)

    conn.commit()
    conn.close()

    # clear cart
    session["cart"] = []
    session.modified = True

    # success message
    if status == "Submitted":
        flash("Order submitted successfully", "success")
    else:
        flash("Order saved as Pending approval")

    return redirect(url_for("orders"))




@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=True)