import os
from flask import Flask, request, url_for, redirect, render_template
from supabase import create_client, Client, AuthInvalidCredentialsError
from dotenv import load_dotenv

load_dotenv("dep/vars.env")
flask_app = Flask(__name__)

supabase_client: Client = create_client(
    supabase_url=os.environ.get("SUPABASE_URL"),
    supabase_key=os.environ.get("SUPABASE_PUBLISHABLE_KEY")
)

page_data = {}

def time_to_seconds(time: str):
    components = time.split(":")
    seconds = 0
    length = len(components)
    
    for i in range(length):
        seconds += int(components[i]) * (60 ** (length - i - 1))
    return seconds

def create_reservation(reference_name: str, instruments: list[str], date: str, start_time: str, end_time: str):
    session = supabase_client.auth.get_session()

    same_day_reservations = (supabase_client.from_("reservations")
                             .select("*")
                             .eq("date", date)
                             .execute())

    valid_reservation = True

    start_time_seconds = time_to_seconds(start_time)
    end_time_seconds = time_to_seconds(end_time)

    for reservation in same_day_reservations.data:
        reservation_start_time_seconds = time_to_seconds(reservation["start_time"])
        reservation_end_time_seconds = time_to_seconds(reservation["end_time"])

        if not ((start_time_seconds > reservation_end_time_seconds) or (end_time_seconds < reservation_start_time_seconds)):
            valid_reservation = False; break

    if valid_reservation:
        supabase_client.from_("reservations").insert([
            {
                "name_under": reference_name,
                "made_by": session.user.id,
                "instruments": list(map(lambda x: str(x), instruments)),
                "date": date, 
                "start_time": start_time, 
                "end_time": end_time
            }
        ]).execute()

    return valid_reservation

def DisplayDataTable(client: Client, name: str):
    response = client.from_(name).select("*").execute()

    camelcase_name = ' '.join([word[0].upper() + word[1:] for word in name.split(" ")])

    html = '<style> table, th, td { border: 1px solid black; } </style>'
    html += f'<h1>{camelcase_name}</h1><table><tr>'

    try: # Data may be empty, so data[0] throws an IndexError.
        for column in response.data[0].keys():
            html += f'<th>{column}</th>'
        html += '</tr>'
    except IndexError: return ""

    for row in response.data:
        row_html = [f'<td>{value}</td>' for value in row.values()]
        html += '<tr>' + ''.join(row_html) + '</tr>'
    html += '</tr></table>'

    return html


### Page Methods

def render_page(path: str):
    full_path = f"{path}.html"

    session = supabase_client.auth.get_session()
    if session != None: return render_template(full_path, session=session)
    else:               return render_template(full_path)

def redirect_to(page: str):
    return redirect(url_for(page))

def account_request_handle():
    session = supabase_client.auth.get_session()
    return redirect_to('login')    if request.form.get('login')    and session == None else \
           redirect_to('register') if request.form.get('register') and session == None else \
           redirect_to('logout')   if request.form.get('logout')   and session != None else None

@flask_app.route('/', methods = ["GET", "POST"])
def root():
    account_request = account_request_handle()
    if account_request != None and request.method == "POST": return account_request

    if request.method == "POST":
        if request.form.get('view_reservations') != None:
            return redirect_to("reservations")

    return render_page("display/root")


@flask_app.route('/register', methods = ["GET", "POST"])
def register():
    if request.method == "POST":
        account_request = account_request_handle()
        if account_request != None: return account_request


        if request.form.get('back') != None: 
            return redirect_to("root")

        if request.form.get('submit') != None:
            supabase_client.auth.sign_up(credentials={
                "email": request.form["email"],
                "password": request.form["pass"],
                "options": {
                    "data": {
                        "full_name": request.form["name"]
                    }
                }
            })

    return render_page("auth/register")


@flask_app.route('/login', methods = ["GET", "POST"])
def login():
    if request.method == "POST":

        if request.form.get('back') != None: 
            return redirect_to("root")

        if request.form.get('submit') != None:
            try:
                supabase_client.auth.sign_in_with_password(credentials={
                    "email": request.form["email"],
                    "password": request.form["pass"]
                })

                return redirect_to("root")
            except: pass

    return render_page("auth/login")

@flask_app.route('/logout', methods = ["GET", "POST"])
def logout():
    if request.method == "POST":
        account_request = account_request_handle()
        if account_request != None: return account_request

        if request.form.get("yes") != None:
            supabase_client.auth.sign_out()

            return redirect_to("root")
        if request.form.get("no") != None:
            return redirect_to("root")

    return render_page("auth/logout")



@flask_app.route('/reservations', methods = ["GET", "POST"])
def reservations():
    account_request = account_request_handle()
    if account_request != None: return account_request

    if request.method == "POST":
        account_request = account_request_handle()
        if account_request != None: return account_request

        if request.form.get('back') != None:
            return redirect_to("root")

        if request.form.get('submit_reservation') != None:
            reference_name = request.form.get('name')
            date = request.form.get('date')
            start_time = request.form.get('start_time')
            end_time = request.form.get('end_time')
            instruments = request.form.get('instruments')

            created = create_reservation(
                    reference_name=reference_name, 
                    instruments=instruments, 
                    date=date, 
                    start_time=start_time, 
                    end_time=end_time
                )

            if not created:
                return render_page("display/reservations") + '<br><br><label>This reservation clashes with an existing reservation! Please choose another timeslot.</label>'


    all_reservations = supabase_client.from_("reservations").select("*").execute()
    all_instruments = supabase_client.from_("instruments").select("*").execute()

    return render_template("display/reservations.html", 
                           session=supabase_client.auth.get_session(),
                           reservations = all_reservations.data,
                           instruments = all_instruments.data)

if __name__ == '__main__':
    flask_app.run(debug=True) 