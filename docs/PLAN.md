# Project Plan: Kanban Studio MVP

## Status Legend
- [ ] Not started
- [x] Done

---

## Part 1: Plan (current)

### Goals
Produce a detailed, approved plan and document the existing frontend.

### Steps
- [x] Explore and document the existing frontend in `frontend/AGENTS.md`
- [x] Enrich this PLAN.md with substeps, checklists, and success criteria
- [x] User reviews and approves plan

### Success Criteria
- `frontend/AGENTS.md` accurately describes the existing code
- This document covers all 10 parts with actionable checklists
- User has signed off before any code is written

---

## Part 2: Scaffolding

### Goals
Docker infrastructure, FastAPI backend skeleton, start/stop scripts. Prove the stack runs end-to-end with a "hello world" HTML page and a working API endpoint.

### Steps
- [x] Create `backend/` FastAPI app
  - [x] `backend/main.py` — FastAPI app with `GET /api/hello` returning `{"message": "hello world"}` and serving static files at `/`
  - [x] `backend/requirements.txt` (or `pyproject.toml` for uv)
  - [x] Placeholder `backend/static/index.html` with "hello world"
- [x] Create `Dockerfile`
  - [x] Uses `uv` to install Python dependencies
  - [x] Builds and runs FastAPI with uvicorn on port 8000
  - [x] Copies static files into image
- [x] Create `docker-compose.yml` (optional but helpful for local dev)
- [x] Create start/stop scripts in `scripts/`
  - [x] `scripts/start.sh` (Mac/Linux)
  - [x] `scripts/stop.sh` (Mac/Linux)
  - [x] `scripts/start.bat` (Windows)
  - [x] `scripts/stop.bat` (Windows)
  - [x] Update `scripts/AGENTS.md`
- [x] Update `backend/AGENTS.md`

### Success Criteria
- `docker build` completes without errors
- Running the start script launches the container
- `GET http://localhost:8000/` returns the hello world HTML page
- `GET http://localhost:8000/api/hello` returns `{"message": "hello world"}`
- Stop script cleanly shuts down the container

---

## Part 3: Add Frontend

### Goals
Static-export the Next.js frontend and serve it via FastAPI so the Kanban board loads at `/`.

### Steps
- [x] Update `frontend/next.config.ts` for static export (`output: 'export'`)
- [x] Add a build step to `Dockerfile` that runs `npm run build` inside `frontend/` and copies `frontend/out/` to `backend/static/`
- [x] Confirm FastAPI still mounts static files at `/` correctly (index.html fallback for SPA routing)
- [ ] Smoke-test: board loads, drag-and-drop works, column rename works
- [x] Run existing unit and E2E tests against the built app
- [x] Fix any build or test issues introduced by the static export change

### Success Criteria
- `GET http://localhost:8000/` serves the Kanban board
- All existing unit tests pass (`npm run test:unit`)
- All existing E2E tests pass against localhost:8000
- No console errors in browser

---

## Part 4: Authentication

### Goals
Hardcoded login gate. Credentials: `user` / `password`. Must be logged in to see the board. Can log out.

### Steps
- [x] Backend
  - [x] `POST /api/auth/login` — validates credentials, returns a session token (simple signed JWT or random token stored in memory)
  - [x] `POST /api/auth/logout` — invalidates token
  - [x] Auth middleware/dependency that protects board API routes
- [x] Frontend
  - [x] `LoginPage` component (username + password form)
  - [x] Token stored in `localStorage` (or cookie)
  - [x] `page.tsx` renders `LoginPage` if not authenticated, `KanbanBoard` if authenticated
  - [x] Logout button in board header
  - [x] Redirect to login on 401 from API
- [x] Tests
  - [x] Backend: unit tests for login/logout endpoints
  - [x] Frontend: unit test for login form rendering and submit
  - [x] E2E: login flow, board visible after login, logout returns to login page

### Success Criteria
- Visiting `/` without auth shows login form
- Correct credentials → board visible
- Wrong credentials → error message, no board
- Logout → back to login, board no longer accessible
- All tests pass

---

## Part 5: Database Schema

### Goals
Design and document the SQLite schema. Get user sign-off before implementation.

### Steps
- [x] Draft schema covering: users, boards, columns, cards
- [x] Save schema as `docs/schema.json` (table/column definitions in JSON)
- [x] Document rationale in `docs/DATABASE.md`
- [ ] User reviews and approves

### Schema Outline (draft — subject to approval)
```json
{
  "users":   { "id": "integer PK", "username": "text UNIQUE", "password_hash": "text" },
  "boards":  { "id": "integer PK", "user_id": "integer FK", "name": "text" },
  "columns": { "id": "integer PK", "board_id": "integer FK", "title": "text", "position": "integer" },
  "cards":   { "id": "integer PK", "column_id": "integer FK", "title": "text", "details": "text", "position": "integer" }
}
```

### Success Criteria
- Schema supports multiple users (future-proof) but MVP uses one
- Schema supports one board per user for MVP
- User has approved schema before Part 6 begins

---

## Part 6: Backend API

### Goals
Full CRUD API for the Kanban board backed by SQLite. DB is created on first run if absent.

### Steps
- [x] Set up SQLite with SQLAlchemy (or raw sqlite3)
  - [x] DB file path configurable via env var, default `./data/kanban.db`
  - [x] Schema auto-created on startup if tables don't exist
  - [x] Seed one default board for the hardcoded user on first run
- [x] API routes (all require auth)
  - [x] `GET /api/board` — returns full board (columns + cards) for current user
  - [x] `PATCH /api/columns/{id}` — rename column
  - [x] `POST /api/cards` — create card in a column
  - [x] `PATCH /api/cards/{id}` — update card title/details
  - [x] `DELETE /api/cards/{id}` — delete card
  - [x] `PATCH /api/cards/{id}/move` — move card to new column/position
- [x] Unit tests for every route (use pytest + httpx TestClient)
- [x] Update `backend/AGENTS.md`

### Success Criteria
- All routes return correct data and status codes
- Auth is enforced (unauthenticated requests → 401)
- DB is created automatically on first start
- All backend tests pass (`pytest`)

---

## Part 7: Frontend + Backend Integration

### Goals
Replace in-memory frontend state with live API calls. Board is now persistent.

### Steps
- [x] Create `frontend/src/lib/api.ts` — typed fetch wrappers for all backend endpoints
- [x] `KanbanBoard` fetches board state from `GET /api/board` on mount
- [x] Column rename calls `PATCH /api/columns/{id}`
- [x] Add card calls `POST /api/cards`
- [x] Delete card calls `DELETE /api/cards/{id}`
- [x] Drag-and-drop calls `PATCH /api/cards/{id}/move`
- [x] Optimistic updates with rollback on error (keep UX snappy)
- [x] Remove all hardcoded initial board state from frontend
- [x] Tests
  - [x] Unit tests: mock API calls, test component behavior on success/error
  - [x] E2E: full flow — login, add card, move card, rename column, refresh page and verify persistence

### Success Criteria
- Board data persists across page refreshes and container restarts
- All CRUD operations work end-to-end
- No hardcoded board state in frontend
- All tests pass

---

## Part 8: AI Connectivity

### Goals
Backend can call OpenRouter. Prove it works with a simple test.

### Steps
- [ ] Add `openai` Python package (OpenAI SDK, compatible with OpenRouter)
- [ ] `OPENROUTER_API_KEY` read from `.env` / environment variable
- [ ] `backend/ai.py` — thin wrapper around the OpenRouter API using model `openai/gpt-oss-120b:free`
- [ ] `GET /api/ai/ping` — sends "What is 2+2?" to the AI, returns the response (dev/test endpoint)
- [ ] Test the ping endpoint manually and via pytest (can be skipped in CI if no key)

### Success Criteria
- `GET /api/ai/ping` returns a valid response from the AI
- API key is never hardcoded — always from environment
- Test documents expected behavior (may be marked as integration test)

---

## Part 9: AI Kanban Intelligence

### Goals
AI receives full board context + user question and can respond with text and/or board updates via Structured Outputs.

### Steps
- [ ] Define Structured Output schema:
  ```json
  {
    "reply": "string",
    "board_update": {
      "cards_to_create": [...],
      "cards_to_update": [...],
      "cards_to_delete": [...],
      "cards_to_move": [...]
    }
  }
  ```
- [ ] `POST /api/chat` endpoint
  - [ ] Accepts `{ message: string, history: [{role, content}] }`
  - [ ] Fetches current board state for the authenticated user
  - [ ] Sends system prompt (board JSON) + conversation history + user message to AI
  - [ ] Parses Structured Output response
  - [ ] If `board_update` is non-empty, applies changes to DB
  - [ ] Returns `{ reply: string, board_updated: boolean }`
- [ ] Comprehensive backend tests for the chat endpoint (mock AI response)

### Success Criteria
- Asking "add a card called 'Deploy to prod' to the Done column" creates that card in the DB
- Reply text is coherent and relevant
- Conversation history is maintained within a session
- All backend tests pass

---

## Part 10: AI Chat Sidebar

### Goals
Beautiful sidebar UI for AI chat. If the AI updates the board, the UI refreshes automatically.

### Steps
- [ ] `ChatSidebar` component
  - [ ] Toggle open/closed from board header button
  - [ ] Message list: user messages right-aligned, AI messages left-aligned
  - [ ] Input bar with submit button (Enter to send)
  - [ ] Loading indicator while AI is thinking
  - [ ] Error display on API failure
- [ ] Wire to `POST /api/chat`
- [ ] On response: if `board_updated === true`, re-fetch board state from `GET /api/board`
- [ ] Conversation history maintained in component state (cleared on page refresh is acceptable for MVP)
- [ ] Styling consistent with existing color scheme
- [ ] Tests
  - [ ] Unit: sidebar renders, sends message, shows reply
  - [ ] E2E: open sidebar, type message, receive reply, verify board updates if AI makes a change

### Success Criteria
- Sidebar looks polished and matches the design language
- AI can create, move, and update cards via natural language
- Board updates are reflected in the UI without manual refresh
- All tests pass
- No emojis anywhere

---

## Notes

- Model for all AI calls: `openai/gpt-oss-120b:free` via OpenRouter
- `.env` file at project root (gitignored) holds `OPENROUTER_API_KEY`
- Windows start/stop scripts: `.bat`; Mac/Linux: `.sh`
- Only one user for MVP but DB designed for multiple
- Keep it simple — no over-engineering, no extra features
