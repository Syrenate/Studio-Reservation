import os, supabase
from flask import Flask, request, url_for, redirect
from supabase import create_client, Client, SupabaseAuthClient
from supabase import SupabaseAuthClient as auth
from dotenv import load_dotenv

load_dotenv("src/vars.env")
app = Flask(__name__)

supabase_client: Client = create_client(
    os.environ.get("SUPABASE_URL"),
    os.environ.get("SUPABASE_PUBLISHABLE_KEY")
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

def click_button():
    print("clicked")


def DisplayDataTable(name: str):
    response = supabase_client.table(name).select("*").execute()
    data = response.data

    html = '<style> table, th, td { border: 1px solid black; } </style>'
    html += f'<h1>{name}</h1><table><tr>'

    print(data)
    try:
        for column in data[0].keys():
            html += f'<th>{column}</th>'
        html += '</tr>'
    except IndexError as e:
        print("Database is empty!")
        return None

    for row in data:
        html += '<tr>'
        for column in row.keys():
            html += f'<td>{row[column]}</td>'
        html += '</tr>'
    html += '</tr></table>'

    return html


@app.route('/')
def index():
    #html = "<button onclick=click_button()>Click here</button>"
    html = ""
    for table in ["instruments", "accounts", "reservations"]:
        html += DisplayDataTable(table) + "<br>"
    return html

@app.route('/signup', methods = ["GET", "POST"])
def signup():
    if request.method == "GET":
        return open("src/pages/signup.html").read()

    email = request.form["email"]
    password = request.form["pass"]

    auth.sign_up(supabase_client, credentials={
        email,
        password,
    })


    redirect(url_for("login"))


@app.route('/login', methods = ["GET", "POST"])
def login():
    return open("src/pages/login.html").read()

    

if __name__ == '__main__':
    #supabase_client.table("reservations").delete().eq("id", 1).execute()
    #add_reservation(1, [1,2], )

    app.run(debug=True)