import mysql.connector
from flask import Flask, request, jsonify, render_template, redirect, url_for
from random import randint
from datetime import datetime
import time

app = Flask(__name__)

def runQuery(query, params=None):
    try:
        db = mysql.connector.connect(
            host='localhost', 
            database='event_mgmt', 
            user='root', 
            password='HarperMC2003'
        )
        cursor = db.cursor(buffered=True)
        cursor.execute(query, params)
        
        if query.strip().lower().startswith("select"):
            result = cursor.fetchall()
        else:
            db.commit()
            result = []

        return result

    except Exception as e:
        print(f"Database error: {e}")
        return []

    finally:
        db.close()

@app.route('/', methods=['GET', 'POST'])
def renderLoginPage():
    events = runQuery("SELECT * FROM events")

    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['e_mail']
        phone_num = request.form['phone_num']
        event_id = request.form['Event']
        ticket_type = request.form['ticket_type']
        payment_type = request.form['payment_type']

        # Validate phone number
        if len(phone_num) != 10 or not phone_num.isdigit():
            return render_template('loginfail.html', errors=["Invalid Phone Number!"])

        # Validate email
        if not email.endswith('.com'):
            return render_template('loginfail.html', errors=["Invalid Email!"])

        try:
            # Insert the customer into the Customer table
            runQuery("INSERT INTO Customer (first_name, last_name, e_mail, phone_num) VALUES (%s, %s, %s, %s)",
                     (first_name, last_name, email, phone_num))

            # Retrieve the customer ID
            customer_id = runQuery("SELECT ID FROM Customer WHERE e_mail = %s", (email,))[0][0]
            print(f"Customer ID: {customer_id}")

            # Fetch event details for price
            event = runQuery("SELECT general_price, vip_price FROM events WHERE ID = %s", (event_id,))[0]
            if ticket_type == 'General':
                price = event[0]
            else:
                price = event[1]

            # Assign a random distributor ID between 1 and 24
            distributor_id = randint(1, 24)

            # Insert a new ticket record
            runQuery("INSERT INTO TICKET (type, tickets_available, tickets_sold, price, event_id, distributer_id) VALUES (%s, %s, %s, %s, %s, %s)",
                     (ticket_type, 100, 1, price, event_id, distributor_id))

            # Retrieve the ticket ID
            ticket_id = runQuery("SELECT ID FROM TICKET ORDER BY ID DESC LIMIT 1")[0][0]
            print(f"Ticket ID: {ticket_id}")

            # Insert a new purchase record
            runQuery("INSERT INTO Purchase (customer_id, ticket_id, payment_type, purchase_date) VALUES (%s, %s, %s, %s)",
                     (customer_id, ticket_id, payment_type, datetime.now()))
            print("Purchase record inserted successfully.")

            # Retrieve the purchase ID
            purchase_id = runQuery("SELECT LAST_INSERT_ID()")[0][0]
            print(f"Purchase ID: {purchase_id}")

        except Exception as e:
            print(f"Error: {str(e)}")
            return render_template('loginfail.html', errors=["Database error: " + str(e)])

        return render_template('index.html', events=events, errors=["Successfully Registered!"])

    return render_template('index.html', events=events)



@app.route('/loginfail', methods=['GET'])
def renderLoginFail():
    return render_template('loginfail.html')

@app.route('/admin', methods=['GET', 'POST'])
def renderAdmin():
    if request.method == 'POST':
        UN = request.form['username']
        PS = request.form['password']

        if UN == 'admin' and PS == 'admin':
            return redirect('/eventType')

        return render_template('admin.html', errors=["Wrong Username/Password"])

    return render_template('admin.html')

@app.route('/eventType', methods=['GET', 'POST'])
def getEvents():
    if request.method == 'POST':
        try:
            if 'newEvent' in request.form:
                Name = request.form["newEvent"]
                fee = request.form["Fee"]
                #participants = request.form["maxP"]
                Type = request.form["EventType"]
                Location = request.form["EventLocation"]
                Date = request.form['Date']
                #runQuery("INSERT INTO events(event_title, event_price, participants, type_id, location_id, date) VALUES(%s, %s, %s, %s, %s, %s)", (Name, fee, participants, Type, Location, Date))
            elif 'EventId' in request.form:
                EventId = request.form["EventId"]
                runQuery("DELETE FROM events WHERE event_id=%s", (EventId,))
        except mysql.connector.Error as e:
            print(f"Error: {e}")

    events = runQuery("SELECT * FROM events")
    companies = runQuery("SELECT * FROM Company")
    distributers = runQuery("SELECT * FROM Distributer")
    customers = runQuery("SELECT * FROM Customer")
    tickets = runQuery("SELECT * FROM Ticket")
    purchases = runQuery("SELECT * FROM Purchase")
    cust_of = runQuery("SELECT * FROM cust_of")

    return render_template('events.html', events=events, companies=companies, distributers=distributers, customers=customers, tickets=tickets, purchases=purchases, cust_of=cust_of)

@app.route('/manage_distributers', methods=['GET', 'POST'])
def manage_distributers():
    if request.method == "POST":
        if 'ID' in request.form and 'name' in request.form  and 'location' in request.form:
            try:
                distributer_id = request.form["ID"]
                name = request.form["name"]
                location = request.form["location"]
                
                runQuery("INSERT INTO Distributer (ID, name, location) VALUES (%s, %s, %s)", (distributer_id, name, location))
                print(f"Distributer added: {distributer_id}, {name}")
                
            except Exception as e:
                print(f"Error adding distributer: {e}")
        
        elif 'DistributerID' in request.form:
            try:
                distributer_id = request.form["DistributerID"]
                runQuery("DELETE FROM Distributer WHERE ID = %s", (distributer_id,))
                print(f"Distributer deleted: {distributer_id}")
            except Exception as e:
                print(f"Error deleting distributer: {e}")

    events = runQuery("SELECT * FROM events")
    companies = runQuery("SELECT * FROM Company")
    distributers = runQuery("SELECT * FROM Distributer")
    customers = runQuery("SELECT * FROM Customer")
    tickets = runQuery("SELECT * FROM Ticket")
    purchases = runQuery("SELECT * FROM Purchase")
    cust_of = runQuery("SELECT * FROM cust_of")

    return render_template('events.html', events=events, companies=companies, distributers=distributers, customers=customers, tickets=tickets, purchases=purchases, cust_of=cust_of)

@app.route('/manage_customers', methods=['GET', 'POST'])
def manage_customers():
    if request.method == "POST":
        if 'ID' in request.form and 'first_name' in request.form  and 'last_name' in request.form and 'e_mail' in request.form and 'phone_num' in request.form:
            try:
                customer_id = request.form["ID"]
                first_name = request.form["first_name"]
                last_name = request.form["last_name"]
                e_mail = request.form["e_mail"]
                phone_num = request.form["phone_num"]

                runQuery("INSERT INTO Customer (ID, first_name, last_name, e_mail, phone_num) VALUES (%s, %s, %s, %s, %s)", (customer_id, first_name, last_name, e_mail, phone_num))
                print(f"Customer added: {customer_id}, {first_name}, {last_name}")
                
            except Exception as e:
                print(f"Error adding customer: {e}")
        
        elif 'CustomerID' in request.form:
            try:
                customer_id = request.form["CustomerID"]
                runQuery("DELETE FROM Customer WHERE ID = %s", (customer_id,))
                print(f"Customer deleted: {customer_id}")
            except Exception as e:
                print(f"Error deleting Customer: {e}")

    events = runQuery("SELECT * FROM events")
    companies = runQuery("SELECT * FROM Company")
    distributers = runQuery("SELECT * FROM Distributer")
    customers = runQuery("SELECT * FROM Customer")
    tickets = runQuery("SELECT * FROM Ticket")
    purchases = runQuery("SELECT * FROM Purchase")
    cust_of = runQuery("SELECT * FROM cust_of")

    return render_template('events.html', events=events, companies=companies, distributers=distributers, customers=customers, tickets=tickets, purchases=purchases, cust_of=cust_of)

@app.route('/manage_companies', methods=['GET', 'POST'])
def manage_companies():
    if request.method == "POST":
        if 'ID' in request.form and 'name' in request.form  and 'location' in request.form:
            try:
                company_id = request.form["ID"]
                name = request.form["name"]
                location = request.form["location"]
                
                runQuery("INSERT INTO Company (ID, name, location) VALUES (%s, %s, %s)", (company_id, name, location))
                print(f"Company added: {company_id}, {name}")
                
            except Exception as e:
                print(f"Error adding event: {e}")
        
        elif 'CompanyID' in request.form:
            try:
                company_id = request.form["CompanyID"]
                runQuery("DELETE FROM Company WHERE ID = %s", (company_id,))
                print(f"Company deleted: {company_id}")
            except Exception as e:
                print(f"Error deleting event: {e}")

    events = runQuery("SELECT * FROM events")
    companies = runQuery("SELECT * FROM Company")
    distributers = runQuery("SELECT * FROM Distributer")
    customers = runQuery("SELECT * FROM Customer")
    tickets = runQuery("SELECT * FROM Ticket")
    purchases = runQuery("SELECT * FROM Purchase")
    cust_of = runQuery("SELECT * FROM cust_of")

    return render_template('events.html', events=events, companies=companies, distributers=distributers, customers=customers, tickets=tickets, purchases=purchases, cust_of=cust_of)

@app.route('/manage_tickets', methods=['GET', 'POST'])
def manage_tickets():
    if request.method == "POST":
        if 'ID' in request.form and 'type' in request.form  and 'tickets_available' in request.form and 'tickets_sold' in request.form and 'price' in request.form and 'event_id' in request.form and 'distributer_id' in request.form:
            # Handle Add Event
            try:
                ticket_id = request.form["ID"]
                type = request.form["type"]
                tickets_available = request.form["tickets_available"]
                tickets_sold = request.form["tickets_sold"]
                price = request.form["price"]
                event_id = request.form["event_id"]
                distributer_id = request.form["distributer_id"]


                
                query = f"""
                INSERT INTO TICKET (ID, type, tickets_available,tickets_sold,price,event_id,distributer_id)
                VALUES ({ticket_id}, '{type}','{tickets_available}','{tickets_sold}','{price}','{event_id}','{distributer_id}');
                """
                runQuery(query)
                
                print(f"Ticket added: {ticket_id}, {price},{distributer_id}")
                
            except Exception as e:
                print(f"Error adding ticket: {e}")
        
        elif 'TicketID' in request.form:
            # Handle Delete Event
            try:
                ticket_id = request.form["TicketID"]
                runQuery(f"DELETE FROM TICKET WHERE ID = {ticket_id}")
                print(f"Ticket deleted: {ticket_id}")
            except Exception as e:
                print(f"Error deleting ticket: {e}")

    events = runQuery("SELECT * FROM events")
    companies = runQuery("SELECT * FROM Company")
    distributers = runQuery("SELECT * FROM Distributer")
    customers = runQuery("SELECT * FROM Customer")
    tickets = runQuery("SELECT * FROM Ticket")
    purchases = runQuery("SELECT * FROM Purchase")
    cust_of = runQuery("SELECT * FROM cust_of")

    return render_template('events.html', events=events, companies=companies, distributers=distributers, customers=customers, tickets=tickets, purchases=purchases, cust_of=cust_of)

@app.route('/manage_purchase', methods=['GET', 'POST'])#problem var
def manage_purchase():
    if request.method == "POST":
        if 'purchase_id' in request.form and 'customer_id' in request.form  and 'ticket_id' in request.form and 'payment_type' in request.form and 'purchase_date' in request.form:
            # Handle Add Event
            try:
                purchase_id = request.form["purchase_id"]
                customer_id = request.form["customer_id"]
                ticket_id = request.form["ticket_id"]
                payment_type = request.form["payment_type"]
                purchase_date = request.form["purchase_date"]

                
                query = f"""
                INSERT INTO Purchase (purchase_id, customer_id, ticket_id,payment_type,purchase_date)
                VALUES ({purchase_id}, '{customer_id}','{ticket_id}','{payment_type}','{purchase_date}');
                """
                runQuery(query)
                
                print(f"Purchase added: {purchase_id}, {customer_id},{ticket_id}")
                
            except Exception as e:
                print(f"Error adding purchase: {e}")
        
        elif 'PurchaseID' in request.form:
            # Handle Delete Event
            try:
                purchase_id = request.form["PurchaseID"]
                runQuery(f"DELETE FROM Purchase WHERE ID = {purchase_id}")
                print(f"Purchase deleted: {purchase_id}")
            except Exception as e:
                print(f"Error deleting Purchase: {e}")

    events = runQuery("SELECT * FROM events")
    companies = runQuery("SELECT * FROM Company")
    distributers = runQuery("SELECT * FROM Distributer")
    customers = runQuery("SELECT * FROM Customer")
    tickets = runQuery("SELECT * FROM Ticket")
    purchases = runQuery("SELECT * FROM Purchase")
    cust_of = runQuery("SELECT * FROM cust_of")

    return render_template('events.html', events=events, companies=companies, distributers=distributers, customers=customers, tickets=tickets, purchases=purchases, cust_of=cust_of)
@app.route('/manage_cust_of', methods=['GET', 'POST'])
def manage_cust_of():
    if request.method == "POST":
        if 'company_id' in request.form and 'customer_id' in request.form:
            try:
                company_id = request.form["company_id"]
                customer_id = request.form["customer_id"]
                
                runQuery("INSERT INTO cust_of (company_id, customer_id) VALUES (%s, %s)", (company_id, customer_id))
                print(f"cust_of added: {company_id}, {customer_id}")
                
            except Exception as e:
                print(f"Error adding cust_of: {e}")
        
        elif 'CustOfID' in request.form:
            try:
                cust_of_id = request.form["CustOfID"]
                runQuery("DELETE FROM cust_of WHERE company_id = %s AND customer_id = %s", (company_id, customer_id))
                print(f"cust_of deleted: {cust_of_id}")
            except Exception as e:
                print(f"Error deleting cust_of: {e}")

    events = runQuery("SELECT * FROM events")
    companies = runQuery("SELECT * FROM Company")
    distributers = runQuery("SELECT * FROM Distributer")
    customers = runQuery("SELECT * FROM Customer")
    tickets = runQuery("SELECT * FROM Ticket")
    purchases = runQuery("SELECT * FROM Purchase")
    cust_of = runQuery("SELECT * FROM cust_of")

    return render_template('events.html', events=events, companies=companies, distributers=distributers, customers=customers, tickets=tickets, purchases=purchases, cust_of=cust_of)

@app.route('/manage_events', methods=['GET', 'POST'])
def manage_events():
    if request.method == "POST":
        if 'ID' in request.form and 'name' in request.form and 'type' in request.form and 'location' in request.form and 'income' in request.form and 'expense' in request.form and 'datetime' in request.form and 'details' in request.form and 'company_id' in request.form and 'general' in request.form and 'vipp' in request.form:
            # Handle Add Event
            try:
                event_id = request.form["ID"]
                name = request.form["name"]
                event_type = request.form["type"]
                location = request.form["location"]
                event_datetime = request.form["datetime"]
                general = request.form["general"]
                vip = request.form["vipp"]
                income = request.form["income"]
                expense = request.form["expense"]
                details = request.form["details"]
                company_id = request.form["company_id"]
                
                query = f"""
                INSERT INTO events (ID, name, type, location, datetime,general_price,vip_price, income, expense, details, company_id)
                VALUES ({event_id}, '{name}', '{event_type}', '{location}', '{event_datetime}', '{general}', '{vip}', '{income}', '{expense}', '{details}', {company_id});
                """
                runQuery(query)
                
                print(f"Event added: {event_id}, {name}")
                
            except Exception as e:
                print(f"Error adding event: {e}")
        
        elif 'EventId' in request.form:
            # Handle Delete Event
            try:
                event_id = request.form["EventId"]
                runQuery(f"DELETE FROM events WHERE ID = {event_id}")
                print(f"Event deleted: {event_id}")
            except Exception as e:
                print(f"Error deleting event: {e}")

    events = runQuery("SELECT * FROM events")
    companies = runQuery("SELECT * FROM Company")
    distributers = runQuery("SELECT * FROM Distributer")
    customers = runQuery("SELECT * FROM Customer")
    tickets = runQuery("SELECT * FROM Ticket")
    purchases = runQuery("SELECT * FROM Purchase")
    cust_of = runQuery("SELECT * FROM cust_of")

    return render_template('events.html', events=events, companies=companies, distributers=distributers, customers=customers, tickets=tickets, purchases=purchases, cust_of=cust_of)

if __name__ == '__main__':
    app.run(debug=True)
