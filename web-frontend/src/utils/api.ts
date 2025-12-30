export const getApiUrl = (): string => {
    // 優先使用環境變數
    if (process.env.NEXT_PUBLIC_API_URL) {
        return process.env.NEXT_PUBLIC_API_URL.replace(/\/$/, '');
    }

    // 如果在瀏覽器中
    if (typeof window !== 'undefined') {
        const hostname = window.location.hostname;
        const port = window.location.port;
        const origin = window.location.origin;

        console.log(`[API Config] 偵測到瀏覽器環境: origin=${origin}, hostname=${hostname}, port=${port}`);

        // 如果是本地開發環境
        if (
            hostname === 'localhost' ||
            hostname === '127.0.0.1' ||
            hostname.startsWith('192.168.') ||
            port === '3000'
        ) {
            const url = 'http://localhost:8000';
            console.log(`[API Config] 判定為開發環境，使用直連後端: ${url}`);
            return url;
        }

        // 其他情況通常使用相對路徑
        console.log(`[API Config] 判定為生產/外部環境，使用相對路徑: /api/...`);
        return '';
    }

    return 'http://localhost:8000';
};
