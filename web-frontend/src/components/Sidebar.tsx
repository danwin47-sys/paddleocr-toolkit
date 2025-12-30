export default function Sidebar() {
    return (
        <aside className="sidebar">
            {/* Logo */}
            <div className="logo">
                P
            </div>

            {/* Nav Items */}
            <nav className="flex flex-col items-center" style={{ gap: '2rem' }}>
                <button className="action-btn text-white" style={{ transform: 'scale(1.1)' }}>
                    <span className="text-2xl">🏠</span>
                </button>
                <button className="action-btn">
                    <span className="text-2xl">📁</span>
                </button>
                <button className="action-btn">
                    <span className="text-2xl">⚙️</span>
                </button>
            </nav>
        </aside>
    );
}
