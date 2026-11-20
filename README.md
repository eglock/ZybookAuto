# ZybookAuto
Automatically completes activities on Zybooks, with ability to vary time between answer submission.

## Requirements
`requests` library which can be installed using:
```sh
pip install requests
```

## Running
```sh
python3 ./ZybookAuto.py # From within the project directory
```

*NOTE: This repository is no longer actively maintained. If you encounter any issues feel free to open a merge request and I will review it.*

---

## Recent Updates
### Fixed ZybookAuto Authentication
Fixed the "Ill-formatted request" error by updating how the script handles authentication. The Zybooks API no longer accepts the `auth_token` as a query parameter for GET requests. It now needs to be in the `Authorization` header.

**Changes:**
* **ZybookAuto.py**: Updated `signin` to pull `auth_token` and set a global `Authorization: Bearer <token>` header on the session.
* **GET Requests**: Updated `get_books`, `get_chapters`, and `get_problems` to remove deprecated query parameters.
* **Compatibility**: POST requests still include the token in the body for legacy support. Using the session header for authentication.