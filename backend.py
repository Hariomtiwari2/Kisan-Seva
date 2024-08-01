from flask import Flask, render_template, request, send_from_directory, redirect, url_for, session, flash, jsonify, json
from models.crop_ml import predict_crop  # crop_ml.py has a predict function
import os
import pandas as pd
from pymongo import MongoClient
from flask_bcrypt import Bcrypt
from bson.objectid import ObjectId
from bson import json_util
import razorpay
from datetime import datetime
import logging
from logging.handlers import RotatingFileHandler
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import ssl
import certifi
from models.yield_test import predict_yield

app = Flask(__name__)
bcrypt = Bcrypt(app)
app.secret_key = 'VS7*BCPs8*$bY463!b&U#PC@T66MnF'  # Change this to a real secret in production

# MongoDB setup 
client = MongoClient('mongodb+srv://obiwan:b3fvAm9boMZwZAn8@kisanseva.r803jgh.mongodb.net/?retryWrites=true&w=majority&appName=KisanSeva')  # Update the URI as per your MongoDB setup
# client = MongoClient('mongodb://localhost:27017/')
db = client['KisanSeva']  # Database name
users = db['users']  # Collection for users
transactions = db['transactions']  # Collection for transactions

# Temp otp storing
otp_store = {}

# Set up logging
log_file_handler = RotatingFileHandler('app.log', maxBytes=100000, backupCount=3)
log_file_handler.setLevel(logging.DEBUG)
log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log_file_handler.setFormatter(log_formatter)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(log_file_handler)

# Razorpay setup
razorpay_client = razorpay.Client(auth=("rzp_test_BPrcISiqCRRTx4", "Sti1T5fv3F8oAgUKKN9LXkNn"))

# Initialize the database and collections
def initialize_db():
    # Check if the 'visitors' collection exists and create it if it doesn't
    if 'visitors' not in db.list_collection_names():
        visitors = db.create_collection('visitors')
        # Initialize the visitors counter for the index page
        visitors.insert_one({'page': 'index', 'count': 1510})
    
    # Ensure the users collection exists and has appropriate indexes
    if 'users' not in db.list_collection_names():
        users = db.create_collection('users')
        users.create_index('username', unique=True)
    else:
        # Ensure all users have the 'transactions' field; do not overwrite if it exists
        db.users.update_many(
            {'transactions': {'$exists': False}},
            {'$set': {'transactions': []}}
        )
    
    # Ensure the 'marketplace' collection exists
    if 'marketplace' not in db.list_collection_names():
        db.create_collection('marketplace')

    # Ensure the 'transactions' collection exists
    if 'transactions' not in db.list_collection_names():
        db.create_collection('transactions')

#app.before_request_funcs = [(None, initialize_db())]

@app.route("/", methods=["GET"])  # Route for displaying the form
def index():
    db.visitors.update_one({'page': 'index'}, {'$inc': {'count': 1}})
    visitor_count = db.visitors.find_one({'page': 'index'})['count']
    return render_template("index.html", visitor_count=visitor_count)


@app.route('/account', methods=['GET'])
def account():
    visitor_count = db.visitors.find_one({'page': 'index'})['count']
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']
    user = db.users.find_one({'username': username})

    if user:
        # Ensure all timestamps are datetime objects
        transactions = user.get('transactions', [])
        for transaction in transactions:
            if isinstance(transaction['timestamp'], str):
                transaction['timestamp'] = datetime.strptime(transaction['timestamp'], "%Y-%m-%d %H:%M:%S")
        
        # Sort transactions by timestamp in descending order
        user['transactions'] = sorted(transactions, key=lambda x: x['timestamp'], reverse=True)

    return render_template('account.html', user=user, visitor_count=visitor_count)


@app.route('/account', methods=['GET', 'POST'])
def update_account():
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']
    user = db.users.find_one({'username': username})

    if request.method == 'POST':
        email = request.form.get('email')
        phone = request.form.get('phone')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        address = request.form.get('address')

        update_fields = {}
        if email:
            update_fields['email'] = email
        if phone:
            update_fields['phone'] = phone
        if first_name:
            update_fields['first_name'] = first_name
        if last_name:
            update_fields['last_name'] = last_name
        if address:
            update_fields['address'] = address

        if update_fields:
            db.users.update_one({'username': username}, {'$set': update_fields})

        flash('Account information updated successfully', 'success')

    # Sort transactions by timestamp in descending order
    user['transactions'] = sorted(user['transactions'], key=lambda x: x['timestamp'], reverse=True)

    return render_template('account.html', user=user)


def send_email(recipient, subject, body):
    sender = 'kisanseva13@gmail.com'
    password = 'nlor xkrk almo qtau'
    
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = recipient

    # Create SSL context with specific SSL version
    context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
    context.options |= ssl.OP_NO_TLSv1  # Exclude TLSv1
    context.options |= ssl.OP_NO_TLSv1_1  # Exclude TLSv1.1

    with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as server:
        # Login to the email server
        server.login(sender, password)
        # Send the email
        server.sendmail(sender, [recipient], msg.as_string())

@app.route("/send_otp", methods=["POST"])
def send_otp():
    data = request.json
    email = data['email']
    otp = random.randint(100000, 999999)
    otp_store[email] = otp
    send_email(email, 'Your Kisan Seva OTP Code', f'Your OTP code is {otp}')
    return jsonify({'status': 'success'})

@app.route("/verify_otp", methods=["POST"])
def verify_otp():
    data = request.json
    email = data['email']
    otp = int(data['otp'])
    if email in otp_store and otp_store[email] == otp:
        del otp_store[email]
        return jsonify({'status': 'success'})
    return jsonify({'status': 'fail'})

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        email = request.form.get("email")
        user = users.find_one({"username": username})
        if user:
            flash('Username already exists!', 'warning')
            return redirect(url_for('signup'))
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        users.insert_one({"username": username, "password": hashed_password, "email": email})
        flash('Account created successfully! Please login.', 'success')
        return redirect(url_for('login'))
    return render_template("signup.html")

@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = users.find_one({"username": username})
        if user and bcrypt.check_password_hash(user["password"], password):
            session['username'] = username
            session['logged_in'] = True
            flash('You were successfully logged in.', 'success')

            # Check if there's a product ID stored in the session for checkout
            if 'redirect_to_checkout' in session:
                product_id = session.pop('redirect_to_checkout')
                return redirect(url_for('checkout', product_id=product_id))
            else:
                return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'danger')
            return redirect(url_for('login'))  # Redirect back to the login page
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop('username', None)
    session.pop('admin', None)
    session['logged_in'] = False
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))


@app.route('/predict')
def predict():
    visitor_count = 1  # Replace with actual visitor count from database if needed
    return render_template('yield_predict.html', visitor_count=visitor_count)

@app.route('/predict_yield', methods=['POST'])
def predict_yield_route():
    Crop = request.form['Crop']
    user_land_area = float(request.form['land_area'])
    State = "Uttar Pradesh"
    if Crop == "Rice" or Crop == "Maize" or Crop == "Cotton(lint)":
        Season = "Kharif"
    elif Crop == "Wheat":
        Season = "Rabi"
    elif Crop == "Sugarcane" or Crop == "Potato":
        Season = "Whole Year"
    
    Annual_Rainfall = 758.3  # Average expected rainfall of uttar pradesh in mm
    
    final_production, predicted_yield = predict_yield(Season, State, Crop, Annual_Rainfall, user_land_area)
    
    result = f"Predicted Yield of {Crop} for Next Season on {user_land_area} Bighas: {final_production * 1000:.2f} kg"
    
    return render_template('yield_predict.html', result=result)


@app.route('/ads.txt')
def ads_txt():
    # Adjust the path if your ads.txt is located elsewhere
    return send_from_directory(app.static_folder, 'ads.txt')

@app.route('/kisan_seva_logo')
def website_logo():
    # Providing the correct path to the 'index' folder inside the 'static' folder
    directory_path = os.path.join(app.static_folder, 'index')
    return send_from_directory(directory_path, 'kisan_seva_logo.png')

@app.route('/marketplace')
def marketplace():
    visitor_count = db.visitors.find_one({'page': 'index'})['count']
    return render_template('marketplace/marketplace.html', visitor_count=visitor_count)

@app.route('/products')
def products_home():
    visitor_count = db.visitors.find_one({'page': 'index'})['count']

    # Fetch all unique categories from the database
    categories = db.marketplace.distinct('category')
    products_by_category = {category: [] for category in categories}

    # Fetch products for each category
    for category in categories:
        products = db.marketplace.find({'category': category})
        products_by_category[category] = list(products)

    return render_template('marketplace/products_home.html', visitor_count=visitor_count, products_by_category=products_by_category)

@app.route('/privacy_policy')
def privacy_policy():
    visitor_count = db.visitors.find_one({'page': 'index'})['count']
    return render_template('privacy_policy.html', visitor_count=visitor_count)

@app.route('/terms_and_conditions')
def terms_and_conditions():
    visitor_count = db.visitors.find_one({'page': 'index'})['count']
    return render_template('terms_and_conditions.html', visitor_count=visitor_count)

@app.route('/disclaimer')
def disclaimer():
    visitor_count = db.visitors.find_one({'page': 'index'})['count']
    return render_template('disclaimer.html', visitor_count=visitor_count)

@app.route('/articles_home')
def articles_home():
    visitor_count = db.visitors.find_one({'page': 'index'})['count']
    return render_template('articles_home.html', visitor_count=visitor_count)

@app.route('/article_1')
def article_1():
    visitor_count = db.visitors.find_one({'page': 'index'})['count']
    return render_template('articles/organic_farming.html', visitor_count=visitor_count)

@app.route('/about')
def about():
    visitor_count = db.visitors.find_one({'page': 'index'})['count']
    return render_template('about.html', visitor_count=visitor_count)

@app.route('/sitemap.xml')
def sitemap():
    return send_from_directory(directory=os.path.join(app.root_path, 'static'), path='sitemap.xml')

@app.route('/mission')
def mission():
    visitor_count = db.visitors.find_one({'page': 'index'})['count']
    return render_template('mission&vision.html', visitor_count=visitor_count)

# Razorpay Integration

@app.route('/checkout/<product_id>', methods=['GET'])
def checkout(product_id):
    visitor_count = db.visitors.find_one({'page': 'index'})['count']
    product = db.marketplace.find_one({"_id": ObjectId(product_id)})
    if 'username' in session:
        # Fetch the user's information from MongoDB
        username = session['username']
        user = db.users.find_one({'username': username})
        # debugging user collection
        # logger.debug(f"{session[username]}")
        if user:
            # Pass the user's information to the template rendering the checkout page
            return render_template('payment_gateway/checkout.html', product=product, user=user, visitor_count=visitor_count)
        
    if product:
        # Check if the user is logged in
        if 'username' in session:
            return render_template('payment_gateway/checkout.html', product=product, user=user, visitor_count=visitor_count)
        else:
            # If the user is not logged in, save the product ID in the session and redirect to the login page
            session['redirect_to_checkout'] = product_id
            return redirect(url_for('login'))

    return render_template('checkout.html', product=product,user=user, visitor_count=visitor_count)



@app.route('/process_checkout', methods=['GET', 'POST'])
def process_checkout():
    visitor_count = db.visitors.find_one({'page': 'index'})['count']
    if request.method == 'POST':
        product_name = request.form.get('product_name')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        contact = request.form.get('contact')
        address = request.form.get('address')
        state = request.form.get('state')
        address = request.form.get('address')
        order_amount = int(request.form.get('amount')) * 100  # Convert to paise
        order_currency = 'INR'
        order_receipt = 'order_rcptid_11'
        
        # Create order in Razorpay
        razorpay_order = razorpay_client.order.create({
            'amount': order_amount,
            'currency': order_currency,
            'receipt': order_receipt
        })

        order_id = razorpay_order['id']
        order_status = razorpay_order['status']

        if order_status == 'created':
            return render_template('payment_gateway/pay.html', 
                                    order_id=order_id,
                                    product_name=product_name, 
                                    amount=order_amount, 
                                    currency=order_currency,
                                    first_name=first_name,
                                    last_name=last_name,
                                    email=email,
                                    contact=contact,
                                    state=state,
                                    address=address)
        else:
            return "Order creation failed", 500
    return render_template('payment_gateway/checkout.html', visitor_count=visitor_count)

@app.route('/payment_success', methods=['POST'])
def payment_success():
    logger.debug(f"Received POST data: {request.form}")

    # Collecting parameters from the request
    razorpay_payment_id = request.form.get('razorpay_payment_id')
    razorpay_order_id = request.form.get('razorpay_order_id')
    razorpay_signature = request.form.get('razorpay_signature')
    product_id = request.form.get('product_id')

    logger.debug(f"Payment success initiated with payment_id: {razorpay_payment_id}, order_id: {razorpay_order_id}")

    if not (razorpay_payment_id and razorpay_order_id and razorpay_signature):
        logger.error("Payment verification failed. Required data missing.")
        flash("Payment verification failed. Required data missing.", "danger")
        if product_id:
            return redirect(url_for('checkout', product_id=product_id))
        return redirect(url_for('products_home'))  # Redirect to home or an error page if product_id is missing

    try:
        params_dict = {
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_order_id': razorpay_order_id,
            'razorpay_signature': razorpay_signature
        }

        # Verifying the payment signature
        result = razorpay_client.utility.verify_payment_signature(params_dict)

        logger.debug("Payment verified successfully")

        # Collecting transaction details from the form to send confirmation email
        product_name = request.form.get('product_name')
        amount_paise = int(request.form.get('amount'))
        amount_rupees = amount_paise / 100  # Convert paise to rupees
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        contact = request.form.get('contact')
        state = request.form.get('state')
        address = request.form.get('address')
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Add transaction details to the user's account
        transaction_details_in_user = {
            'transaction_id': razorpay_payment_id,
            'order_id': razorpay_order_id,
            'amount': amount_rupees,
            'product_name': product_name,
            'state': state,
            'address': address,
            'timestamp': timestamp
        }


        # Add transaction details in the Transactions collection
        transaction_details_in_transactions = {
            'transaction_id': razorpay_payment_id,
            'order_id': razorpay_order_id,
            'username': session['username'],  # Add the username to the transaction details
            'contact': contact,
            'Type': 'Marketplace Purchase',
            'amount': amount_rupees,
            'product_name': product_name,
            'state': state,
            'address': address,
            'timestamp': timestamp
        }

        logger.debug(f"Transaction details to be inserted: {transaction_details_in_transactions}")

        # Update the transaction details in the Users collection
        update_result_in_users = db.users.update_one(
            {'username': session['username']},
            {'$push': {'transactions': transaction_details_in_user}}
        )

        # Log the transaction details in the Users collection
        if update_result_in_users.modified_count > 0:
            logger.debug("Transaction details updated successfully in the Users collection")
        else:
            logger.error("Failed to update transaction details in the Users collection")


        # Insert the transaction details into the Transactions collection
        insert_result_in_transactions = db.transactions.insert_one(transaction_details_in_transactions)

        # Log the transaction details in the Transactions collection
        if insert_result_in_transactions.inserted_id:
            logger.debug("Transaction details inserted successfully in the Transactions collection")
        else:
            logger.error("Failed to insert transaction details in the Transactions collection")


        # Prepare and send the order confirmation email
        email_subject = "Order Confirmation"
        email_body = f"""
        <html>
        <body>
            <h2>Order Confirmation</h2>
            <p>Dear {first_name} {last_name},</p>
            <p>Thank you for your purchase! Here are your order details:</p>
            <table border="1" cellpadding="5" cellspacing="0">
                <tr>
                    <th>Product Name</th>
                    <td>{product_name}</td>
                </tr>
                <tr>
                    <th>Transaction ID</th>
                    <td>{razorpay_payment_id}</td>
                </tr>
                <tr>
                    <th>Order ID</th>
                    <td>{razorpay_order_id}</td>
                </tr>
                <tr>
                    <th>Amount Paid</th>
                    <td>₹{amount_rupees:.2f}</td>
                </tr>
                <tr>
                    <th>Address</th>
                    <td>{address}, {state}</td>
                </tr>
                <tr>
                    <th>Timestamp</th>
                    <td>{timestamp}</td>
                </tr>
            </table>
            <p>If you have any questions or need further assistance, please feel free to contact us.</p>
            <p>Best regards,<br>Kisan Seva Team</p>
        </body>
        </html>
        """

        send_email(email, email_subject, email_body)
        logger.debug("Order confirmation email sent successfully")


        flash("Payment was successful!", "success")
        return redirect(url_for('account'))  # Redirect to the account info page

    except razorpay.errors.SignatureVerificationError as e:
        logger.error(f"Razorpay Signature Verification Failed: {e}")
        flash("Razorpay Signature Verification Failed", "danger")
        if product_id:
            return redirect(url_for('checkout', product_id=product_id))
        return redirect(url_for('products_home'))  # Redirect to home or an error page if product_id is missing

# send order confirmation email
def send_email(recipient, subject, body):
    sender = 'kisanseva13@gmail.com'
    password = 'nlor xkrk almo qtau'
    
    msg = MIMEMultipart()
    msg['From'] = sender
    msg['To'] = recipient
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'html'))

    # Create SSL context with specific SSL version
    context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
    context.options |= ssl.OP_NO_TLSv1  # Exclude TLSv1
    context.options |= ssl.OP_NO_TLSv1_1  # Exclude TLSv1.1

    with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as server:
        # Login to the email server
        server.login(sender, password)
        # Send the email
        server.sendmail(sender, [recipient], msg.as_string())


if __name__ == "__main__":
    initialize_db()  # Initialize the database collections and fields
    app.run(debug=True)