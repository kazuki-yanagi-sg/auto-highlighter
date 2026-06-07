import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { VoicePlayer } from "./VoicePlayer";

beforeAll(() => {
  // jsdom は再生未実装なのでスタブ
  HTMLMediaElement.prototype.play = () => Promise.resolve();
  HTMLMediaElement.prototype.pause = () => {};
});

test("4色のボタンを表示する", () => {
  render(<VoicePlayer documentId={1} />);
  expect(screen.getByRole("button", { name: /重要/ })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: /注意/ })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: /参照/ })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: /具体例/ })).toBeInTheDocument();
});

test("色を選ぶと audio の src がストリーミングURLになる", async () => {
  render(<VoicePlayer documentId={42} />);
  await userEvent.click(screen.getByRole("button", { name: /重要/ }));
  expect(screen.getByTestId("audio")).toHaveAttribute(
    "src",
    "/api/documents/42/tts?color=red",
  );
});

test("再生/一時停止ボタンがある", async () => {
  render(<VoicePlayer documentId={1} />);
  await userEvent.click(screen.getByRole("button", { name: /参照/ }));
  expect(
    screen.getByRole("button", { name: /再生|一時停止|停止/ }),
  ).toBeInTheDocument();
});

test("audio がエラーになるとメッセージを表示する", async () => {
  render(<VoicePlayer documentId={1} />);
  await userEvent.click(screen.getByRole("button", { name: /具体例/ }));
  fireEvent.error(screen.getByTestId("audio"));
  expect(screen.getByText(/再生できません|失敗/)).toBeInTheDocument();
});
