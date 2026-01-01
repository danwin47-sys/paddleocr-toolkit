"use client";

import { useState, useRef, useEffect } from "react";
import Sidebar from "@/components/Sidebar";
import { useOCR } from "@/hooks/useOCR";
import SettingsModal from "@/components/SettingsModal";
import TranslationModal from "@/components/TranslationModal";
import FormatSelector from "@/components/FormatSelector";
import BatchUpload from "@/components/BatchUpload";
import * as gtag from "@/lib/gtag";

export default function Home() {
  const { uploadFile, isProcessing, progress, statusText, result, error } = useOCR();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [useGemini, setUseGemini] = useState(false);
  const [useClaude, setUseClaude] = useState(false);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isTranslationOpen, setIsTranslationOpen] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [uploadMode, setUploadMode] = useState<'single' | 'batch'>('single');

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      processFile(e.target.files[0]);
    }
  };

  const processFile = (file: File) => {
    const gKey = localStorage.getItem('gemini_api_key') || undefined;
    const cKey = localStorage.getItem('claude_api_key') || undefined;

    if (useGemini && !gKey) {
      alert('請先在設定中輸入 Gemini API Key');
      setIsSettingsOpen(true);
      return;
    }
    if (useClaude && !cKey) {
      alert('請先在設定中輸入 Claude API Key');
      setIsSettingsOpen(true);
      return;
    }

    const ocrMode = localStorage.getItem('ocr_mode') || 'hybrid';

    // GA 事件追蹤：檔案上傳
    const fileExt = file.name.split('.').pop()?.toLowerCase() || 'unknown';
    gtag.event({
      action: 'upload',
      category: 'OCR',
      label: fileExt,
      value: Math.round(file.size / 1024), // KB
    });

    uploadFile(file, ocrMode, useGemini ? gKey : undefined, useClaude ? cKey : undefined);
  };

  const triggerUpload = () => {
    fileInputRef.current?.click();
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      processFile(e.dataTransfer.files[0]);
    }
  };

  const handleCopyText = () => {
    const text = result?.results?.raw_result || '';
    navigator.clipboard.writeText(text);
    alert('✅ 已複製到剪貼簿');

    // GA 事件追蹤：複製文字
    gtag.event({
      action: 'copy_text',
      category: 'OCR',
      label: 'clipboard',
    });
  };

  // GA 事件追蹤：OCR 完成
  useEffect(() => {
    if (result && !isProcessing) {
      const processingTime = (result as any).processing_time || 0;
      gtag.event({
        action: 'ocr_complete',
        category: 'OCR',
        label: (result as any).file_type || 'unknown',
        value: Math.round(processingTime),
      });
    }
  }, [result, isProcessing]);

  return (
    <div className="app-layout">
      <SettingsModal isOpen={isSettingsOpen} onClose={() => setIsSettingsOpen(false)} />
      <TranslationModal
        isOpen={isTranslationOpen}
        onClose={() => setIsTranslationOpen(false)}
        originalText={result?.results?.raw_result || ''}
      />

      {/* Sidebar */}
      <Sidebar />

      {/* Main Content */}
      <main className="app-main">
        {/* Header */}
        <header className="app-header">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <h1>智慧文件辨識系統</h1>
              <p>PaddleOCR Toolkit - 快速、精準的 OCR 服務</p>
            </div>
            <button
              className="btn btn-ghost"
              style={{ fontSize: '1.5rem' }}
              onClick={() => setIsSettingsOpen(true)}
              title="設定"
            >
              ⚙️
            </button>
          </div>
        </header>

        {/* Mode Tabs */}
        <div style={{ display: 'flex', gap: 'var(--spacing-2)', marginBottom: 'var(--spacing-6)', borderBottom: '1px solid var(--border-color)' }}>
          <button
            onClick={() => setUploadMode('single')}
            style={{
              padding: 'var(--spacing-3) var(--spacing-5)',
              background: uploadMode === 'single' ? 'var(--color-primary)' : 'transparent',
              color: uploadMode === 'single' ? 'white' : 'var(--text-primary)',
              border: 'none',
              borderBottom: uploadMode === 'single' ? '2px solid var(--color-primary)' : 'none',
              cursor: 'pointer',
              fontWeight: uploadMode === 'single' ? '600' : '400',
              transition: 'all 0.2s',
              borderRadius: '6px 6px 0 0'
            }}
          >
            📄 單檔案上傳
          </button>
          <button
            onClick={() => setUploadMode('batch')}
            style={{
              padding: 'var(--spacing-3) var(--spacing-5)',
              background: uploadMode === 'batch' ? 'var(--color-primary)' : 'transparent',
              color: uploadMode === 'batch' ? 'white' : 'var(--text-primary)',
              border: 'none',
              borderBottom: uploadMode === 'batch' ? '2px solid var(--color-primary)' : 'none',
              cursor: 'pointer',
              fontWeight: uploadMode === 'batch' ? '600' : '400',
              transition: 'all 0.2s',
              borderRadius: '6px 6px 0 0'
            }}
          >
            📦 批量處理
          </button>
        </div>

        {/* Content based on mode */}
        {uploadMode === 'single' ? (
          <div className="app-grid">
            {/* Left Column */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-6)' }}>

              {/* Upload Zone */}
              <div
                className={`upload-zone ${isDragging ? 'dragging' : ''}`}
                onClick={!isProcessing ? triggerUpload : undefined}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                style={{ cursor: isProcessing ? 'wait' : 'pointer' }}
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
                    <div className="upload-zone-icon">📄</div>
                    <div className="upload-zone-title">點選或拖曳上傳檔案</div>
                    <div className="upload-zone-subtitle">支援 PDF, PNG, JPG (最大 2500px)</div>
                  </>
                ) : (
                  <div style={{ width: '100%', maxWidth: '300px', margin: '0 auto' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 'var(--spacing-2)', fontSize: 'var(--font-size-sm)' }}>
                      <span className="text-secondary">{statusText}</span>
                      <span className="font-medium">{Math.round(progress)}%</span>
                    </div>
                    <div className="progress-bar">
                      <div className="progress-bar-fill" style={{ width: `${progress}%` }}></div>
                    </div>
                  </div>
                )}
              </div>

              {/* Error Message */}
              {error && (
                <div className="card" style={{ background: 'var(--color-error-light)', borderColor: 'var(--color-error)', color: 'var(--color-error)' }}>
                  ❌ {error}
                </div>
              )}

              {/* Feature Toggles */}
              <div className="card">
                <div className="card-header">
                  <span className="card-title">AI 智慧校正</span>
                </div>

                {/* Gemini Toggle */}
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: 'var(--spacing-4) 0', borderBottom: '1px solid var(--border-color)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-3)' }}>
                    <div style={{ width: '36px', height: '36px', background: 'linear-gradient(135deg, #4285f4, #34a853)', borderRadius: 'var(--radius-sm)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'white', fontWeight: '600' }}>
                      G
                    </div>
                    <div>
                      <div className="font-medium">Gemini 語義校正</div>
                      <div className="text-secondary" style={{ fontSize: 'var(--font-size-sm)' }}>使用 Google AI 修復辨識錯誤</div>
                    </div>
                  </div>
                  <button
                    onClick={() => setUseGemini(!useGemini)}
                    style={{
                      width: '48px',
                      height: '26px',
                      background: useGemini ? 'var(--color-primary)' : 'var(--color-slate-300)',
                      borderRadius: '13px',
                      border: 'none',
                      position: 'relative',
                      cursor: 'pointer',
                      transition: 'background var(--transition-fast)'
                    }}
                  >
                    <div style={{
                      width: '20px',
                      height: '20px',
                      background: 'white',
                      borderRadius: '50%',
                      position: 'absolute',
                      top: '3px',
                      left: useGemini ? '25px' : '3px',
                      transition: 'left var(--transition-fast)',
                      boxShadow: 'var(--shadow-sm)'
                    }}></div>
                  </button>
                </div>

                {/* Claude Toggle */}
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: 'var(--spacing-4) 0' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-3)' }}>
                    <div style={{ width: '36px', height: '36px', background: 'linear-gradient(135deg, #d97706, #ea580c)', borderRadius: 'var(--radius-sm)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'white', fontWeight: '600' }}>
                      C
                    </div>
                    <div>
                      <div className="font-medium">Claude 語義校正</div>
                      <div className="text-secondary" style={{ fontSize: 'var(--font-size-sm)' }}>使用 Anthropic AI 深度解析</div>
                    </div>
                  </div>
                  <button
                    onClick={() => setUseClaude(!useClaude)}
                    style={{
                      width: '48px',
                      height: '26px',
                      background: useClaude ? 'var(--color-primary)' : 'var(--color-slate-300)',
                      borderRadius: '13px',
                      border: 'none',
                      position: 'relative',
                      cursor: 'pointer',
                      transition: 'background var(--transition-fast)'
                    }}
                  >
                    <div style={{
                      width: '20px',
                      height: '20px',
                      background: 'white',
                      borderRadius: '50%',
                      position: 'absolute',
                      top: '3px',
                      left: useClaude ? '25px' : '3px',
                      transition: 'left var(--transition-fast)',
                      boxShadow: 'var(--shadow-sm)'
                    }}></div>
                  </button>
                </div>
              </div>
            </div>

            {/* Right Column: Results */}
            <div className="results-card">
              <div className="results-header">
                <span className="results-title">
                  {result ? '辨識結果' : '處理結果'}
                </span>
                {result?.results?.confidence && (
                  <span className="badge badge-success">
                    信心度: {Math.round(result.results.confidence * 100)}%
                  </span>
                )}
              </div>

              {result ? (
                <>
                  {/* Action Buttons */}
                  <div style={{ padding: 'var(--spacing-4) var(--spacing-6)', borderBottom: '1px solid var(--border-color)', display: 'flex', gap: 'var(--spacing-3)', flexWrap: 'wrap' }}>
                    <FormatSelector taskId={result.task_id} />
                    <button className="btn btn-secondary" onClick={handleCopyText}>
                      📋 複製文字
                    </button>
                    <button className="btn btn-primary" onClick={() => setIsTranslationOpen(true)}>
                      🌐 翻譯
                    </button>
                    <button
                      className="btn btn-primary"
                      onClick={() => {
                        const apiUrl = localStorage.getItem('api_url') || '';
                        const endpoint = apiUrl ? `${apiUrl}/api/export-searchable-pdf/${result.task_id}` : `/api/export-searchable-pdf/${result.task_id}`;
                        window.open(endpoint, '_blank');
                      }}
                      title="下載可搜尋 PDF（僅支援 PDF 檔案）"
                    >
                      📄 可搜尋 PDF
                    </button>
                  </div>

                  {/* Result Content */}
                  <div className="results-content">
                    {result.results?.raw_result || "⚠️ 無辨識結果"}
                  </div>
                </>
              ) : (
                <div className="results-empty">
                  <div className="results-empty-icon">📝</div>
                  <div>上傳檔案後，辨識結果將顯示於此</div>
                </div>
              )}
            </div>
          </div>
        ) : (
          <BatchUpload
            mode={localStorage.getItem('ocr_mode') || 'hybrid'}
            onComplete={(results) => {
              console.log('批量處理完成:', results);
              // 可選：顯示通知
            }}
          />
        )}
      </main>
    </div>
  );
}
