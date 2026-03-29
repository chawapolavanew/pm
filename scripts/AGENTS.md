# Scripts

Start and stop scripts for running the Docker container locally.

| File       | Platform    | Action                          |
|------------|-------------|---------------------------------|
| start.sh   | Mac / Linux | Build image and start container |
| stop.sh    | Mac / Linux | Stop and remove container       |
| start.bat  | Windows     | Build image and start container |
| stop.bat   | Windows     | Stop and remove container       |

All scripts must be run from any directory — they resolve the project root relative to their own location.

The container is named `kanban-pm` and runs on port 8000.
