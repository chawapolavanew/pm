import type { BoardData } from "@/lib/kanban";

export class ApiError extends Error {
  constructor(public status: number) {
    super(`API error: ${status}`);
  }
}

function colNum(colId: string): number {
  return parseInt(colId.replace("col-", ""), 10);
}

function cardNum(cardId: string): number {
  return parseInt(cardId.replace("card-", ""), 10);
}

async function apiFetch(
  url: string,
  options: RequestInit,
  token: string
): Promise<Response> {
  const res = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
      ...(options.headers ?? {}),
    },
  });
  if (!res.ok) throw new ApiError(res.status);
  return res;
}

export async function fetchBoard(token: string): Promise<BoardData> {
  const res = await apiFetch("/api/board", { method: "GET" }, token);
  return res.json();
}

export async function apiRenameColumn(
  token: string,
  colId: string,
  title: string
): Promise<void> {
  await apiFetch(
    `/api/columns/${colNum(colId)}`,
    { method: "PATCH", body: JSON.stringify({ title }) },
    token
  );
}

export async function apiCreateCard(
  token: string,
  columnId: string,
  title: string,
  details: string
): Promise<{ id: string; title: string; details: string }> {
  const res = await apiFetch(
    "/api/cards",
    {
      method: "POST",
      body: JSON.stringify({ column_id: colNum(columnId), title, details }),
    },
    token
  );
  return res.json();
}

export async function apiDeleteCard(
  token: string,
  cardId: string
): Promise<void> {
  await apiFetch(`/api/cards/${cardNum(cardId)}`, { method: "DELETE" }, token);
}

export async function apiMoveCard(
  token: string,
  cardId: string,
  columnId: string,
  position: number
): Promise<void> {
  await apiFetch(
    `/api/cards/${cardNum(cardId)}/move`,
    {
      method: "PATCH",
      body: JSON.stringify({ column_id: colNum(columnId), position }),
    },
    token
  );
}
