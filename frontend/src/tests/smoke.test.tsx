import { render, screen } from "@testing-library/react";
import { App } from "../App";

// ランディングはライブラリ画面(ロゴ「速読」)。
test("App はロゴを表示する", () => {
  render(<App />);
  expect(screen.getByText("速読")).toBeInTheDocument();
});
