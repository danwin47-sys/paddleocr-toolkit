'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

export default function Sidebar() {
    const pathname = usePathname();
    return (
        <aside className="app-sidebar">
            {/* Logo */}
            <div className="sidebar-logo">
                P
            </div>

            {/* Navigation */}
            <nav className="sidebar-nav">
                <Link href="/" className={`sidebar-nav-item ${pathname === '/' ? 'active' : ''}`} title="首頁">
                    <span>🏠</span>
                </Link>
                <button className="sidebar-nav-item" title="檔案管理">
                    <span>📁</span>
                </button>
                <Link href="/logs" className={`sidebar-nav-item ${pathname === '/logs' ? 'active' : ''}`} title="系統日誌">
                    <span>🔍</span>
                </Link>
                <button className="sidebar-nav-item" title="設定">
                    <span>⚙️</span>
                </button>
            </nav>
        </aside>
    );
}
