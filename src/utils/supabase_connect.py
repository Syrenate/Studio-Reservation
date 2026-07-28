import os
from flask import Flask, request, url_for, redirect
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv("src/vars.env")
app = Flask(__name__)

supabase_client: Client = create_client(
    supabase_url=os.environ.get("SUPABASE_URL"),
    supabase_key=os.environ.get("SUPABASE_PUBLISHABLE_KEY")
)


def add_reservation(user_id: int, instruments: list[int], date: str, start_time: str, end_time: str):
    supabase_client.from_("reservations").insert([
        {
            "account_id": user_id,
            "instruments": list(map(lambda x: str(x), instruments)),
            "date": date, 
            "start_time": start_time, 
            "end_time": end_time
        }
    ]).execute()

def DisplayDataTable(name: str):
    response = supabase_client.table(name).select("*").execute()

    camel_name = ' '.join([word[0].upper() + word[1:] for word in name.split(" ")])

    html = '<style> table, th, td { border: 1px solid black; } </style>'
    html += f'<h1>{camel_name}</h1><table><tr>'

    try:
        for column in response.data[0].keys():
            html += f'<th>{column}</th>'
        html += '</tr>'
    except IndexError as e:
        print(f"Database {name} is empty!")
        return ""

    for row in response.data:
        html += '<tr>'
        for column in row.keys():
            html += f'<td>{row[column]}</td>'
        html += '</tr>'
    html += '</tr></table>'

    return html

@app.route('/', methods = ["GET", "POST"])
def root():
    session = supabase_client.auth.get_session()

    if request.method == "GET":
        if session == None: html = open("src/pages/root_unlogged.html").read() 
        else:               html = f"Logged in as: {session.user.user_metadata["full_name"]} " + open("src/pages/root_logged.html").read()

        for table in ["instruments", "reservations"]:
            html += DisplayDataTable(table) + "<br>"
        return html

    if request.form.get('signout') != None:
        response = supabase_client.auth.sign_out()
        return redirect(url_for("root"), Response="GET")
    elif request.form.get('signin') != None:
        return redirect(url_for("signin"), Response="GET")
    elif request.form.get('signup') != None:
        return redirect(url_for("signup"), Response="GET")


@app.route('/signup', methods = ["GET", "POST"])
def signup():
    if request.method == "GET":
        return open("src/pages/signup.html").read()

    if request.form.get('back') == "Back":
        return redirect(url_for("root"), Response="GET")
    
    
    print(request.form["email"], request.form["pass"])
    response = supabase_client.auth.sign_up(credentials={
        "email": request.form["email"],
        "password": request.form["pass"],
        "options": {
            "data": {
                "full_name": request.form["name"]
            }
        }
    })

    return redirect(url_for("signin"), Response="GET")


@app.route('/signin', methods = ["GET", "POST"])
def signin():
    if request.method == "GET":
        return open("src/pages/signin.html").read()

    if request.form.get('back') == "Back":
        return redirect(url_for("root"), Response="GET")
    
    response = supabase_client.auth.sign_in_with_password(credentials={
        "email": request.form["email"],
        "password": request.form["pass"]
    })

    return redirect(url_for("root"), Response="GET")

    

if __name__ == '__main__':
    #supabase_client.table("reservations").delete().eq("id", 1).execute()
    #add_reservation(1, [1,2], )

    app.run(debug=True)