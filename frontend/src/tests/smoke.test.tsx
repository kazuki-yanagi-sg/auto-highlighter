import { render, screen } from "@testing-library/react";
import { App } from "../App";

// ランディングはライブラリ画面(ロゴ「マーカー」)。
test("App はロゴを表示する", () => {
  render(<App />);
  expect(screen.getByText("マーカー支援")).toBeInTheDocument();
});
