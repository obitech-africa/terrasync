# TerraSync capture-only field PWA

Evidence is created only through a live camera session. The capture operation automatically binds:
- inspector identity
- work order
- device-local TerraSync ID
- phone latitude/longitude and accuracy
- UTC capture time
- evidence UUID
- SHA-256 of the final watermarked JPEG

There is no file upload control and no separate GPS capture action.

Camera and geolocation require HTTPS in production. `http://localhost` and `http://127.0.0.1` are treated as secure contexts by modern browsers for local development.
