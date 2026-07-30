import os, dotenv
from supabase import create_client, Client

dotenv.load_dotenv("dep/vars.env")

def LoadClient():
    supabase_client: Client = create_client(
        supabase_url = os.environ.get("SUPABASE_URL"),
        supabase_key = os.environ.get("SUPABASE_PUBLISHABLE_KEY")
    )

    return supabase_client