import sqlite3
from functools import wraps
from flask import redirect, session
from urllib.parse import unquote
from urllib import request
import json
import datetime
import time


def db_select(query, params=None):
    # Create a connection to the database
    conn = sqlite3.connect('inventory.sqlite')

    # Create a cursor object to execute the SQL query
    cursor = conn.cursor()

    # execute query
    if params:
        cursor.execute(query, params)
    else:
        cursor.execute(query)

    # Fetch all the rows from the query result
    rows = cursor.fetchall()

    # Get the column names from the cursor description
    column_names = [desc[0] for desc in cursor.description]

    # Create a list of dictionaries where each dictionary represents a row
    result = [dict(zip(column_names, row)) for row in rows]

    # Close the cursor and connection
    cursor.close()
    conn.close()

    return result


def db_update(query, params):
    conn = sqlite3.connect('inventory.sqlite')
    cursor = conn.cursor()
    try:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        conn.commit()  # Commit the changes for DELETE or UPDATE
        return 0
    except sqlite3.Error as e:
        conn.rollback()  # Rollback changes if there's an error
        return 1
    finally:
        cursor.close()
        conn.close()


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            # User is not logged in, redirect to the login page
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def get_name(item_link: str) -> str:
    item_name = item_link[47:]
    return unquote(item_name)


def get_price(item_link: str) -> int:
    # Implement logic to retrieve and return the item's price
    try:
        market_hash_name = item_link[47:]
        target_url = "https://steamcommunity.com/market/priceoverview/?appid=730&currency=1&market_hash_name=" \
            + market_hash_name
        url_request = request.urlopen(target_url)
        data = json.loads(url_request.read().decode())
        item_price = str(data.get('lowest_price'))
        item_price = float(item_price.replace('$', ''))
    except:
        item_price = 0

    return item_price


def update_data(data):
    # Check if cost_per_item, current_price, and number_of_items can be converted to integers
    try:
        float(data['cost_per_item'])
        float(data['current_price'])
        float(data['number_of_items'])
    except ValueError:
        return 1

    # convert items into floats if they can be floats
    for key, value in data.items():
        try:
            data[key] = float(value)
        except Exception:
            pass

    # populate calculated fields
    data['total_cost'] = round(
        data['number_of_items'] * data['cost_per_item'], 2)
    data['total_value'] = round(
        data['number_of_items'] * data['current_price'], 2)
    data['total_return_dollar'] = round(
        data['total_value'] - data['total_cost'], 2)
    data['total_return_percent'] = round(
        (data['total_return_dollar'] / data['total_cost']) * 100, 2)

    return data


def update_inventory_prices():
    # Fetch all unique links from the inventory table
    links_query = "SELECT DISTINCT item_link FROM inventory"
    unique_links = db_select(links_query)

    counter = 0
    for link in unique_links:
        link = link['item_link']
        new_price = get_price(link)

        # Update the inventory table with the new current price
        update_query = "UPDATE inventory SET current_price = ? WHERE item_link = ?"
        update_params = (new_price, link)
        db_update(update_query, update_params)

        time.sleep(4.5)  # dont over use API or will get timed out
        counter += 1
        print(counter)

    # update total value, return $ and %
    items_query = "SELECT * FROM inventory"
    items = db_select(items_query)

    for item in items:
        new_item = update_data(item)

        query = "UPDATE inventory SET "
        params = []

        for key, value in new_item.items():
            query += f"{key} = ?, "
            params.append(value)

        query = query.rstrip(', ')  # Remove the trailing comma and space
        query += " WHERE item_number = ?"  # Assuming item_number is the primary key

        params.append(item['item_number'])

        # Execute the SQL query
        result = db_update(query, params)
        if result != 0:
            return 'Error updating db'

    est_timezone = datetime.timezone(datetime.timedelta(hours=-5))
    est_time = datetime.datetime.now(est_timezone)
    with open('db_last_updated.txt', 'w') as file:
        file.write(
            f"Database was last updated at {est_time.strftime('%Y-%m-%d %H:%M:%S')} EST")

    return 0
