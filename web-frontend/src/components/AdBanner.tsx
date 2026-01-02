/**
 * Google AdSense 廣告橫幅組件
 * 
 * 使用說明：
 * 1. 先到 https://www.google.com/adsense 申請帳號
 * 2. 獲得發布商 ID (ca-pub-XXXXXXXXXXXXXXXX)
 * 3. 為每個廣告單元創建 slot ID
 * 4. 替換下面的 YOUR_PUBLISHER_ID
 * 
 * 使用範例：
 * <AdBanner 
 *   slot="1234567890"
 *   format="horizontal"
 *   style={{ height: '90px' }}
 * />
 */

'use client';

import { useEffect } from 'react';

interface AdBannerProps {
    /**
     * AdSense 廣告單元 slot ID
     * 從 AdSense 控制台獲取
     */
    slot: string;

    /**
     * 廣告格式
     * - auto: 自適應
     * - horizontal: 橫幅
     * - rectangle: 方形
     * - vertical: 垂直
     */
    format?: 'auto' | 'horizontal' | 'rectangle' | 'vertical';

    /**
     * 自定義樣式
     */
    style?: React.CSSProperties;

    /**
     * 是否全寬響應式
     */
    responsive?: boolean;

    /**
     * 廣告標籤（用於標識不同位置）
     */
    label?: string;
}

export default function AdBanner({
    slot,
    format = 'auto',
    style,
    responsive = true,
    label,
}: AdBannerProps) {
    useEffect(() => {
        try {
            // 確保 adsbygoogle 可用
            if (typeof window !== 'undefined') {
                (window as any).adsbygoogle = (window as any).adsbygoogle || [];
                (window as any).adsbygoogle.push({});
            }
        } catch (err) {
            console.error('AdSense 載入錯誤:', err);
        }
    }, []);

    // 如果沒有設置 slot，顯示佔位符（開發環境）
    if (!slot || slot === 'YOUR_SLOT_ID') {
        return (
            <div
                style={{
                    ...style,
                    background: '#f0f0f0',
                    border: '2px dashed #ccc',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: '#666',
                    fontSize: '14px',
                    textAlign: 'center',
                    padding: '20px',
                }}
            >
                <div>
                    📢 廣告位置預留
                    {label && <div style={{ fontSize: '12px', marginTop: '5px' }}>({label})</div>}
                    <div style={{ fontSize: '12px', marginTop: '5px', color: '#999' }}>
                        請設置 AdSense Slot ID
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div style={{ margin: '20px 0', textAlign: 'center' }}>
            {label && (
                <div style={{ fontSize: '10px', color: '#999', marginBottom: '5px' }}>
                    廣告
                </div>
            )}
            <ins
                className="adsbygoogle"
                style={style || { display: 'block' }}
                data-ad-client="ca-pub-YOUR_PUBLISHER_ID"
                data-ad-slot={slot}
                data-ad-format={format}
                data-full-width-responsive={responsive ? 'true' : 'false'}
            />
        </div>
    );
}

/**
 * 常用廣告尺寸預設
 */
export const AdSizes = {
    // 橫幅廣告
    leaderboard: { width: '728px', height: '90px' },      // 排行榜
    banner: { width: '468px', height: '60px' },            // 橫幅

    // 方形廣告
    mediumRectangle: { width: '300px', height: '250px' }, // 中型矩形
    largeRectangle: { width: '336px', height: '280px' },  // 大型矩形
    square: { width: '250px', height: '250px' },          // 正方形

    // 摩天樓廣告
    wideSkyscraper: { width: '160px', height: '600px' },  // 寬型摩天樓
    skyscraper: { width: '120px', height: '600px' },      // 摩天樓
    halfPage: { width: '300px', height: '600px' },        // 半頁

    // 行動裝置
    mobileBanner: { width: '320px', height: '50px' },     // 手機橫幅
    mobileLarge: { width: '320px', height: '100px' },     // 手機大型
};

/**
 * 預設廣告組件（常用尺寸）
 */
export function TopBannerAd({ slot }: { slot: string }) {
    return (
        <AdBanner
            slot={slot}
            format="horizontal"
            style={AdSizes.leaderboard}
            label="頂部橫幅"
        />
    );
}

export function SidebarAd({ slot }: { slot: string }) {
    return (
        <AdBanner
            slot={slot}
            format="rectangle"
            style={AdSizes.mediumRectangle}
            label="側邊欄"
        />
    );
}

export function ContentAd({ slot }: { slot: string }) {
    return (
        <AdBanner
            slot={slot}
            format="rectangle"
            style={AdSizes.largeRectangle}
            label="內容區"
        />
    );
}
