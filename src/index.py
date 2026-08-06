from flask import Flask, request, url_for, redirect, render_template
from SupabaseConnect import LoadClient, Client
from DatabaseControls import create_reservation

app = Flask(__name__)
supabase_client = LoadClient()
    
## Utils

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


## Page Routes

@app.route('/', methods = ["GET", "POST"])
def root():
    if request.method == "POST":
        account_request = account_request_handle()
        if account_request != None: return account_request
        
        if request.form.get('view_reservations') != None:
            return redirect_to("reservations")
        if request.form.get('view_instruments') != None:
            return redirect_to("instruments")

    return render_page("display/root")


@app.route('/register', methods = ["GET", "POST"])
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


@app.route('/login', methods = ["GET", "POST"])
def login():
    if request.method == "POST":
        account_request = account_request_handle()
        if account_request != None: return account_request

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

@app.route('/logout', methods = ["GET", "POST"])
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


def render_reservation_page(error_msg: str = ""):
    all_reservations = supabase_client.from_("reservations").select("*").execute()
    all_instruments = supabase_client.from_("instruments").select("*").execute()

    return render_template("display/reservations.html", 
                           session = supabase_client.auth.get_session(),
                           reservations = all_reservations.data,
                           instruments = all_instruments.data) + f"<br><br><label>{error_msg}</label>"


@app.route('/reservations', methods = ["GET", "POST"])
def reservations():
    if request.method == "POST":
        account_request = account_request_handle()
        if account_request != None: return account_request

        if request.form.get('back') != None:
            return redirect_to("root")

        if request.form.get('submit_reservation') != None:
            instruments = request.form.get('instrument_select')
            print(instruments)

            created = create_reservation(database_client=supabase_client,
                    reference_name=request.form.get('name'), 
                    instruments=instruments, 
                    date=request.form.get('date'), 
                    start_time=request.form.get('start_time'), 
                    end_time=request.form.get('end_time')
                )

            if not created:
                error_msg = "This reservation clashes with an existing reservation! Please choose another timeslot."
                return render_reservation_page(error_msg)

    return render_reservation_page()

@app.route("/instruments", methods=["GET", "POST"])
def instruments():
    if request.method == "POST":
        account_request = account_request_handle()
        if account_request != None: return account_request

        if request.form.get('back') != None:
            return redirect_to("root")

    all_instruments = supabase_client.from_("instruments").select("*").execute()
    return render_template("display/instruments.html", instruments=all_instruments.data)




if __name__ == '__main__':
    app.run(debug=True) 