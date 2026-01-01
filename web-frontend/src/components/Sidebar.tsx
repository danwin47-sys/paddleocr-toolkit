'use client';

export default function Sidebar() {
    return (
        <aside className="app-sidebar">
            {/* Logo */}
            <div className="sidebar-logo">
                P
            </div>

            {/* Navigation */}
            <nav className="sidebar-nav">
                <button className="sidebar-nav-item active" title="首頁">
                    <span>🏠</span>
                </button>
                <button className="sidebar-nav-item" title="檔案管理">
                    <span>📁</span>
                </button>
                <button className="sidebar-nav-item" title="設定">
                    <span>⚙️</span>
                </button>
            </nav>
        </aside>
    );
}
