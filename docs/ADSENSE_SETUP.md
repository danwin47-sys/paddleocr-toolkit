# 🚀 Google AdSense 整合指南

**完成時間**：15-30 分鐘  
**難度**：⭐ 簡單

---

## ✅ 已完成

1. ✅ 創建 `AdBanner.tsx` 組件
2. ⏳ 修改 `layout.tsx`（下一步）
3. ⏳ 在 `page.tsx` 中放置廣告
4. ⏳ 申請 AdSense 帳號

---

## 📝 步驟 1：申請 Google AdSense

### 1.1 前往 AdSense 網站
```
https://www.google.com/adsense
```

### 1.2 註冊流程
1. 使用 Google 帳號登入
2. 填寫網站 URL：`https://your-vercel-app.vercel.app`
3. 填寫聯絡資訊
4. 同意條款

### 1.3 獲取代碼
註冊後會獲得：
- **發布商 ID**：`ca-pub-XXXXXXXXXXXXXXXX`
- **AdSense 代碼**

---

## 🔧 步驟 2：修改 layout.tsx

### 2.1 打開檔案
```
web-frontend/src/app/layout.tsx
```

### 2.2 在 `<head>` 區塊最後添加
```typescript
{/* Google AdSense - 廣告營利 */}
<Script
  async
  src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-YOUR_PUBLISHER_ID"
  crossOrigin="anonymous"
  strategy="afterInteractive"
/>
```

### 2.3 完整範例
```typescript
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-TW" suppressHydrationWarning>
      <head>
        {/* Google Analytics - 已存在 */}
        {GA_TRACKING_ID && (
          <Script src={`https://www.googletagmanager.com/gtag/js?id=${GA_TRACKING_ID}`} strategy="afterInteractive" />
        )}
        
        {/* Google AdSense - 新增這一段 */}
        <Script
          async
          src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-YOUR_PUBLISHER_ID"
          crossOrigin="anonymous"
          strategy="afterInteractive"
        />
      </head>
      <body>{children}</body>
    </html>
  );
}
```

**重要**：將 `YOUR_PUBLISHER_ID` 替換為您的實際發布商 ID

---

## 📍 步驟 3：在頁面中放置廣告

### 3.1 在 page.tsx 頂部 import
```typescript
import AdBanner, { TopBannerAd, SidebarAd } from '@/components/AdBanner';
```

### 3.2 建議的廣告位置

#### 位置 1：頂部橫幅（高價值）
```typescript
{/* 模式切換標籤之前 */}
<TopBannerAd slot="YOUR_SLOT_ID_1" />

{/* Mode Tabs */}
<div style={{ display: 'flex', gap: 'var(--spacing-2)' }}>
  {/* 標籤切換 */}
</div>
```

#### 位置 2：側邊欄（中價值）
```typescript
{/* 左側欄內容前 */}
<div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-6)' }}>
  <SidebarAd slot="YOUR_SLOT_ID_2" />
  
  {/* Format Selector */}
  {/* Settings: OCR Mode */}
</div>
```

#### 位置 3：結果區旁（高價值）
```typescript
{/* 結果顯示區域 */}
{result && (
  <div style={{ display: 'flex', gap: '20px' }}>
    {/* OCR 結果 */}
    <div style={{ flex: 1 }}>
      {/* 結果內容 */}
    </div>
    
    {/* 右側廣告 */}
    <div style={{ width: '300px' }}>
      <AdBanner 
        slot="YOUR_SLOT_ID_3"
        format="vertical"
        style={{ width: '300px', height: '600px' }}
        label="結果廣告"
      />
    </div>
  </div>
)}
```

---

## 🎨 步驟 4：創建廣告單元（AdSense 控制台）

### 4.1 登入 AdSense
前往：https://www.google.com/adsense

### 4.2 創建廣告單元
1. 點擊「廣告」→「依網站」
2. 點擊「新增廣告單元」
3. 選擇「展示廣告」

### 4.3 配置各個單元

**廣告單元 1：頂部橫幅**
- 名稱：`Top Banner`
- 類型：橫幅廣告
- 尺寸：728x90 或響應式
- 獲得 Slot ID（例：1234567890）

**廣告單元 2：側邊欄**
- 名稱：`Sidebar Ad`
- 類型：展示廣告
- 尺寸：300x250
- 獲得 Slot ID（例：0987654321）

**廣告單元 3：結果區**
- 名稱：`Result Page Ad`
- 類型：展示廣告
- 尺寸：300x600
- 獲得 Slot ID（例：1122334455）

---

## 🔗 步驟 5：更新組件中的 ID

### 5.1 修改 AdBanner.tsx
```typescript
// 第 72 行，替換發布商 ID
data-ad-client="ca-pub-YOUR_PUBLISHER_ID"
// 改為
data-ad-client="ca-pub-1234567890123456"  // 您的實際 ID
```

### 5.2 在 page.tsx 中使用實際 Slot ID
```typescript
<TopBannerAd slot="1234567890" />  // 替換為實際 slot
<SidebarAd slot="0987654321" />    // 替換為實際 slot
<AdBanner slot="1122334455" />     // 替換為實際 slot
```

---

## ✅ 步驟 6：測試和部署

### 6.1 本地測試
```bash
cd web-frontend
npm run dev
```

訪問 http://localhost:3000

**預期結果**：
- 看到廣告佔位符（開發環境）
- 或顯示「AdSense 正在審核」

### 6.2 部署到 Vercel
```bash
git add .
git commit -m "feat: 整合 Google AdSense 廣告系統"
git push origin master
```

Vercel 會自動部署

### 6.3 等待 AdSense 審核
- 審核時間：1-3 天
- 審核期間可能顯示空白或測試廣告
- 通過後會顯示真實廣告

---

## 📊 步驟 7：優化廣告表現

### 7.1 監控指標（AdSense 控制台）
- CPM（每千次曝光收入）
- CTR（點擊率）
- RPM（每千次頁面收入）

### 7.2 優化建議
1. **A/B 測試位置** - 測試不同廣告位置
2. **調整廣告數量** - 3-5 個為佳
3. **響應式設計** - 確保手機上也正常顯示
4. **優質內容** - 提高流量和停留時間

---

## 🎯 快速上線檢查清單

- [ ] 已申請 Google AdSense 帳號
- [ ] 獲得發布商 ID (ca-pub-XXXXXX)
- [ ] 創建至少 3 個廣告單元
- [ ] 修改 layout.tsx（加入 AdSense 腳本）
- [ ] 修改 AdBanner.tsx（替換發布商 ID）
- [ ] 在 page.tsx 中放置廣告
- [ ] 本地測試確認
- [ ] 部署到 Vercel
- [ ] 提交 AdSense 審核
- [ ] 等待審核通過（1-3天）

---

## 💰 預期收入

假設每日訪問量：
```
100 人/天 → $60-150 USD/月
500 人/天 → $300-750 USD/月
1,000 人/天 → $600-1,500 USD/月
5,000 人/天 → $3,000-7,500 USD/月
```

---

## 🆘 常見問題

### Q1：廣告不顯示？
A：
1. 檢查 AdSense 是否審核通過
2. 檢查發布商 ID 是否正確
3. 檢查 Slot ID 是否正確
4. 清除瀏覽器快取

### Q2：顯示「廣告位置預留」？
A：這是開發模式的佔位符，正常現象
- 確保已設置正確的 Slot ID
- 部署到生產環境後會顯示真實廣告

### Q3：收入很低？
A：
1. 需要更多流量
2. 優化廣告位置
3. 提升內容品質
4. 改善 SEO

---

## 🚀 下一步

1. **優先執行**：申請 AdSense（今天）
2. **等待期間**：優化 SEO 和內容
3. **審核通過後**：監控並優化廣告表現

**預計時間表**：
- Day 1：申請 AdSense
- Day 2-3：整合廣告代碼
- Day 4-7：等待審核
- Day 8+：開始賺錢！💰

---

**恭喜！您即將開始盈利之路！** 🎉
