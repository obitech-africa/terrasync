# TerraSync Milestone 1

## Working surfaces

- Field technician: `http://127.0.0.1:8000/app/`
- Coordinator: `http://127.0.0.1:8000/coordinator/`
- Supervisor: `http://127.0.0.1:8000/supervisor/`
- API docs: `http://127.0.0.1:8000/docs`

## Demo credentials

Field technician first-device activation:

- Username: `field.tech`
- One-time code: `246810`

The code is consumed after the first successful activation. The device then keeps its bearer credential locally and opens without asking for the OTP again.

Coordinator:

- Username: `coordinator`
- Password: `demo123`

Supervisor:

- Username: `supervisor`
- Password: `demo123`

Admin API account:

- Username: `admin`
- Password: `demo123`

## Milestone 1 capabilities

- Server-side users and roles
- PBKDF2 password/OTP hashing
- One-time field-device activation
- Registered device bearer sessions
- Persistent offline field login
- Device revocation
- Coordinator and supervisor RBAC
- Coordinator assignment creation
- Technician-specific assignment feed
- Coordinator OTP issuance
- Coordinator operations metrics
- Supervisor portfolio/risk metrics
- Separate field/coordinator/supervisor UI surfaces
- Offline field PWA shell and cached assignments

## Development database note

This milestone adds new tables and a new `assigned_user_id` column. For the zero-config SQLite demo, delete an old `terrasync.db` before first run or use a fresh database. Production should use Alembic migrations.
