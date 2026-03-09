import sqlite3

conn = sqlite3.connect("jobs.db", check_same_thread=False)

def get_cursor():
    return conn.cursor()

def get_queue_data():
    # Initialise cursor
    cur = get_cursor()
    statuses = ["Received", "Printing", "Printed"]
    queue = {}
    # Iterate through each status and add to queue dict by position
    for status in statuses:
        jobs = cur.execute("SELECT id, customer_name, file_name, assigned_user, status, position, file_path, errors FROM jobs WHERE status=? ORDER BY position ASC", (status,)).fetchall()
        queue[status] = jobs
    return queue

def insert_job(file_name, position=None, assigned_user="Unassigned", file_path="", customer_name="Manual", errors=""):
    cur = get_cursor()
    # Get position value
    jobs = cur.execute("SELECT position FROM jobs ORDER BY position ASC").fetchall()
    # If no jobs, insert with pos 1
    if position:
        if len(jobs) == 0:
            pos = 1.0
        # If inserting into first position, take pos of top job and subtract 1
        elif position == 1:
            pos = jobs[0][0] - 1
        # If inserting into last position, take pos of bottom job and add 1
        elif position > len(jobs):
            pos = jobs[-1][0] + 1
        # If inserting between jobs, take pos of next and previous jobs and average
        else:
            pos = (jobs[position-2][0] + jobs[position-1][0])/2
    else:
        pos = jobs[-1][0] + 1
    
    cur.execute("INSERT INTO jobs (customer_name, file_name, file_path, assigned_user, position, errors) VALUES (?, ?, ?, ?, ?, ?)", (customer_name, file_name, file_path, assigned_user, pos, errors))
    conn.commit()

def remove_job(job_id):
    cur = get_cursor()
    cur.execute("DELETE FROM jobs WHERE id=?", (job_id, ))
    conn.commit()

def update_status(job_id, status):
    cur = get_cursor()
    cur.execute("UPDATE jobs SET status=? WHERE id=?", (status, job_id))
    conn.commit()
    
def get_job(job_id):
    cur = get_cursor()
    job = cur.execute("SELECT customer_name, file_name, file_path, assigned_user, status, position, errors FROM jobs WHERE id=?", (job_id, )).fetchone()
    return job

def update_assigned(job_id, user):
    cur = get_cursor()
    cur.execute("UPDATE jobs SET assigned_user=? WHERE id=?", (user, job_id))
    conn.commit()

def update_file_path(file_path, job_id):
    cur = get_cursor()
    cur.execute("UPDATE jobs SET file_path=? WHERE id=?", (file_path, job_id))
    conn.commit()