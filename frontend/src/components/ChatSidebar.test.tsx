import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ChatSidebar } from "@/components/ChatSidebar";
import * as api from "@/lib/api";

vi.mock("@/lib/api");
vi.mock("@/lib/auth", () => ({ getToken: () => "test-token" }));

async function openSidebar() {
  await userEvent.click(screen.getByRole("button", { name: /open ai chat/i }));
}

describe("ChatSidebar", () => {
  beforeEach(() => {
    vi.mocked(api.apiChat).mockResolvedValue({ reply: "Got it!", board_updated: false });
  });

  it("is closed by default", () => {
    render(<ChatSidebar onBoardUpdated={() => {}} />);
    const sidebar = screen.getByTestId("chat-sidebar");
    expect(sidebar.className).toContain("translate-x-full");
  });

  it("opens when toggle button is clicked", async () => {
    render(<ChatSidebar onBoardUpdated={() => {}} />);
    await openSidebar();
    const sidebar = screen.getByTestId("chat-sidebar");
    expect(sidebar.className).toContain("translate-x-0");
  });

  it("sends a message and shows the reply", async () => {
    render(<ChatSidebar onBoardUpdated={() => {}} />);
    await openSidebar();

    await userEvent.type(screen.getByPlaceholderText(/ask the ai/i), "Hello AI");
    await userEvent.click(screen.getByRole("button", { name: /send message/i }));

    expect(await screen.findByText("Got it!")).toBeInTheDocument();
    expect(api.apiChat).toHaveBeenCalledWith("test-token", "Hello AI", []);
  });

  it("clears the input after sending", async () => {
    render(<ChatSidebar onBoardUpdated={() => {}} />);
    await openSidebar();

    const input = screen.getByPlaceholderText(/ask the ai/i);
    await userEvent.type(input, "Hi");
    await userEvent.click(screen.getByRole("button", { name: /send message/i }));

    expect(input).toHaveValue("");
  });

  it("calls onBoardUpdated when board_updated is true", async () => {
    vi.mocked(api.apiChat).mockResolvedValue({ reply: "Done!", board_updated: true });
    const onBoardUpdated = vi.fn();
    render(<ChatSidebar onBoardUpdated={onBoardUpdated} />);
    await openSidebar();

    await userEvent.type(screen.getByPlaceholderText(/ask the ai/i), "Add a card");
    await userEvent.click(screen.getByRole("button", { name: /send message/i }));

    await screen.findByText("Done!");
    expect(onBoardUpdated).toHaveBeenCalledTimes(1);
  });

  it("does not call onBoardUpdated when board_updated is false", async () => {
    const onBoardUpdated = vi.fn();
    render(<ChatSidebar onBoardUpdated={onBoardUpdated} />);
    await openSidebar();

    await userEvent.type(screen.getByPlaceholderText(/ask the ai/i), "What is on the board?");
    await userEvent.click(screen.getByRole("button", { name: /send message/i }));

    await screen.findByText("Got it!");
    expect(onBoardUpdated).not.toHaveBeenCalled();
  });

  it("shows an error message when the API fails", async () => {
    vi.mocked(api.apiChat).mockRejectedValue(new Error("fail"));
    render(<ChatSidebar onBoardUpdated={() => {}} />);
    await openSidebar();

    await userEvent.type(screen.getByPlaceholderText(/ask the ai/i), "Hello");
    await userEvent.click(screen.getByRole("button", { name: /send message/i }));

    expect(await screen.findByText(/something went wrong/i)).toBeInTheDocument();
  });

  it("passes conversation history on subsequent messages", async () => {
    render(<ChatSidebar onBoardUpdated={() => {}} />);
    await openSidebar();

    const input = screen.getByPlaceholderText(/ask the ai/i);
    await userEvent.type(input, "First message");
    await userEvent.click(screen.getByRole("button", { name: /send message/i }));
    await screen.findByText("Got it!");

    await userEvent.type(input, "Second message");
    await userEvent.click(screen.getByRole("button", { name: /send message/i }));
    await screen.findAllByText("Got it!");

    expect(api.apiChat).toHaveBeenLastCalledWith(
      "test-token",
      "Second message",
      expect.arrayContaining([
        expect.objectContaining({ role: "user", content: "First message" }),
        expect.objectContaining({ role: "assistant", content: "Got it!" }),
      ])
    );
  });
});
