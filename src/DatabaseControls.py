from supabase import Client

def time_to_seconds(time: str):
    components = time.split(":")

    seconds = 0
    for i in range(len(components)):
        seconds += int(components[i]) * 60 ** (2 - i)
    return seconds

def create_reservation(database_client: Client, reference_name: str, instruments: list[str], date: str, start_time: str, end_time: str):
    session = database_client.auth.get_session()

    same_day_reservations = (database_client.from_("reservations")
                             .select("*")
                             .eq("date", date)
                             .execute())

    is_valid_reservation = True

    start_time_seconds = time_to_seconds(start_time)
    end_time_seconds = time_to_seconds(end_time)

    for reservation in same_day_reservations.data:
        reservation_start_time_seconds = time_to_seconds(reservation["start_time"])
        reservation_end_time_seconds = time_to_seconds(reservation["end_time"])

        if not ((start_time_seconds > reservation_end_time_seconds) or (end_time_seconds < reservation_start_time_seconds)):
            is_valid_reservation = False; break

    if is_valid_reservation:
        database_client.from_("reservations").insert([
            {
                "name_under": reference_name,
                "made_by": session.user.id,
                "instruments": list(map(lambda x: str(x), instruments)),
                "date": date, 
                "start_time": start_time, 
                "end_time": end_time
            }
        ]).execute()

    return is_valid_reservation