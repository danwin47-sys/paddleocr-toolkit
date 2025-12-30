"use client";

import { useState, useRef } from "react";
import Sidebar from "@/components/Sidebar";
import { useOCR } from "@/hooks/useOCR";
import SettingsModal from "@/components/SettingsModal";
import TranslationModal from "@/components/TranslationModal";
import FormatSelector from "@/components/FormatSelector";

export default function Home() {
  const { uploadFile, isProcessing, progress, statusText, result, error } = useOCR();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [useGemini, setUseGemini] = useState(false);
  const [useClaude, setUseClaude] = useState(false);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isTranslationOpen, setIsTranslationOpen] = useState(false);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const file = e.target.files[0];
      // 檢查是否需要 Client-side API Key 驗證
      const gKey = localStorage.getItem('gemini_api_key') || undefined;
      const cKey = localStorage.getItem('claude_api_key') || undefined;

      if (useGemini && !gKey) {
        alert('請先在設定 (⚙️) 中輸入 Gemini API Key');
        setIsSettingsOpen(true);
        return;
      }
      if (useClaude && !cKey) {
        alert('請先在設定 (⚙️) 中輸入 Claude API Key');
        setIsSettingsOpen(true);
        return;
      }

      // 從設定讀取 OCR 模式 (預設 hybrid)
      const ocrMode = localStorage.getItem('ocr_mode') || 'hybrid';

      // 執行上傳 (僅在開關開啟時傳遞 Key)
      uploadFile(
        file,
        ocrMode,
        useGemini ? gKey : undefined,
        useClaude ? cKey : undefined
      );
    }
  };

  const triggerUpload = () => {
    fileInputRef.current?.click();
  };

  return (
    <div className="flex" style={{ minHeight: '100vh' }}>
      <SettingsModal isOpen={isSettingsOpen} onClose={() => setIsSettingsOpen(false)} />
      <TranslationModal
        isOpen={isTranslationOpen}
        onClose={() => setIsTranslationOpen(false)}
        originalText={result?.results?.raw_result || ''}
      />

      {/* Sidebar */}
      <Sidebar />

      {/* Main Content */}
      <main className="main-content">
        {/* Header */}
        <header className="flex justify-between items-center" style={{ marginBottom: '40px' }}>
          <div>
            <h1 className="header-title">
              Dashboard
            </h1>
            <p className="text-slate-400">智慧文件辨識系統</p>
          </div>
          <button
            className="action-btn"
            style={{ width: '40px', height: '40px', fontSize: '1.5rem' }}
            onClick={() => setIsSettingsOpen(true)}
          >
            ⚙️
          </button>
        </header>

        {/* Dashboard Grid */}
        <div className="dashboard-grid">
          {/* Left Section: Upload & Features */}
          <div className="flex flex-col" style={{ gap: '20px' }}>

            {/* Upload Zone */}
            <div
              className="glass-card text-center"
              style={{ padding: '60px 20px', border: '2px dashed var(--glass-border)', cursor: isProcessing ? 'wait' : 'pointer' }}
              onClick={!isProcessing ? triggerUpload : undefined}
            >
              <input
                type="file"
                ref={fileInputRef}
                onChange={handleFileChange}
                className="hidden"
                accept=".pdf,.png,.jpg,.jpeg"
              />

              {!isProcessing ? (
                <>
                  <span style={{ fontSize: '50px', display: 'block', marginBottom: '20px' }}>
                    ☁️
                  </span>
                  <h2 style={{ fontSize: '1.25rem', fontWeight: 600, marginBottom: '10px' }}>點選上傳檔案</h2>
                  <p className="text-slate-400">支援 PDF, PNG, JPG (最大 2500px)</p>
                </>
              ) : (
                <div className="w-full">
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', fontSize: '14px' }}>
                    <span>{statusText}</span>
                    <span>{Math.round(progress)}%</span>
                  </div>
                  <div style={{ height: '6px', background: 'rgba(255,255,255,0.1)', borderRadius: '3px', overflow: 'hidden' }}>
                    <div style={{ height: '100%', background: 'var(--primary)', width: `${progress}%`, transition: 'width 0.3s' }}></div>
                  </div>
                </div>
              )}
            </div>

            {/* Error Message */}
            {error && (
              <div style={{ padding: '15px', background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.2)', borderRadius: '12px', color: '#fca5a5' }}>
                ❌ {error}
              </div>
            )}

            {/* Feature Switches */}
            <div className="feature-card">
              <div className="flex items-center" style={{ gap: '15px' }}>
                <div style={{ width: '32px', height: '32px', background: 'white', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#1e1b4b', fontWeight: 'bold' }}>
                  G
                </div>
                <div>
                  <p className="font-bold">Gemini 3 語義校正</p>
                  <p className="text-slate-400" style={{ fontSize: '12px' }}>使用 Google AI 修復辨識錯誤</p>
                </div>
              </div>
              <div
                onClick={() => setUseGemini(!useGemini)}
                style={{ width: '48px', height: '24px', background: useGemini ? 'var(--primary)' : 'rgba(255,255,255,0.1)', borderRadius: '34px', position: 'relative', cursor: 'pointer', transition: '0.3s' }}
              >
                <div style={{ width: '18px', height: '18px', background: 'white', borderRadius: '50%', position: 'absolute', top: '3px', left: useGemini ? '27px' : '3px', transition: '0.3s' }}></div>
              </div>
            </div>

            <div className="feature-card">
              <div className="flex items-center" style={{ gap: '15px' }}>
                <div style={{ width: '32px', height: '32px', background: '#f97316', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'white', fontWeight: 'bold' }}>
                  C
                </div>
                <div>
                  <p className="font-bold">Claude 3.5 語義校正</p>
                  <p className="text-slate-400" style={{ fontSize: '12px' }}>使用 Anthropic AI 深度解析</p>
                </div>
              </div>
              <div
                onClick={() => setUseClaude(!useClaude)}
                style={{ width: '48px', height: '24px', background: useClaude ? 'var(--primary)' : 'rgba(255,255,255,0.1)', borderRadius: '34px', position: 'relative', cursor: 'pointer', transition: '0.3s' }}
              >
                <div style={{ width: '18px', height: '18px', background: 'white', borderRadius: '50%', position: 'absolute', top: '3px', left: useClaude ? '27px' : '3px', transition: '0.3s' }}></div>
              </div>
            </div>
          </div>

          {/* Right Section: Results & Recent Files */}
          <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
            <div className="flex justify-between items-center" style={{ marginBottom: '20px' }}>
              <h3 style={{ fontSize: '1.125rem', fontWeight: 600 }}>
                {result ? '辨識結果' : '最近處理檔案'}
              </h3>
              {result?.results?.confidence && (
                <span style={{ fontSize: '12px', padding: '4px 8px', borderRadius: '6px', background: 'rgba(16, 185, 129, 0.1)', color: 'var(--accent)' }}>
                  信心度: {Math.round(result.results.confidence * 100)}%
                </span>
              )}
            </div>

            <div style={{ flex: 1, overflowY: 'auto', background: 'rgba(0,0,0,0.2)', borderRadius: '12px', padding: '20px', whiteSpace: 'pre-wrap', fontSize: '14px', lineHeight: '1.6', color: '#cbd5e1', minHeight: '300px' }}>
              {result ? (
                <>
                  {/* Action Buttons */}
                  <div style={{ marginBottom: '20px' }}>
                    {/* Format Selector */}
                    <FormatSelector taskId={result.task_id} />

                    {/* Other Actions */}
                    <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
                      <button
                        className="action-btn"
                        style={{ flex: 1, minWidth: '120px' }}
                        onClick={() => {
                          const text = result.results?.raw_result || '';
                          navigator.clipboard.writeText(text);
                          alert('✅ 已複製到剪貼簿');
                        }}
                      >
                        📋 複製文字
                      </button>
                      <button
                        className="action-btn"
                        style={{ flex: 1, minWidth: '120px', background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}
                        onClick={() => setIsTranslationOpen(true)}
                      >
                        🌐 翻譯
                      </button>
                    </div>
                  </div>
                  <div style={{ marginBottom: '20px' }}>
                    {result.results?.raw_result || "⚠️ raw_result 為空"}
                  </div>

                  {/* Debug Panel */}
                  <details style={{ marginTop: '20px', padding: '10px', background: 'rgba(0,0,0,0.3)', borderRadius: '8px', fontSize: '12px' }}>
                    <summary style={{ cursor: 'pointer', color: '#fbbf24', fontWeight: 'bold' }}>🔍 除錯資訊 (Debug)</summary>
                    <div style={{ marginTop: '10px', color: '#94a3b8' }}>
                      <p><strong>Task ID:</strong> {result.task_id}</p>
                      <p><strong>Status:</strong> {result.status}</p>
                      <p><strong>Progress:</strong> {result.progress}%</p>
                      <p><strong>Error:</strong> {result.error || 'null'}</p>
                      <hr style={{ margin: '10px 0', borderColor: 'rgba(255,255,255,0.1)' }} />
                      <p><strong>Results Object:</strong></p>
                      <pre style={{ background: 'rgba(0,0,0,0.5)', padding: '10px', borderRadius: '4px', overflow: 'auto', maxHeight: '200px' }}>
                        {JSON.stringify(result.results, null, 2)}
                      </pre>
                      <hr style={{ margin: '10px 0', borderColor: 'rgba(255,255,255,0.1)' }} />
                      <p><strong>完整回應:</strong></p>
                      <pre style={{ background: 'rgba(0,0,0,0.5)', padding: '10px', borderRadius: '4px', overflow: 'auto', maxHeight: '200px' }}>
                        {JSON.stringify(result, null, 2)}
                      </pre>
                    </div>
                  </details>
                </>
              ) : (
                <p className="text-center text-slate-400" style={{ padding: '20px' }}>尚無資料</p>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
