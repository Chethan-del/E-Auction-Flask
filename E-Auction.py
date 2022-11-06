from flask import Flask, render_template, request, url_for, redirect, session, flash
from flask_mysqldb import MySQL
from datetime import date
from base64 import b64encode

app = Flask(__name__)
app.secret_key = "EAuction"

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'chethan@123'
app.config['MYSQL_DB'] = 'e_auction'

mysql = MySQL(app)

@app.route("/")
def home():
    # Displays Home Page
    return render_template("Home.html")

@app.route("/sign_up", methods=['GET', 'POST'])
# Used for Sign_Up
def sign_up():
    if request.method == 'POST':
        # stores the values entered in form
        fname = request.form['First_name']
        lname = request.form['Last_name']
        password = request.form['password']
        email = request.form['mail']
        user_name = request.form['User_name']
        phone_number = request.form['phone']
        gender = request.form['gender']
        cur = mysql.connection.cursor()
        # Inserts the Form entered values Into login and user tables
        cur.execute("Insert Into login_cred (mail,password) values (%s,%s)", (email, password))
        cur.execute("INSERT INTO user (first_name,last_name,user_name,gender, phone_number, mail) VALUES (%s,%s,%s,%s,%s,%s)",(fname, lname, user_name,gender,phone_number, email))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('login'))
    return render_template("Sign_up.html")

@app.route("/login", methods=['GET', 'POST'])
def login():
    data = 0
    if request.method == 'POST':
        password = request.form['password']
        email = request.form['mail']
        session["email"] = email

        cur = mysql.connection.cursor()
        cur.execute("select *from login_cred")
        login_data = cur.fetchall()
        cur.close()

        # Checks whether the email is present in table
        for i in login_data:
            if(i[0] == email and i[1] == password):
                flash("You have successfully logged in", "info")
                return redirect(url_for('auction'))
            else:
                data = 0
    elif "email" in session:
        # Checks whether we have already logged in
        flash("You have already logged in", "info")
        return redirect(url_for('auction'))

    return render_template("login.html", search = data)

@app.route("/sell_now", methods=['GET', 'POST'])
# Used to sell products
def sell_now():
    if request.method == "POST":
        email = session["email"]
        file = request.files['u_img']
        file_name = file.filename or ''
        b_status = 'N'                      # initially bid status is null
        category = request.form['category']
        product_name = request.form['name']
        description = request.form['description']
        int_amount = request.form['price']
        last_date = request.form['date']
        cur = mysql.connection.cursor()
        cur.execute('select user_id from user where mail=%s', [email])
        user_id = cur.fetchall()
        # Inserts form entered product details in product table
        cur.execute("insert into product (product_name, description, amount, last_date, user_id, category, item,bid_status) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",(product_name, description, int_amount, last_date, user_id[0][0], category, file_name, b_status))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('accounts'))
    return render_template("selling_product_now.html")

@app.route("/payments_done", methods=['GET', 'POST'])
# Displays the details of payment done by user
def payments_done():
    email = session["email"]
    cur = mysql.connection.cursor()
    cur.execute("select p.payment_id, p.product_id, p.bid_price from payment p where p.user_id in (select  U.user_id from user U where U.mail=%s)", [email])
    rec_payment_details = cur.fetchall()
    return render_template("payments_done.html", payment_details = rec_payment_details)

@app.route("/payment_tab/<prod_id>", methods=['GET', 'POST'])
# Used to display payment payment_tab page
def payment_tab(prod_id):
    email = session["email"]
    cur = mysql.connection.cursor()
    # Fetches bidding_price from bidded table to display on the page
    cur.execute("select bidded_price from bidded b where product_id = %s ", [prod_id])
    price = cur.fetchall()[0]
    cur.execute("select product_name,user_id from product where product_id = %s ", [prod_id])
    pro = cur.fetchall()[0]
    if request.method == "POST":
        feedback = request.form['feedback']
        cur = mysql.connection.cursor()
        cur.execute("select user_id from user where mail = %s", [email])
        u_id = cur.fetchall()[0][0]
        # After click on pay button insertion is done in payment table
        cur.execute("insert into payment (user_id,product_id,bid_price,feedback) VALUES (%s,%s,%s,%s)",(u_id, prod_id, price[0], feedback))
        mysql.connection.commit()
        return redirect(url_for('payments'))
    return render_template("payment_tab.html", details=price, product_id = prod_id, pro = pro)

@app.route("/payments", methods=['GET', 'POST'])
# Used to display payment_due page
def payments():
    email = session["email"]
    cur = mysql.connection.cursor()
    # Fetches details from bidded table for payments due page
    cur.execute("select b.product_id, b.bidded_price from bidded b where b.payment_status = 'N' and b.user_id in (select user_id from user where mail = %s)",[email])
    payment_details = cur.fetchall()
    cur.close()
    return render_template("payments.html", payment_details = payment_details)

@app.route("/sold", methods=['GET', 'POST'])
# Used to display selling page
# Details include only products that are 'IN-BID'
def sold():
    email = session["email"]
    cur = mysql.connection.cursor()
    cur.execute('select p.product_id, p.amount, p.last_date from product p, user u where p.user_id = u.user_id and u.mail = %s and p.bid_status = "N" group by p.product_id',[email])
    sold_data = cur.fetchall()
    cur.close()
    return render_template("sold_product.html", sold_data = sold_data)

@app.route("/bidded", methods=['GET', 'POST'])
# Used to show the Bid_Won page
def bidded():
    email = session["email"]
    cur = mysql.connection.cursor()
    # Fetches details from bidded table based on user_id
    cur.execute('select b.product_id, b.bidded_price from bidded b where b.user_id in (select u.user_id from user u where u.mail = %s) order by b.product_id',[email])
    bid = cur.fetchall()
    return render_template("Bidded.html", bid = bid)

@app.route("/bidded_inbid", methods=['GET', 'POST'])
# Used to show Your_Bidding page
def bidded_inbid():
    email = session["email"]
    cur = mysql.connection.cursor()
    # Fetches data from bidding table based on user_id
    cur.execute('select b.product_id, b.cur_price from bidding b where b.user_id in (select u.user_id from user u where u.mail = %s) order by b.product_id',[email])
    bid = cur.fetchall()
    return render_template("Bidded_Inbid.html", bid = bid)

@app.route("/accounts", methods=['GET', 'POST'])
def accounts():
    #Used to display Accounts Page
    return render_template("Account.html")

@app.route("/details", methods=['GET', 'POST'])
# Used to display Details Page
def details():
    email = session["email"]
    cur = mysql.connection.cursor()
    cur.execute('select *from user where mail=%s', [email])
    details = cur.fetchall()
    cur.close()
    return render_template("Details.html", details = details)

@app.route("/auction", methods=['GET', 'POST'])
# Used to display Auction page
def auction():
    cur = mysql.connection.cursor()
    # Fetches details from product table whose products are not yet bidded
    cur.execute('select p.product_id, p.product_name,p.last_date from product p where category = "Digital-Art" and p.bid_status = "N"')
    art = cur.fetchall()
    cur.execute('select p.product_id, p.product_name,p.last_date from product p where category = "Mobile" and p.bid_status = "N"')
    mobile = cur.fetchall()
    cur.execute('select p.product_id, p.product_name, p.last_date from product p where category = "Laptop" and p.bid_status = "N"')
    laptop = cur.fetchall()
    cur.execute('select p.product_id, p.product_name, p.last_date from product p where category = "Book" and p.bid_status = "N"')
    book = cur.fetchall()
    cur.close()
    return render_template("Bidding_place.html", mobile = mobile, art = art, laptop = laptop, book = book)

@app.route("/product_view/<id>", methods=['GET', 'POST'])
# Used to display product_view page
def product_view(id):
    email = session["email"]
    cur = mysql.connection.cursor()

    # Fetches details for product_view
    cur.execute('select product_id, product_name, description, last_date, item from product where product_id = %s', [id])
    product_data = cur.fetchall()

    cur.execute('select user_id from user where mail=%s', [email])
    u_id = cur.fetchall()
    cur.close()

    if str(product_data[0][3]) <= str(date.today()): # when last_date equals current date
        p_status = 'N'
        cur = mysql.connection.cursor()
        # Fetches maximum of current price as a product will have multiple entries in bidding
        cur.execute('select max(cur_price) from bidding where product_id = %s and user_id = %s',[id,u_id[0][0]])
        cu = cur.fetchall()
        # After last_date expires bidding is closed and product is inserted in bidded table
        cur.execute("insert into bidded (product_id,bidded_price,user_id,payment_status) VALUES (%s,%s,%s,%s)",[id,cu[0][0],u_id[0][0],p_status])
        mysql.connection.commit()
        cur.close()

    cur = mysql.connection.cursor()
    # Fetches maximum cur_price from bidding in descending order
    cur.execute('select b.cur_price from bidding b where b.product_id = %s order by b.cur_price DESC', [id])
    bid_data = cur.fetchall()

    cur.execute('select amount from product where product_id = %s',[id])
    price = cur.fetchall()[0][0]

    if request.method == 'POST':
        bid_amount = request.form['bid_amount']
        '''try:
            if str(bid_data[0][0]) >= bid_amount:
                flash("Your bid is less than current bid", "info")
                return redirect(url_for('product_view', id=id))
        except:
            if price >= bid_amount:
                flash("Your bid is less than current bid", "info")
                return redirect(url_for('product_view', id=id))'''
        cur = mysql.connection.cursor()
        # Checking if product present in bidding table and if not present cur_price == bidded_amount
        # If present it updates the respective product in bidding
        cur.execute('select bid_id from bidding where product_id = %s and user_id in (select u.user_id from user u where u.mail = %s)',[id, email])
        check_present = cur.fetchall()
        cur.close()
        if check_present == (()):
            cur = mysql.connection.cursor()
            cur.execute('select p.product_id from product p where p.product_id = %s', [id])
            value = cur.fetchall()
            user_id = int(u_id[0][0])
            product_id = int(value[0][0])
            cur.execute("insert into bidding (cur_price,product_id,user_id) VALUES (%s,%s,%s)",(bid_amount, product_id, user_id))
            mysql.connection.commit()
            cur.close()
            return redirect(url_for('accounts'))
        else:
            cur = mysql.connection.cursor()
            cur.execute('UPDATE bidding join product on product.product_id = bidding.product_id set bidding.cur_price = %s where product.product_id = %s and bidding.user_id = %s',[bid_amount, id, u_id])
            mysql.connection.commit()
            cur.close()

    return render_template("Product_view.html", product_details = product_data, cur_price = bid_data, price = price)

@app.route("/logout")
def logout():
    # Used to logout from the session
    if "email" not in session:
        flash("You have already logged out", "info")
        return redirect(url_for('home'))
    else:
        session.pop("email", None)
        flash("You have succesfully logged out", "info")
        return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug = True)