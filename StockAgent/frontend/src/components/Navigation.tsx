import Link from "next/link";

const navItems = [
  { href: "/", label: "대시보드" },
  { href: "/trades", label: "매매 내역" },
  { href: "/strategy", label: "전략 설정" },
  { href: "/scanner", label: "장초 스캐너" },
  { href: "/reports", label: "리포트" },
];

export default function Navigation() {
  return (
    <nav className="w-64 bg-gray-900 text-white p-4">
      <h1 className="text-xl font-bold mb-8">StockAgent</h1>
      <ul className="space-y-2">
        {navItems.map((item) => (
          <li key={item.href}>
            <Link
              href={item.href}
              className="block px-4 py-2 rounded hover:bg-gray-700"
            >
              {item.label}
            </Link>
          </li>
        ))}
      </ul>
    </nav>
  );
}

export { navItems };
