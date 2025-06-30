# scheduler_logic.py
import pandas as pd
from models import Schedule, BUILDINGS, EXCLUDED_LAB_ROOMS # This is fine
import datetime
from sqlalchemy import or_

def get_available_time_slots(day, db_session): # <--- This function
    all_rooms_info = []
    for building_name, building_data in BUILDINGS.items():
        for floor_num, rooms_on_floor in building_data['floors'].items():
            for room_name in rooms_on_floor:
                all_rooms_info.append({
                    'building': building_name,
                    'floor': floor_num,
                    'room_name': room_name
                })

    room_availability = {}
    time_slots = []
    # Generate time slots every hour from 08:00 to 22:00
    for hour in range(8, 23): # Range up to 22 means 22:00 is the last start time
        time_slots.append(datetime.time(hour, 0))

    # Initialize all rooms as 'Tersedia' for all time slots
    for room_info in all_rooms_info:
        full_room_name = f"{room_info['building']} - Lantai {room_info['floor']} - {room_info['room_name']}"
        room_availability[full_room_name] = [{'time': t, 'status': 'Tersedia'} for t in time_slots]

    # Ambil jadwal yang ada untuk hari yang dipilih
    existing_schedules = db_session.query(Schedule).filter_by(day=day, class_type='Offline').all()

    # Mark occupied time slots
    for sched in existing_schedules:
        full_room_name = f"{sched.building} - Lantai {sched.floor} - {sched.room}"
        if full_room_name in room_availability:
            for i, slot in enumerate(room_availability[full_room_name]):
                slot_time = slot['time']
                # Check if the start of the slot time is within the existing schedule's duration
                # or if the existing schedule starts within this slot time.
                # A simple check for a 1-hour slot: if slot_time falls within sched duration
                if (slot_time >= sched.start_time and slot_time < sched.end_time):
                    room_availability[full_room_name][i]['status'] = 'Terpakai'

    # Mark break time (12:00-13:00) for all rooms
    break_start = datetime.time(12, 0)
    break_end = datetime.time(13, 0)

    for room_name in room_availability:
        for i, slot in enumerate(room_availability[room_name]):
            slot_time = slot['time']
            if slot_time >= break_start and slot_time < break_end:
                room_availability[room_name][i]['status'] = 'Istirahat'
    
    return room_availability