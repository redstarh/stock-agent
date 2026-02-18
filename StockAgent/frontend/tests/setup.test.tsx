/**
 * T-F1: 프로젝트 초기 셋업 테스트
 */
import { render, screen } from "@testing-library/react";
import Navigation from "@/components/Navigation";

describe("T-F1: 프로젝트 초기 셋업", () => {
  test("Navigation component renders without crash", () => {
    const { container } = render(<Navigation />);
    expect(container).toBeTruthy();
  });

  test("Navigation contains all required links", () => {
    render(<Navigation />);
    expect(screen.getByText("대시보드")).toBeInTheDocument();
    expect(screen.getByText("매매 내역")).toBeInTheDocument();
    expect(screen.getByText("전략 설정")).toBeInTheDocument();
    expect(screen.getByText("장초 스캐너")).toBeInTheDocument();
    expect(screen.getByText("리포트")).toBeInTheDocument();
  });

  test("App title is displayed", () => {
    render(<Navigation />);
    expect(screen.getByText("StockAgent")).toBeInTheDocument();
  });
});
