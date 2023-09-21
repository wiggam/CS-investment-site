from flask import Flask, jsonify, render_template, session, redirect, request
from werkzeug.security import check_password_hash, generate_password_hash
from utils import db_select, db_update, login_required, get_name, get_price, update_data
from keys import secret_key

# create Flask app
app = Flask(__name__, template_folder='templates')

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"

# Set a secret key for session management
app.secret_key = secret_key


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route('/')
@login_required
def index():

    # read contents of db_last_updated
    with open('db_last_updated.txt', 'r') as file:
        last_updated = file.read()

    return render_template('index.html', user_authenticated=True, last_updated=last_updated)


@app.route('/instructions')
def instructions():

    user_authenticated = False
    if session['user_id']:
        user_authenticated = True

    return render_template('instructions.html', user_authenticated=user_authenticated)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return render_template("login.html", login_error=True)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return render_template("login.html", login_error=True)

        # Query database for username
        query = "SELECT * FROM login WHERE username = ?"
        username = request.form.get("username")
        rows = db_select(query, (username,))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return render_template("login.html", login_error=True)

        # Remember which user has logged in
        session["user_id"] = rows[0]["user_id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html", login_error=False)


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return render_template("register.html", login_error1=True)

        # Ensure password and confirmation were submitted
        elif not request.form.get("password") or not request.form.get("confirmation"):
            return render_template("register.html", login_error2=True)

        # Ensure password and confirmation match
        elif request.form.get("password") != request.form.get("confirmation"):
            return render_template("register.html", login_error3=True)

        # Check for duplicate username
        query = "SELECT * FROM login WHERE username = ?"
        params = request.form.get("username")
        rows = db_select(query, (params,))
        if len(rows) >= 1:
            return render_template("register.html", login_error4=True)

        # Add user to db
        query = "INSERT INTO login (username, hash) VALUES (?, ?)"
        params = [request.form.get("username"), generate_password_hash(
            request.form.get("password"))]
        db_update(query, params)

        # Redirect user to login
        return redirect("/login")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


@app.route('/get_data')
@login_required
def get_data_from_db():

    query = "SELECT * FROM inventory WHERE user_id = ?"
    params = session["user_id"]
    data = db_select(query, (params,))

    return jsonify(data)


@app.route('/search', methods=['POST'])
@login_required
def search_items():
    search_query = request.form.get('search_query')

    # Perform a database query to retrieve data based on the search query
    data_query = "SELECT * FROM inventory WHERE item_name LIKE ? AND user_id = ?"
    params = ('%' + search_query + '%', session['user_id'])
    data = db_select(data_query, params)

    # Calculate new totals for the filtered data
    totals_query = "SELECT SUM(number_of_items) as number_of_items, SUM(total_cost) as total_cost, SUM(total_value) as total_value, SUM(total_return_dollar) as total_return_dollar FROM inventory WHERE item_name LIKE ? AND user_id = ?"
    totals_data = db_select(totals_query, params)
    # Just send the dictionary
    totals_data = totals_data[0]

    # Add total return percent
    totals_data['total_return_percent'] = round(
        (totals_data['total_return_dollar'] / totals_data['total_cost']) * 100, 2)

    # Round values
    for key, value in totals_data.items():
        totals_data[key] = round(value, 2)

    # Return both data sets as JSON
    return jsonify({'data': data, 'totals': totals_data})


@app.route('/get_totals')
@login_required
def get_totals():
    query = "SELECT SUM(number_of_items) as number_of_items, SUM(total_cost) as total_cost, SUM(total_value) as total_value, SUM(total_return_dollar) as total_return_dollar FROM inventory WHERE user_id = ?"
    params = session['user_id']
    data = db_select(query, (params,))

    if data and data[0]['total_cost'] is not None and data[0]['total_return_dollar'] is not None:
        # Just send dictionary
        data = data[0]

        # Calculate and add total return percent
        if data['total_cost'] > 0:
            data['total_return_percent'] = round(
                (data['total_return_dollar'] / data['total_cost']) * 100, 2)
        else:
            data['total_return_percent'] = 0.0

        # Round values
        for key, value in data.items():
            data[key] = round(value, 2)
    else:
        # Handle case where data is None or some values are None
        data = {
            'number_of_items': 0,
            'total_cost': 0.0,
            'total_value': 0.0,
            'total_return_dollar': 0.0,
            'total_return_percent': 0.0
        }

    return jsonify(data)


@app.route('/edit_item/<item_id>', methods=['POST'])
@login_required
def edit_item(item_id):

    # check if loggedin user matches the user_id of the item
    query = "SELECT * FROM inventory WHERE user_id = ? AND item_number = ?"
    params = [session['user_id'], item_id]
    if not db_select(query, params):
        return {'error': 'User cannot access this item'}, 404

    try:
        # get row
        edited_data = request.get_json()

        # make sure all data is supplied
        for key, value in edited_data.items():
            if value == '':
                return {'error': f'{key} cannot be left empty'}, 400

        print(edited_data)
        edited_data = update_data(edited_data)

        if edited_data == 1:
            return {'message': 'COST PER ITEM, CURRENT PRICE, and NUMBER OF ITEMS must be numbers'}, 400

        # Construct the SQL query based on the edited_data dictionary
        query = "UPDATE inventory SET "
        params = []

        for key, value in edited_data.items():
            query += f"{key} = ?, "
            params.append(value)

        query = query.rstrip(', ')  # Remove the trailing comma and space
        query += " WHERE item_number = ?"  # Assuming item_number is the primary key

        # Append the item_id to the params list
        params.append(item_id)

        # Execute the dynamic SQL query
        result = db_update(query, params)

        if result == 0:
            return {'message': f'Item {item_id} updated successfully'}, 200
        else:
            return {'error': f'Item {item_id} not found or update failed'}, 404

    except Exception as e:
        return {'error': 'An error occurred while updating the item'}, 500


@app.route("/delete_item/<item_id>", methods=['POST'])
@login_required
def delete_item(item_id):

    # check if logged-in user matches the user_id of the item
    query = "SELECT * FROM inventory WHERE user_id = ? AND item_number = ?"
    params = [session['user_id'], item_id]
    if not db_select(query, params):
        return {'error': 'User cannot access this item'}, 404

    try:
        # update inventory table
        query = "DELETE FROM inventory WHERE item_number = ?"
        params = item_id
        result = db_update(query, (params,))

        if result == 0:
            return {'message': f'Item {item_id} deleted successfully'}, 200
        else:
            return {'message': f'Item {item_id} not found or delete failed'}, 404

    except Exception as e:
        print(e)
        return {'error': 'An error occurred while updating the item'}, 500


@app.route("/add_item", methods=['POST'])
@login_required
def add_item():

    try:
        new_data = request.get_json()

        # add name to data if not supplied
        if not "item_name" in new_data:
            new_data['item_name'] = get_name(new_data['item_link'])
            if new_data['item_name'] == '':
                return {'message': 'Error getting name from link, please ensure link is correct'}, 400

        # add current price to data if not supplied
        if not "current_price" in new_data:
            new_data['current_price'] = get_price(new_data['item_link'])

        # get user_id
        new_data['user_id'] = session['user_id']

        new_data = update_data(new_data)
        if new_data == 1:
            return {'message': 'COST PER ITEM, CURRENT PRICE, and NUMBER OF ITEMS must be numbers'}, 400

        # update inventory table
        query = """INSERT INTO inventory (date, cost_per_item, number_of_items, item_link, item_name, current_price, user_id, total_cost, total_value, total_return_dollar, total_return_percent)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
        params = []
        for key, value in new_data.items():
            params.append(value)

        inv_result = db_update(query, params)

        if inv_result == 0:
            return {'message': 'Item added successfully'}, 200
        else:
            return {'message': 'Error'}, 500

    except Exception as e:
        print("Error")
        return {'message': f'Error {e}'}, 500


if __name__ == '__main__':
    app.run(debug=True)
