import os

from functools import wraps

from datetime import datetime



import psycopg2

from psycopg2.extras import RealDictCursor

from flask import Flask, flash, redirect, render_template_string, request, session, url_for

from dotenv import load_dotenv



load_dotenv()



app = Flask(__name__)

app.secret_key = os.getenv("SECRET_KEY", "ecotrace-development-secret-change-in-env")



DB_CONFIG = {

    "host": os.getenv("PGHOST", "localhost"),

    "port": os.getenv("PGPORT", "5432"),

    "dbname": os.getenv("PGDATABASE", "ecotrace"),

    "user": os.getenv("PGUSER", "postgres"),

    "password": os.getenv("PGPASSWORD"),
    "connect_timeout": 5,

}



BASE_CSS = """

:root { --eco:#176b4d; --eco2:#0e4f39; --soft:#eef8f3; --ink:#1d2b26; }

body { background:#f5f7f6; color:var(--ink); font-family:Arial, sans-serif; }

.navbar { background:var(--eco2)!important; }

.navbar-brand { font-weight:700; letter-spacing:.3px; }

.card { border:0; border-radius:14px; box-shadow:0 5px 18px rgba(0,0,0,.06); }

.card-header { background:white; border-bottom:1px solid #e8ecea; font-weight:700; }

.stat { font-size:28px; font-weight:700; color:var(--eco); }

.badge-status { font-size:.78rem; }

.table { vertical-align:middle; }

.small-muted { color:#6b7772; font-size:.88rem; }

.hero { background:linear-gradient(135deg,#e8f7ef,#ffffff); border-radius:18px; padding:25px; }

.login-card { max-width:440px; margin:8vh auto; }

pre.json { max-height:260px; overflow:auto; background:#111827; color:#e5e7eb; padding:12px; border-radius:8px; font-size:12px; }

.timeline { border-left:3px solid #b8daca; margin-left:14px; padding-left:22px; }

.timeline-item { position:relative; margin-bottom:20px; }

.timeline-item:before { content:''; position:absolute; left:-31px; top:4px; width:12px; height:12px; border-radius:50%; background:var(--eco); }

"""



LAYOUT = """

<!doctype html>

<html lang="en">

<head>

<meta charset="utf-8">

<meta name="viewport" content="width=device-width, initial-scale=1">

<title>{{ title }} | EcoTrace</title>

<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">

<style>{{ css|safe }}</style>

</head>

<body>

{% if session.get('user_id') %}

<nav class="navbar navbar-expand-lg navbar-dark mb-4">

<div class="container-fluid px-4">

<a class="navbar-brand" href="{{ url_for('dashboard') }}">🌿 EcoTrace</a>

<button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#nav"><span class="navbar-toggler-icon"></span></button>

<div class="collapse navbar-collapse" id="nav">

<ul class="navbar-nav me-auto">

<li class="nav-item"><a class="nav-link" href="{{ url_for('dashboard') }}">Dashboard</a></li>

<li class="nav-item"><a class="nav-link" href="{{ url_for('samples') }}">Samples</a></li>

<li class="nav-item"><a class="nav-link" href="{{ url_for('tests') }}">Tests</a></li>

{% if session.get('role') in ['ADMIN','STORAGE'] %}<li class="nav-item"><a class="nav-link" href="{{ url_for('storage') }}">Storage</a></li>{% endif %}

{% if session.get('role') in ['ADMIN','AUDITOR'] %}<li class="nav-item"><a class="nav-link" href="{{ url_for('audit') }}">Audit History</a></li>{% endif %}

</ul>

<span class="navbar-text me-3">{{ session.get('full_name') }} · {{ session.get('role') }}</span>

<a class="btn btn-outline-light btn-sm" href="{{ url_for('logout') }}">Logout</a>

</div></div></nav>

{% endif %}

<div class="container-fluid px-4 pb-5">

{% with messages = get_flashed_messages(with_categories=true) %}

{% for category, message in messages %}<div class="alert alert-{{ category }} alert-dismissible fade show">{{ message }}<button class="btn-close" data-bs-dismiss="alert"></button></div>{% endfor %}

{% endwith %}

{{ body|safe }}

</div>

<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>

</body></html>

"""





def db_connection():
    if not DB_CONFIG.get("password"):
        raise psycopg2.OperationalError(
            "PGPASSWORD is not set. Create a .env file in the EcoTrace folder "
            "with your PostgreSQL password, then restart Flask."
        )
    return psycopg2.connect(**DB_CONFIG)





def render_page(title, body, **context):

    return render_template_string(LAYOUT, title=title, body=render_template_string(body, **context), css=BASE_CSS)





def login_required(view):

    @wraps(view)

    def wrapped(*args, **kwargs):

        if not session.get("user_id"):

            return redirect(url_for("login"))

        return view(*args, **kwargs)

    return wrapped





def roles_required(*roles):

    def decorator(view):

        @wraps(view)

        def wrapped(*args, **kwargs):

            if not session.get("user_id"):

                return redirect(url_for("login"))

            if session.get("role") not in roles:

                flash("You do not have permission to perform this action.", "danger")

                return redirect(url_for("dashboard"))

            return view(*args, **kwargs)

        return wrapped

    return decorator





def audit_context(cur, reason):

    user_id = str(session.get("user_id", ""))

    cur.execute("SELECT set_config('app.user_id', %s, true), set_config('app.reason', %s, true)", (user_id, reason or "Application operation"))





def query_one(sql, params=()):

    with db_connection() as conn:

        with conn.cursor(cursor_factory=RealDictCursor) as cur:

            cur.execute(sql, params)

            return cur.fetchone()





def query_all(sql, params=()):

    with db_connection() as conn:

        with conn.cursor(cursor_factory=RealDictCursor) as cur:

            cur.execute(sql, params)

            return cur.fetchall()





@app.route("/login", methods=["GET", "POST"])

def login():

    if request.method == "POST":

        username = request.form.get("username", "").strip()

        password = request.form.get("password", "")

        try:
            user = query_one(
                """SELECT user_id, username, full_name, role
                   FROM users
                   WHERE username=%s AND password_hash = crypt(%s, password_hash)
                     AND is_active=TRUE""",
                (username, password),
            )
        except psycopg2.OperationalError as exc:
            flash(f"Database connection failed: {exc}", "danger")
            user = None

        if user:

            session.clear()

            session.update({"user_id": user["user_id"], "username": user["username"], "full_name": user["full_name"], "role": user["role"]})

            return redirect(url_for("dashboard"))

        flash("Invalid username or password.", "danger")



    body = """

    <div class="login-card card p-4">

      <div class="text-center mb-4"><div style="font-size:50px">🌿</div><h2>EcoTrace</h2><p class="small-muted">Environmental Sample Lifecycle Tracking</p></div>

      <form method="post">

        <label class="form-label">Username</label><input class="form-control mb-3" name="username" required autofocus>

        <label class="form-label">Password</label><input class="form-control mb-3" type="password" name="password" required>

        <button class="btn btn-success w-100">Login</button>

      </form>

      <div class="alert alert-light mt-3 mb-0 small">Demo admin: <b>admin</b> / <b>admin123</b></div>

    </div>

    """

    return render_page("Login", body)





@app.route("/logout")

def logout():

    session.clear()

    return redirect(url_for("login"))





@app.route("/")

@login_required

def dashboard():

    counts = query_one("""SELECT

        COUNT(*) AS total,

        COUNT(*) FILTER (WHERE status='COLLECTED') AS collected,

        COUNT(*) FILTER (WHERE status='IN_TRANSIT') AS in_transit,

        COUNT(*) FILTER (WHERE status='RECEIVED') AS received,

        COUNT(*) FILTER (WHERE status='TESTING') AS testing,

        COUNT(*) FILTER (WHERE status='TESTED') AS tested,

        COUNT(*) FILTER (WHERE status='STORED') AS stored,

        COUNT(*) FILTER (WHERE status='DISPOSED') AS disposed

        FROM samples""")

    tests = query_one("SELECT COUNT(*) AS total, COUNT(*) FILTER (WHERE status='COMPLETED') AS completed FROM sample_tests")

    recent = query_all("SELECT * FROM v_sample_overview ORDER BY collected_at DESC LIMIT 8")

    body = """

    <div class="hero mb-4"><div class="row align-items-center"><div class="col-lg-8"><h1>EcoTrace Dashboard</h1><p class="mb-0">Track every environmental sample from collection to testing, storage and disposal with a traceable PostgreSQL record.</p></div><div class="col-lg-4 text-lg-end mt-3 mt-lg-0"><a class="btn btn-success" href="{{ url_for('new_sample') }}">+ Register Sample</a></div></div></div>

    <div class="row g-3 mb-4">

    {% for label, value in [('Total Samples', counts.total),('Collected',counts.collected),('In Transit',counts.in_transit),('Received',counts.received),('Testing',counts.testing),('Tested',counts.tested),('Stored',counts.stored),('Disposed',counts.disposed)] %}

      <div class="col-6 col-md-3 col-xl-3"><div class="card p-3"><div class="small-muted">{{ label }}</div><div class="stat">{{ value }}</div></div></div>

    {% endfor %}

    </div>

    <div class="row g-4">

      <div class="col-lg-8"><div class="card"><div class="card-header">Recent Samples</div><div class="table-responsive"><table class="table table-hover mb-0"><thead><tr><th>Code</th><th>Type</th><th>Source</th><th>Status</th><th>Tests</th></tr></thead><tbody>

      {% for s in recent %}<tr><td><a href="{{ url_for('sample_detail', sample_id=s.sample_id) }}">{{ s.sample_code }}</a></td><td>{{ s.sample_type }}</td><td>{{ s.source_name }}</td><td><span class="badge text-bg-success badge-status">{{ s.status }}</span></td><td>{{ s.total_tests }} / {{ s.completed_results }}</td></tr>{% else %}<tr><td colspan="5">No samples yet.</td></tr>{% endfor %}

      </tbody></table></div></div></div>

      <div class="col-lg-4"><div class="card p-4"><h5>Testing Summary</h5><div class="display-6">{{ tests.completed }} / {{ tests.total }}</div><p class="small-muted">completed results / assigned tests</p><a href="{{ url_for('tests') }}" class="btn btn-outline-success">Open Testing</a></div></div>

    </div>

    """

    return render_page("Dashboard", body, counts=counts, recent=recent, tests=tests)





@app.route("/samples")

@login_required

def samples():

    search = request.args.get("q", "").strip()

    status = request.args.get("status", "").strip()

    sql = "SELECT * FROM v_sample_overview WHERE 1=1"

    params = []

    if search:

        sql += " AND (sample_code ILIKE %s OR sample_type ILIKE %s OR source_name ILIKE %s OR source_location ILIKE %s)"

        like = f"%{search}%"

        params.extend([like, like, like, like])

    if status:

        sql += " AND status=%s"

        params.append(status)

    sql += " ORDER BY collected_at DESC"

    rows = query_all(sql, params)

    body = """

    <div class="d-flex flex-wrap justify-content-between align-items-center mb-3"><div><h2>Environmental Samples</h2><div class="small-muted">Collection → registration → transfer → testing → storage → disposal</div></div><a class="btn btn-success" href="{{ url_for('new_sample') }}">+ Register Sample</a></div>

    <div class="card p-3 mb-3"><form class="row g-2"><div class="col-md-5"><input class="form-control" name="q" value="{{ search }}" placeholder="Search code, type, source or location"></div><div class="col-md-3"><select class="form-select" name="status"><option value="">All statuses</option>{% for st in statuses %}<option {% if status==st %}selected{% endif %}>{{ st }}</option>{% endfor %}</select></div><div class="col-md-2"><button class="btn btn-outline-success w-100">Search</button></div><div class="col-md-2"><a class="btn btn-outline-secondary w-100" href="{{ url_for('samples') }}">Reset</a></div></form></div>

    <div class="card"><div class="table-responsive"><table class="table table-hover mb-0"><thead><tr><th>Code</th><th>Type</th><th>Source</th><th>Collected</th><th>Status</th><th>Tests</th><th></th></tr></thead><tbody>

    {% for s in rows %}<tr><td><a href="{{ url_for('sample_detail', sample_id=s.sample_id) }}"><b>{{ s.sample_code }}</b></a></td><td>{{ s.sample_type }}</td><td>{{ s.source_name }}</td><td>{{ s.collected_at.strftime('%Y-%m-%d %H:%M') }}</td><td><span class="badge text-bg-success">{{ s.status }}</span></td><td>{{ s.completed_results }}/{{ s.total_tests }}</td><td><a class="btn btn-sm btn-outline-secondary" href="{{ url_for('sample_detail', sample_id=s.sample_id) }}">View</a></td></tr>{% else %}<tr><td colspan="7" class="text-center py-4">No matching samples.</td></tr>{% endfor %}

    </tbody></table></div></div>

    """

    statuses = ['COLLECTED','REGISTERED','IN_TRANSIT','RECEIVED','TESTING','TESTED','STORED','DISPOSED','REJECTED']

    return render_page("Samples", body, rows=rows, search=search, status=status, statuses=statuses)





@app.route("/samples/new", methods=["GET", "POST"])

@roles_required("ADMIN", "COLLECTOR")

def new_sample():

    if request.method == "POST":

        data = (

            request.form.get("sample_code", "").strip(), request.form.get("sample_type", "").strip(),

            request.form.get("source_name", "").strip(), request.form.get("source_location", "").strip(),

            request.form.get("collected_at", "").strip(), int(session["user_id"]),

            request.form.get("quantity", "").strip(), request.form.get("unit", "g").strip(),

            request.form.get("sample_condition", "GOOD"), request.form.get("description", "").strip(),

        )

        try:

            with db_connection() as conn:

                with conn.cursor() as cur:

                    audit_context(cur, "Register environmental sample")

                    cur.execute("""INSERT INTO samples

                    (sample_code,sample_type,source_name,source_location,collected_at,collected_by,quantity,unit,sample_condition,status,description)

                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,'REGISTERED',%s) RETURNING sample_id""", data)

                    sample_id = cur.fetchone()[0]

            flash("Sample registered successfully.", "success")

            return redirect(url_for("sample_detail", sample_id=sample_id))

        except (ValueError, psycopg2.Error) as exc:

            flash(f"Could not register sample: {exc}", "danger")



    body = """

    <div class="card p-4"><h2>Register Environmental Sample</h2><p class="small-muted">This creates the master sample record used throughout the lifecycle.</p>

    <form method="post" class="row g-3">

      <div class="col-md-4"><label class="form-label">Sample Code</label><input name="sample_code" class="form-control" placeholder="ECO-2026-003" required></div>

      <div class="col-md-4"><label class="form-label">Sample Type</label><input name="sample_type" class="form-control" placeholder="Water / Soil / Sediment" required></div>

      <div class="col-md-4"><label class="form-label">Source Name</label><input name="source_name" class="form-control" required></div>

      <div class="col-md-6"><label class="form-label">Source Location</label><input name="source_location" class="form-control" required></div>

      <div class="col-md-3"><label class="form-label">Collected At</label><input type="datetime-local" name="collected_at" class="form-control" required></div>

      <div class="col-md-3"><label class="form-label">Quantity</label><input type="number" step="0.001" min="0.001" name="quantity" class="form-control" required></div>

      <div class="col-md-3"><label class="form-label">Unit</label><input name="unit" class="form-control" value="g" required></div>

      <div class="col-md-3"><label class="form-label">Condition</label><select name="sample_condition" class="form-select">{% for x in conditions %}<option>{{ x }}</option>{% endfor %}</select></div>

      <div class="col-12"><label class="form-label">Description</label><textarea name="description" class="form-control" rows="3"></textarea></div>

      <div class="col-12"><button class="btn btn-success">Register Sample</button> <a class="btn btn-secondary" href="{{ url_for('samples') }}">Cancel</a></div>

    </form></div>

    """

    return render_page("Register Sample", body, conditions=['GOOD','DAMAGED','CONTAMINATED','UNKNOWN'])





@app.route("/samples/<int:sample_id>")

@login_required

def sample_detail(sample_id):

    sample = query_one("SELECT * FROM v_sample_overview WHERE sample_id=%s", (sample_id,))

    if not sample:

        flash("Sample not found.", "danger")

        return redirect(url_for("samples"))

    lifecycle = query_one("SELECT * FROM v_sample_lifecycle WHERE sample_id=%s", (sample_id,))

    transfers = query_all("""SELECT t.*, u.full_name AS transferred_by_name FROM sample_transfers t JOIN users u ON u.user_id=t.transferred_by WHERE t.sample_id=%s ORDER BY t.transfer_time DESC""", (sample_id,))

    tests_rows = query_all("""SELECT st.*, t.test_code, t.test_name, t.method, t.result_unit, u.full_name AS assigned_to_name,

        r.result_id, r.result_value, r.result_text, r.result_unit AS actual_unit, r.observed_at, eu.full_name AS entered_by_name

        FROM sample_tests st JOIN tests t ON t.test_id=st.test_id

        LEFT JOIN users u ON u.user_id=st.assigned_to

        LEFT JOIN test_results r ON r.sample_test_id=st.sample_test_id

        LEFT JOIN users eu ON eu.user_id=r.entered_by

        WHERE st.sample_id=%s ORDER BY st.assigned_at DESC""", (sample_id,))

    storage_rows = query_all("SELECT * FROM storage WHERE sample_id=%s ORDER BY stored_from DESC", (sample_id,))

    audit_rows = query_all("SELECT * FROM v_audit_history WHERE table_name='samples' AND record_id=%s ORDER BY changed_at DESC", (sample_id,))

    body = """

    <div class="d-flex justify-content-between align-items-center mb-3"><div><h2>{{ sample.sample_code }}</h2><div class="small-muted">{{ sample.sample_type }} · {{ sample.source_name }}</div></div><div>{% if sample.status == 'IN_TRANSIT' %}<form method="post" action="{{ url_for('receive_sample', sample_id=sample.sample_id) }}" class="d-inline"><button class="btn btn-outline-success">Receive</button></form>{% endif %} {% if session.get('role') in ['ADMIN','COLLECTOR'] %}<a class="btn btn-outline-success" href="{{ url_for('transfer_sample', sample_id=sample.sample_id) }}">Transfer</a>{% endif %} {% if session.get('role') in ['ADMIN','LAB'] %}<a class="btn btn-outline-primary" href="{{ url_for('assign_test', sample_id=sample.sample_id) }}">Assign Test</a>{% endif %} {% if session.get('role') in ['ADMIN'] %}<a class="btn btn-outline-secondary" href="{{ url_for('edit_sample', sample_id=sample.sample_id) }}">Edit</a>{% endif %} {% if session.get('role') in ['ADMIN','STORAGE'] and sample.status != 'DISPOSED' %}<a class="btn btn-outline-dark" href="{{ url_for('storage') }}">Storage</a><form method="post" action="{{ url_for('dispose_sample', sample_id=sample.sample_id) }}" class="d-inline" onsubmit="return confirm('Mark this sample as disposed?')"><input type="hidden" name="reason" value="Final sample disposal"><button class="btn btn-outline-danger">Dispose</button></form>{% endif %} {% if session.get('role') == 'ADMIN' %}<form method="post" action="{{ url_for('delete_sample', sample_id=sample.sample_id) }}" class="d-inline" onsubmit="return confirm('Permanently delete this sample and its dependent lifecycle records?')"><button class="btn btn-danger">Delete</button></form>{% endif %} <a class="btn btn-outline-secondary" href="{{ url_for('samples') }}">Back</a></div></div>

    <div class="row g-4">

    <div class="col-lg-5"><div class="card p-4"><h5>Sample Record</h5><dl class="row mb-0"><dt class="col-5">Status</dt><dd class="col-7"><span class="badge text-bg-success">{{ sample.status }}</span></dd><dt class="col-5">Source</dt><dd class="col-7">{{ sample.source_location }}</dd><dt class="col-5">Collected</dt><dd class="col-7">{{ sample.collected_at.strftime('%Y-%m-%d %H:%M') }}</dd><dt class="col-5">Collector</dt><dd class="col-7">{{ sample.collected_by_name }}</dd><dt class="col-5">Quantity</dt><dd class="col-7">{{ sample.quantity }} {{ sample.unit }}</dd><dt class="col-5">Condition</dt><dd class="col-7">{{ sample.sample_condition }}</dd><dt class="col-5">Description</dt><dd class="col-7">{{ sample.description or '—' }}</dd></dl></div></div>

    <div class="col-lg-7"><div class="card p-4"><h5>Lifecycle</h5><div class="timeline"><div class="timeline-item"><b>Collection</b><br><span class="small-muted">{{ sample.collected_at.strftime('%Y-%m-%d %H:%M') }} · {{ sample.source_location }}</span></div>{% for t in transfers %}<div class="timeline-item"><b>Transfer</b><br>{{ t.from_location }} → {{ t.to_location }}<br><span class="small-muted">{{ t.transfer_time.strftime('%Y-%m-%d %H:%M') }} · {{ t.condition_on_transfer }}</span></div>{% endfor %}{% for st in storage_rows %}<div class="timeline-item"><b>Storage</b><br>{{ st.location }}{% if st.shelf %} · Shelf {{ st.shelf }}{% endif %}<br><span class="small-muted">{{ st.stored_from.strftime('%Y-%m-%d %H:%M') }}{% if st.temperature_c is not none %} · {{ st.temperature_c }} °C{% endif %}</span></div>{% endfor %}<div class="timeline-item"><b>Current status</b><br><span class="badge text-bg-success">{{ sample.status }}</span></div></div></div></div>

    </div>

    <div class="card mt-4"><div class="card-header d-flex justify-content-between"><span>Testing & Results</span>{% if session.get('role') in ['ADMIN','LAB'] %}<a href="{{ url_for('assign_test', sample_id=sample.sample_id) }}" class="btn btn-sm btn-success">Assign Test</a>{% endif %}</div><div class="table-responsive"><table class="table mb-0"><thead><tr><th>Test</th><th>Method</th><th>Status</th><th>Result</th><th>Observed</th><th>Action</th></tr></thead><tbody>{% for r in tests_rows %}<tr><td>{{ r.test_code }} — {{ r.test_name }}</td><td>{{ r.method }}</td><td>{{ r.status }}</td><td>{% if r.result_id %}{{ r.result_value if r.result_value is not none else r.result_text }} {{ r.actual_unit or r.result_unit or '' }}{% else %}Pending{% endif %}</td><td>{{ r.observed_at.strftime('%Y-%m-%d %H:%M') if r.observed_at else '—' }}</td><td>{% if not r.result_id and session.get('role') in ['ADMIN','LAB'] %}<a class="btn btn-sm btn-outline-primary" href="{{ url_for('add_result', sample_test_id=r.sample_test_id) }}">Enter Result</a>{% endif %}</td></tr>{% else %}<tr><td colspan="6" class="text-center py-3">No tests assigned.</td></tr>{% endfor %}</tbody></table></div></div>

    <div class="row g-4 mt-1"><div class="col-lg-7"><div class="card"><div class="card-header">Transfer History</div><div class="table-responsive"><table class="table table-sm mb-0"><thead><tr><th>From</th><th>To</th><th>By</th><th>Time</th><th>Condition</th></tr></thead><tbody>{% for t in transfers %}<tr><td>{{t.from_location}}</td><td>{{t.to_location}}</td><td>{{t.transferred_by_name}}</td><td>{{t.transfer_time.strftime('%Y-%m-%d %H:%M')}}</td><td>{{t.condition_on_transfer}}</td></tr>{% else %}<tr><td colspan="5">No transfers.</td></tr>{% endfor %}</tbody></table></div></div></div><div class="col-lg-5"><div class="card"><div class="card-header">Storage History</div><div class="p-3">{% for st in storage_rows %}<div class="mb-2"><b>{{st.location}}</b> {% if st.shelf %}({{st.shelf}}){% endif %}<br><span class="small-muted">{{st.stored_from.strftime('%Y-%m-%d %H:%M')}}{% if st.stored_to %} → {{st.stored_to.strftime('%Y-%m-%d %H:%M')}}{% else %} → active{% endif %}</span></div>{% else %}No storage record.{% endfor %}</div></div></div></div>

    <div class="card mt-4"><div class="card-header">Sample Audit History</div><div class="table-responsive"><table class="table table-sm mb-0"><thead><tr><th>Time</th><th>Action</th><th>User</th><th>Reason</th></tr></thead><tbody>{% for a in audit_rows %}<tr><td>{{a.changed_at.strftime('%Y-%m-%d %H:%M:%S')}}</td><td>{{a.action}}</td><td>{{a.changed_by}}</td><td>{{a.reason or '—'}}</td></tr>{% else %}<tr><td colspan="4">No audit entries.</td></tr>{% endfor %}</tbody></table></div></div>

    """

    return render_page("Sample Detail", body, sample=sample, lifecycle=lifecycle, transfers=transfers, tests_rows=tests_rows, storage_rows=storage_rows, audit_rows=audit_rows)





@app.route("/samples/<int:sample_id>/transfer", methods=["GET", "POST"])

@roles_required("ADMIN", "COLLECTOR")

def transfer_sample(sample_id):

    sample = query_one("SELECT * FROM samples WHERE sample_id=%s", (sample_id,))

    if not sample:

        flash("Sample not found.", "danger")

        return redirect(url_for("samples"))

    if request.method == "POST":

        from_location = request.form.get("from_location", "").strip()

        to_location = request.form.get("to_location", "").strip()

        condition = request.form.get("condition_on_transfer", "GOOD")

        remarks = request.form.get("remarks", "").strip()

        try:

            with db_connection() as conn:

                with conn.cursor() as cur:

                    audit_context(cur, "Transfer sample")

                    cur.execute("""INSERT INTO sample_transfers(sample_id,from_location,to_location,transferred_by,condition_on_transfer,remarks)

                                   VALUES (%s,%s,%s,%s,%s,%s)""", (sample_id, from_location, to_location, session["user_id"], condition, remarks))

                    cur.execute("UPDATE samples SET status='IN_TRANSIT' WHERE sample_id=%s", (sample_id,))

            flash("Sample transfer recorded.", "success")

            return redirect(url_for("sample_detail", sample_id=sample_id))

        except psycopg2.Error as exc:

            flash(f"Transfer failed: {exc}", "danger")

    body = """

    <div class="card p-4"><h2>Transfer {{ sample.sample_code }}</h2><form method="post" class="row g-3"><div class="col-md-6"><label class="form-label">From Location</label><input name="from_location" class="form-control" required value="{{ sample.source_location }}"></div><div class="col-md-6"><label class="form-label">To Location</label><input name="to_location" class="form-control" required></div><div class="col-md-4"><label class="form-label">Condition</label><select name="condition_on_transfer" class="form-select">{% for x in conditions %}<option>{{x}}</option>{% endfor %}</select></div><div class="col-12"><label class="form-label">Remarks</label><textarea name="remarks" class="form-control"></textarea></div><div class="col-12"><button class="btn btn-success">Record Transfer</button> <a class="btn btn-secondary" href="{{url_for('sample_detail',sample_id=sample_id)}}">Cancel</a></div></form></div>

    """

    return render_page("Transfer Sample", body, sample=sample, sample_id=sample_id, conditions=['GOOD','DAMAGED','CONTAMINATED','UNKNOWN'])





@app.route("/samples/<int:sample_id>/receive", methods=["POST"])

@roles_required("ADMIN", "LAB")

def receive_sample(sample_id):

    try:

        with db_connection() as conn:

            with conn.cursor() as cur:

                audit_context(cur, "Receive sample at laboratory")

                cur.execute("""UPDATE sample_transfers SET received_time=CURRENT_TIMESTAMP

                               WHERE transfer_id=(SELECT transfer_id FROM sample_transfers WHERE sample_id=%s ORDER BY transfer_time DESC LIMIT 1)

                               AND received_time IS NULL""", (sample_id,))

                cur.execute("UPDATE samples SET status='RECEIVED' WHERE sample_id=%s", (sample_id,))

        flash("Sample marked as received.", "success")

    except psycopg2.Error as exc:

        flash(f"Receive operation failed: {exc}", "danger")

    return redirect(url_for("sample_detail", sample_id=sample_id))





@app.route("/samples/<int:sample_id>/assign-test", methods=["GET", "POST"])

@roles_required("ADMIN", "LAB")

def assign_test(sample_id):

    sample = query_one("SELECT * FROM samples WHERE sample_id=%s", (sample_id,))

    if not sample:

        flash("Sample not found.", "danger")

        return redirect(url_for("samples"))

    if request.method == "POST":

        test_id = int(request.form["test_id"])

        assigned_to = int(request.form["assigned_to"]) if request.form.get("assigned_to") else None

        priority = request.form.get("priority", "NORMAL")

        try:

            with db_connection() as conn:

                with conn.cursor() as cur:

                    audit_context(cur, "Assign laboratory test")

                    cur.execute("""INSERT INTO sample_tests(sample_id,test_id,assigned_to,status,priority,remarks)

                                   VALUES (%s,%s,%s,'ASSIGNED',%s,%s)""", (sample_id, test_id, assigned_to, priority, request.form.get("remarks", "").strip()))

                    cur.execute("UPDATE samples SET status='TESTING' WHERE sample_id=%s AND status IN ('RECEIVED','REGISTERED','COLLECTED')", (sample_id,))

            flash("Test assigned.", "success")

            return redirect(url_for("sample_detail", sample_id=sample_id))

        except psycopg2.Error as exc:

            flash(f"Could not assign test: {exc}", "danger")

    tests = query_all("SELECT * FROM tests WHERE active=TRUE ORDER BY test_name")

    lab_users = query_all("SELECT user_id, full_name FROM users WHERE role IN ('LAB','ADMIN') AND is_active=TRUE ORDER BY full_name")

    body = """

    <div class="card p-4"><h2>Assign Test</h2><p class="small-muted">Sample: <b>{{ sample.sample_code }}</b></p><form method="post" class="row g-3"><div class="col-md-6"><label class="form-label">Test</label><select name="test_id" class="form-select" required>{% for t in tests %}<option value="{{t.test_id}}">{{t.test_code}} — {{t.test_name}}</option>{% endfor %}</select></div><div class="col-md-4"><label class="form-label">Analyst</label><select name="assigned_to" class="form-select"><option value="">Unassigned</option>{% for u in lab_users %}<option value="{{u.user_id}}">{{u.full_name}}</option>{% endfor %}</select></div><div class="col-md-2"><label class="form-label">Priority</label><select name="priority" class="form-select"><option>LOW</option><option selected>NORMAL</option><option>HIGH</option></select></div><div class="col-12"><label class="form-label">Remarks</label><textarea name="remarks" class="form-control"></textarea></div><div class="col-12"><button class="btn btn-success">Assign</button> <a class="btn btn-secondary" href="{{url_for('sample_detail',sample_id=sample.sample_id)}}">Cancel</a></div></form></div>

    """

    return render_page("Assign Test", body, sample=sample, tests=tests, lab_users=lab_users)





@app.route("/sample-tests/<int:sample_test_id>/result", methods=["GET", "POST"])

@roles_required("ADMIN", "LAB")

def add_result(sample_test_id):

    row = query_one("""SELECT st.*, s.sample_id, s.sample_code, t.test_name, t.result_unit

                       FROM sample_tests st JOIN samples s ON s.sample_id=st.sample_id JOIN tests t ON t.test_id=st.test_id

                       WHERE st.sample_test_id=%s""", (sample_test_id,))

    if not row:

        flash("Test assignment not found.", "danger")

        return redirect(url_for("samples"))

    if request.method == "POST":

        value_text = request.form.get("result_value", "").strip()
        result_text = request.form.get("result_text", "").strip() or None

        try:
            result_value = float(value_text) if value_text else None
        except ValueError:
            flash("Numeric result must be a valid number.", "warning")
            result_value = None
            value_text = "INVALID"

        if value_text == "INVALID":
            pass
        elif result_value is None and not result_text:
            flash("Enter either a numeric result or text result.", "warning")
        else:
            try:

                with db_connection() as conn:

                    with conn.cursor() as cur:

                        audit_context(cur, "Record laboratory test result")

                        cur.execute("""INSERT INTO test_results(sample_test_id,result_value,result_text,result_unit,entered_by,remarks)

                                       VALUES (%s,%s,%s,%s,%s,%s)""", (sample_test_id,result_value,result_text,request.form.get('result_unit') or row['result_unit'],session['user_id'],request.form.get('remarks','').strip()))

                        cur.execute("UPDATE sample_tests SET status='COMPLETED' WHERE sample_test_id=%s", (sample_test_id,))

                        cur.execute("""UPDATE samples SET status='TESTED'

                                       WHERE sample_id=%s AND NOT EXISTS (

                                           SELECT 1 FROM sample_tests WHERE sample_id=%s AND status <> 'COMPLETED'

                                       )""", (row['sample_id'], row['sample_id']))

                flash("Test result recorded.", "success")

                return redirect(url_for("sample_detail", sample_id=row["sample_id"]))

            except (ValueError, psycopg2.Error) as exc:

                flash(f"Could not record result: {exc}", "danger")

    body = """

    <div class="card p-4"><h2>Enter Test Result</h2><p><b>{{ row.sample_code }}</b> · {{ row.test_name }}</p><form method="post" class="row g-3"><div class="col-md-4"><label class="form-label">Numeric Result</label><input type="number" step="0.0001" name="result_value" class="form-control"></div><div class="col-md-4"><label class="form-label">Unit</label><input name="result_unit" class="form-control" value="{{row.result_unit or ''}}"></div><div class="col-md-4"><label class="form-label">Text Result (optional)</label><input name="result_text" class="form-control"></div><div class="col-12"><label class="form-label">Remarks</label><textarea name="remarks" class="form-control"></textarea></div><div class="col-12"><button class="btn btn-success">Save Result</button> <a class="btn btn-secondary" href="{{url_for('sample_detail',sample_id=row.sample_id)}}">Cancel</a></div></form></div>

    """

    return render_page("Test Result", body, row=row)





@app.route("/storage", methods=["GET", "POST"])

@roles_required("ADMIN", "STORAGE")

def storage():

    if request.method == "POST":
        try:
            sample_id = int(request.form["sample_id"])

            with db_connection() as conn:

                with conn.cursor() as cur:

                    audit_context(cur, "Place sample into storage")

                    cur.execute("UPDATE storage SET stored_to=CURRENT_TIMESTAMP WHERE sample_id=%s AND stored_to IS NULL", (sample_id,))

                    cur.execute("""INSERT INTO storage(sample_id,location,shelf,temperature_c,sample_condition,remarks)

                                   VALUES (%s,%s,%s,%s,%s,%s)""", (sample_id,request.form['location'].strip(),request.form.get('shelf','').strip(),request.form.get('temperature_c') or None,request.form['sample_condition'],request.form.get('remarks','').strip()))

                    cur.execute("UPDATE samples SET status='STORED' WHERE sample_id=%s", (sample_id,))

            flash("Storage record created.", "success")

        except psycopg2.Error as exc:

            flash(f"Storage operation failed: {exc}", "danger")

    samples_rows = query_all("SELECT sample_id, sample_code, status FROM samples WHERE status <> 'DISPOSED' ORDER BY sample_code")

    active = query_all("SELECT st.*, s.sample_code FROM storage st JOIN samples s ON s.sample_id=st.sample_id WHERE st.stored_to IS NULL ORDER BY st.stored_from DESC")

    body = """

    <div class="row g-4"><div class="col-lg-5"><div class="card p-4"><h3>Store Sample</h3><form method="post" class="row g-3"><div class="col-12"><label class="form-label">Sample</label><select name="sample_id" class="form-select" required>{% for s in samples_rows %}<option value="{{s.sample_id}}">{{s.sample_code}} — {{s.status}}</option>{% endfor %}</select></div><div class="col-md-7"><label class="form-label">Storage Location</label><input name="location" class="form-control" required></div><div class="col-md-5"><label class="form-label">Shelf</label><input name="shelf" class="form-control"></div><div class="col-md-5"><label class="form-label">Temperature °C</label><input type="number" step="0.01" name="temperature_c" class="form-control"></div><div class="col-md-7"><label class="form-label">Condition</label><select name="sample_condition" class="form-select">{% for x in conditions %}<option>{{x}}</option>{% endfor %}</select></div><div class="col-12"><textarea name="remarks" class="form-control" placeholder="Remarks"></textarea></div><div class="col-12"><button class="btn btn-success">Store Sample</button></div></form></div></div><div class="col-lg-7"><div class="card"><div class="card-header">Active Storage</div><div class="table-responsive"><table class="table mb-0"><thead><tr><th>Sample</th><th>Location</th><th>Shelf</th><th>Temperature</th><th>From</th></tr></thead><tbody>{% for x in active %}<tr><td>{{x.sample_code}}</td><td>{{x.location}}</td><td>{{x.shelf or '—'}}</td><td>{{x.temperature_c or '—'}}</td><td>{{x.stored_from.strftime('%Y-%m-%d %H:%M')}}</td></tr>{% else %}<tr><td colspan="5">No active storage records.</td></tr>{% endfor %}</tbody></table></div></div></div></div>

    """

    return render_page("Storage", body, samples_rows=samples_rows, active=active, conditions=['GOOD','DAMAGED','CONTAMINATED','UNKNOWN'])





@app.route("/samples/<int:sample_id>/edit", methods=["GET", "POST"])

@roles_required("ADMIN")

def edit_sample(sample_id):

    sample = query_one("SELECT * FROM samples WHERE sample_id=%s", (sample_id,))

    if not sample:

        flash("Sample not found.", "danger")

        return redirect(url_for("samples"))

    if request.method == "POST":

        try:

            with db_connection() as conn:

                with conn.cursor() as cur:

                    audit_context(cur, "Update sample master record")

                    cur.execute("""UPDATE samples SET sample_type=%s, source_name=%s, source_location=%s,

                                   quantity=%s, unit=%s, sample_condition=%s, description=%s

                                   WHERE sample_id=%s""", (

                        request.form["sample_type"].strip(), request.form["source_name"].strip(),

                        request.form["source_location"].strip(), request.form["quantity"].strip(),

                        request.form["unit"].strip(), request.form["sample_condition"],

                        request.form.get("description", "").strip(), sample_id))

            flash("Sample record updated.", "success")

            return redirect(url_for("sample_detail", sample_id=sample_id))

        except psycopg2.Error as exc:

            flash(f"Update failed: {exc}", "danger")

    body = """

    <div class="card p-4"><h2>Edit Sample</h2><form method="post" class="row g-3">

      <div class="col-md-4"><label class="form-label">Sample Code</label><input class="form-control" value="{{sample.sample_code}}" disabled></div>

      <div class="col-md-4"><label class="form-label">Sample Type</label><input name="sample_type" class="form-control" value="{{sample.sample_type}}" required></div>

      <div class="col-md-4"><label class="form-label">Source Name</label><input name="source_name" class="form-control" value="{{sample.source_name}}" required></div>

      <div class="col-md-6"><label class="form-label">Source Location</label><input name="source_location" class="form-control" value="{{sample.source_location}}" required></div>

      <div class="col-md-3"><label class="form-label">Quantity</label><input name="quantity" type="number" step="0.001" min="0.001" class="form-control" value="{{sample.quantity}}" required></div>

      <div class="col-md-3"><label class="form-label">Unit</label><input name="unit" class="form-control" value="{{sample.unit}}" required></div>

      <div class="col-md-4"><label class="form-label">Condition</label><select name="sample_condition" class="form-select">{% for x in conditions %}<option {% if sample.sample_condition==x %}selected{% endif %}>{{x}}</option>{% endfor %}</select></div>

      <div class="col-12"><label class="form-label">Description</label><textarea name="description" class="form-control">{{sample.description or ''}}</textarea></div>

      <div class="col-12"><button class="btn btn-success">Save Changes</button> <a class="btn btn-secondary" href="{{url_for('sample_detail',sample_id=sample_id)}}">Cancel</a></div>

    </form></div>

    """

    return render_page("Edit Sample", body, sample=sample, sample_id=sample_id, conditions=['GOOD','DAMAGED','CONTAMINATED','UNKNOWN'])





@app.route("/samples/<int:sample_id>/dispose", methods=["POST"])

@roles_required("ADMIN", "STORAGE")

def dispose_sample(sample_id):

    reason = request.form.get("reason", "Final disposal").strip() or "Final disposal"

    try:

        with db_connection() as conn:

            with conn.cursor() as cur:

                audit_context(cur, reason)

                cur.execute("UPDATE storage SET stored_to=CURRENT_TIMESTAMP WHERE sample_id=%s AND stored_to IS NULL", (sample_id,))

                cur.execute("UPDATE samples SET status='DISPOSED' WHERE sample_id=%s", (sample_id,))

                if cur.rowcount == 0:

                    raise ValueError("Sample not found")

        flash("Sample marked as disposed. The lifecycle and audit history remain available.", "success")

    except (ValueError, psycopg2.Error) as exc:

        flash(f"Disposal failed: {exc}", "danger")

    return redirect(url_for("sample_detail", sample_id=sample_id))





@app.route("/samples/<int:sample_id>/delete", methods=["POST"])

@roles_required("ADMIN")

def delete_sample(sample_id):

    try:

        with db_connection() as conn:

            with conn.cursor() as cur:

                audit_context(cur, "Delete sample record")

                cur.execute("DELETE FROM samples WHERE sample_id=%s", (sample_id,))

                if cur.rowcount == 0:

                    raise ValueError("Sample not found")

        flash("Sample deleted.", "success")

    except (ValueError, psycopg2.Error) as exc:

        flash(f"Delete failed: {exc}", "danger")

    return redirect(url_for("samples"))





@app.route("/tests")

@login_required

def tests():

    rows = query_all("SELECT * FROM v_test_summary ORDER BY test_name")

    body = """

    <div class="d-flex justify-content-between align-items-center mb-3"><div><h2>Testing</h2><div class="small-muted">Master test definitions and assigned test workload.</div></div></div>

    <div class="card"><div class="table-responsive"><table class="table table-hover mb-0"><thead><tr><th>Code</th><th>Test</th><th>Method</th><th>Unit</th><th>Assigned</th><th>Completed</th></tr></thead><tbody>{% for t in rows %}<tr><td>{{t.test_code}}</td><td>{{t.test_name}}</td><td>{{t.method}}</td><td>{{t.result_unit or '—'}}</td><td>{{t.samples_assigned}}</td><td>{{t.results_completed}}</td></tr>{% endfor %}</tbody></table></div></div>

    """

    return render_page("Testing", body, rows=rows)





@app.route("/audit")

@roles_required("ADMIN", "AUDITOR")

def audit():

    table_name = request.args.get("table", "").strip()

    action = request.args.get("action", "").strip()

    sql = "SELECT * FROM v_audit_history WHERE 1=1"

    params = []

    if table_name:

        sql += " AND table_name=%s"; params.append(table_name)

    if action:

        sql += " AND action=%s"; params.append(action)

    sql += " ORDER BY changed_at DESC LIMIT 300"

    rows = query_all(sql, params)

    body = """

    <div class="d-flex justify-content-between align-items-center mb-3"><div><h2>Audit History</h2><div class="small-muted">Database trigger-generated INSERT, UPDATE and DELETE history.</div></div></div>

    <div class="card p-3 mb-3"><form class="row g-2"><div class="col-md-4"><input class="form-control" name="table" value="{{table_name}}" placeholder="Table name"></div><div class="col-md-3"><select class="form-select" name="action"><option value="">All actions</option>{% for a in ['INSERT','UPDATE','DELETE'] %}<option {% if action==a %}selected{% endif %}>{{a}}</option>{% endfor %}</select></div><div class="col-md-2"><button class="btn btn-outline-success w-100">Filter</button></div></form></div>

    <div class="card"><div class="table-responsive"><table class="table table-sm table-hover mb-0"><thead><tr><th>ID</th><th>Table</th><th>Record</th><th>Action</th><th>User</th><th>Time</th><th>Reason</th><th>Data</th></tr></thead><tbody>{% for a in rows %}<tr><td>{{a.audit_id}}</td><td>{{a.table_name}}</td><td>{{a.record_id}}</td><td>{{a.action}}</td><td>{{a.changed_by}}</td><td>{{a.changed_at.strftime('%Y-%m-%d %H:%M:%S')}}</td><td>{{a.reason or '—'}}</td><td><details><summary>View</summary>{% if a.old_data %}<b>Old</b><pre class="json">{{a.old_data}}</pre>{% endif %}{% if a.new_data %}<b>New</b><pre class="json">{{a.new_data}}</pre>{% endif %}</details></td></tr>{% else %}<tr><td colspan="8">No audit records.</td></tr>{% endfor %}</tbody></table></div></div>

    """

    return render_page("Audit History", body, rows=rows, table_name=table_name, action=action)





@app.route("/health")

def health():

    try:

        row = query_one("SELECT current_database() AS database, CURRENT_TIMESTAMP AS server_time")

        return {"status": "ok", "database": row["database"], "server_time": row["server_time"].isoformat()}

    except Exception as exc:

        return {"status": "error", "message": str(exc)}, 500





@app.errorhandler(404)

def not_found(_):

    if session.get("user_id"):

        return render_page("Not Found", "<div class='card p-5 text-center'><h2>Page not found</h2><a class='btn btn-success mt-3' href='{{url_for('dashboard')}}'>Dashboard</a></div>"), 404

    return redirect(url_for("login"))





@app.errorhandler(500)

def server_error(_):

    return render_page("Server Error", "<div class='card p-5'><h2>Server error</h2><p>Check the VS Code terminal for the database error details.</p></div>"), 500





if __name__ == "__main__":

    app.run(host="127.0.0.1", port=int(os.getenv("PORT", "5000")), debug=True)
