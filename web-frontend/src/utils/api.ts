/**
 * 獲取後端 API 的基礎 URL
 * 優先使用環境變數，否則根據目前位址推斷
 */
export const getApiUrl = (): string => {
    // 優先使用 NEXT_PUBLIC_API_URL
    if (process.env.NEXT_PUBLIC_API_URL) {
        return process.env.NEXT_PUBLIC_API_URL.replace(/\/$/, '');
    }

    // 如果在瀏覽器中
    if (typeof window !== 'undefined') {
        const hostname = window.location.hostname;

        // 如果是 localhost
        if (hostname === 'localhost' || hostname === '127.0.0.1') {
            return 'http://localhost:8000';
        }

        // 其他情況通常使用相對路徑，交由 Next.js rewrites 處理
        // 但為了穩定性，這裡也可以返回空字串讓 fetch 使用相對路徑
        return '';
    }

    return 'http://localhost:8000';
};
