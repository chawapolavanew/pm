# Frontend: Kanban Studio

## Overview

A Next.js 16 frontend-only Kanban board demo. No backend, no auth, no persistence — all state is in-memory. This will be integrated into the full Docker/FastAPI stack in later parts of the plan.

## Stack

- **Next.js** 16.1.6 with React 19
- **TypeScript** (strict mode)
- **Tailwind CSS** v4 (PostCSS plugin)
- **@dnd-kit** for drag-and-drop (`/core` v6, `/sortable` v10)
- **Vitest** + React Testing Library for unit tests
- **Playwright** for E2E tests
- Fonts: Space Grotesk (display), Manrope (body) via Google Fonts

## Structure

```
src/
  app/
    layout.tsx          Root layout (fonts, globals)
    page.tsx            Home — renders KanbanBoard
    globals.css         CSS variables + Tailwind import
  components/
    KanbanBoard.tsx     Board state, drag-drop logic, top-level render
    KanbanColumn.tsx    Single column — droppable, editable title
    KanbanCard.tsx      Single card — sortable, removable
    KanbanCardPreview.tsx  Overlay shown during drag
    NewCardForm.tsx     Inline form to add a card to a column
  lib/
    kanban.ts           Types (Board, Column, Card) + moveCard() utility
tests/
  kanban.spec.ts        Playwright E2E tests
```

## Key Patterns

**State**: Lives entirely in `KanbanBoard` via `useState`. No external store. `cards` is a normalized `Record<id, Card>`; columns hold ordered `cardIds` arrays.

**Drag and drop**: `DndContext` with `PointerSensor` (6 px activation threshold) and `closestCorners` detection. `moveCard()` in `lib/kanban.ts` handles both same-column reorder and cross-column moves without mutation.

**Columns**: 5 fixed columns (Backlog, Discovery, In Progress, Review, Done). Titles are editable inline. Columns cannot be added or removed in the current implementation.

**No AI sidebar, no auth, no API calls.** These are added in later parts of the plan.

## Color Scheme (CSS variables)

| Variable             | Value     | Usage                          |
|----------------------|-----------|--------------------------------|
| `--accent-yellow`    | `#ecad0a` | Accent lines, highlights       |
| `--primary-blue`     | `#209dd7` | Links, key sections            |
| `--secondary-purple` | `#753991` | Submit buttons, actions        |
| `--navy-dark`        | `#032147` | Main headings                  |
| `--gray-text`        | `#888888` | Supporting text, labels        |

## Tests

```bash
npm run test:unit       # Vitest (src/**/*.test.{ts,tsx})
npm run test:e2e        # Playwright (tests/*.spec.ts) — needs dev server
npm run test:all        # Both
```

Unit tests cover `moveCard()` logic and board component interactions (column rename, add/remove card). E2E tests cover board render, adding a card, and drag-and-drop between columns.

## What Changes During Integration

- `page.tsx` will gain an auth gate (Part 4)
- Board state will be loaded from and saved to the backend API (Part 7)
- An AI chat sidebar component will be added (Part 10)
- `next.config.ts` will be updated for static export to be served by FastAPI (Part 3)
