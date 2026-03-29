import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { KanbanBoard } from "@/components/KanbanBoard";
import type { BoardData } from "@/lib/kanban";
import * as api from "@/lib/api";

vi.mock("@/lib/api");
vi.mock("@/lib/auth", () => ({ getToken: () => "test-token" }));

const testBoard: BoardData = {
  columns: [
    { id: "col-1", title: "Backlog", cardIds: [] },
    { id: "col-2", title: "Discovery", cardIds: [] },
    { id: "col-3", title: "In Progress", cardIds: [] },
    { id: "col-4", title: "Review", cardIds: [] },
    { id: "col-5", title: "Done", cardIds: [] },
  ],
  cards: {},
};

beforeEach(() => {
  vi.mocked(api.fetchBoard).mockResolvedValue(structuredClone(testBoard));
  vi.mocked(api.apiRenameColumn).mockResolvedValue(undefined);
  vi.mocked(api.apiCreateCard).mockImplementation(
    async (_token, _colId, title, details) => ({
      id: "card-new",
      title,
      details,
    })
  );
  vi.mocked(api.apiDeleteCard).mockResolvedValue(undefined);
  vi.mocked(api.apiMoveCard).mockResolvedValue(undefined);
});

async function getFirstColumn() {
  return (await screen.findAllByTestId(/column-/i))[0];
}

describe("KanbanBoard", () => {
  it("renders five columns", async () => {
    render(<KanbanBoard />);
    expect(await screen.findAllByTestId(/column-/i)).toHaveLength(5);
  });

  it("renames a column", async () => {
    render(<KanbanBoard />);
    const column = await getFirstColumn();
    const input = within(column).getByLabelText("Column title");
    await userEvent.clear(input);
    await userEvent.type(input, "New Name");
    expect(input).toHaveValue("New Name");
  });

  it("adds and removes a card", async () => {
    render(<KanbanBoard />);
    const column = await getFirstColumn();
    const addButton = within(column).getByRole("button", {
      name: /add a card/i,
    });
    await userEvent.click(addButton);

    const titleInput = within(column).getByPlaceholderText(/card title/i);
    await userEvent.type(titleInput, "New card");
    const detailsInput = within(column).getByPlaceholderText(/details/i);
    await userEvent.type(detailsInput, "Notes");

    await userEvent.click(within(column).getByRole("button", { name: /add card/i }));

    expect(await within(column).findByText("New card")).toBeInTheDocument();

    const deleteButton = within(column).getByRole("button", {
      name: /delete new card/i,
    });
    await userEvent.click(deleteButton);

    expect(within(column).queryByText("New card")).not.toBeInTheDocument();
  });
});
