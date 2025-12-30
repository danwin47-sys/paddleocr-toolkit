"use client";

import { useState, useEffect } from "react";
import { getApiUrl } from "@/utils/api";

interface TranslationModalProps {
    isOpen: boolean;
    onClose: () => void;
    originalText: string;
}

export default function TranslationModal({ isOpen, onClose, originalText }: TranslationModalProps) {
    const [targetLang, setTargetLang] = useState('en');
    const [provider, setProvider] = useState('ollama');
    const [translatedText, setTranslatedText] = useState('');
    const [isTranslating, setIsTranslating] = useState(false);
    const [error, setError] = useState('');
    const [debugLogs, setDebugLogs] = useState<string[]>([]);

    const addLog = (msg: string) => {
        setDebugLogs(prev => [...prev.slice(-4), `${new Date().toLocaleTimeString().split(' ')[0]} ${msg}`]);
    };

    const languages = [
        { value: 'en', label: 'English 🇬🇧', flag: '🇬🇧' },
        { value: 'zh-TW', label: '繁體中文 🇹🇼', flag: '🇹🇼' },
        { value: 'zh-CN', label: '简体中文 🇨🇳', flag: '🇨🇳' },
        { value: 'ja', label: '日本語 🇯🇵', flag: '🇯🇵' },
        { value: 'ko', label: '한국어 🇰🇷', flag: '🇰🇷' },
        { value: 'es', label: 'Español 🇪🇸', flag: '🇪🇸' },
        { value: 'fr', label: 'Français 🇫🇷', flag: '🇫🇷' },
        { value: 'de', label: 'Deutsch 🇩🇪', flag: '🇩🇪' }
    ];

    const providers = [
        { value: 'ollama', label: 'Ollama (本地免費)', icon: '🖥️' },
        { value: 'gemini', label: 'Gemini (Google AI)', icon: '🌟' },
        { value: 'claude', label: 'Claude (Anthropic)', icon: '🤖' }
    ];

    const handleTranslate = async () => {
        setIsTranslating(true);
        setError('');
        setTranslatedText('');
        setDebugLogs([]);
        addLog('準備翻譯請求...');

        try {
            const body: any = {
                text: originalText,
                target_lang: targetLang,
                provider: provider
            };

            addLog(`文字長度: ${originalText.length} 字元`);

            // 如果需要 API key，從 localStorage 獲取
            if (provider === 'gemini') {
                const apiKey = localStorage.getItem('gemini_api_key');
                if (apiKey) body.api_key = apiKey;
                addLog('已加載 Gemini API Key');
            } else if (provider === 'claude') {
                const apiKey = localStorage.getItem('claude_api_key');
                if (apiKey) body.api_key = apiKey;
                addLog('已加載 Claude API Key');
            }

            addLog(`正在向後端發送請求 (${provider})...`);

            const apiUrl = getApiUrl();
            const endpoint = apiUrl ? `${apiUrl}/api/translate` : '/api/translate';

            addLog(`正在向後端發送請求 (${provider})...`);

            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'ngrok-skip-browser-warning': 'true'
                },
                body: JSON.stringify(body)
            });

            addLog(`後端回應狀態: ${response.status} ${response.statusText}`);

            if (!response.ok) {
                const text = await response.text();
                addLog(`錯誤詳情: ${text.slice(0, 100)}...`);
                throw new Error(`伺服器錯誤: ${response.status}`);
            }

            addLog('正在解析回應數據...');
            const data = await response.json();

            if (data.status === 'success') {
                addLog('翻譯成功！');
                setTranslatedText(data.translated_text);
            } else {
                addLog(`翻譯失敗: ${data.message}`);
                setError(data.message || '翻譯失敗');
            }
        } catch (err: any) {
            addLog(`發生異常: ${err.message}`);
            setError('翻譯失敗: ' + err.message);
        } finally {
            setIsTranslating(false);
        }
    };

    const handleCopy = () => {
        navigator.clipboard.writeText(translatedText);
        alert('✅ 已複製翻譯結果');
    };

    if (!isOpen) return null;

    return (
        <div
            className="modal-backdrop"
            style={{
                position: 'fixed',
                top: 0,
                left: 0,
                right: 0,
                bottom: 0,
                background: 'rgba(0, 0, 0, 0.7)',
                backdropFilter: 'blur(4px)',
                zIndex: 9998,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                padding: '20px'
            }}
            onClick={onClose}
        >
            <div
                className="glass-card"
                style={{
                    width: '100%',
                    maxWidth: '600px',
                    maxHeight: '90vh',
                    padding: '30px',
                    position: 'relative',
                    zIndex: 9999,
                    overflowY: 'auto'
                }}
                onClick={(e) => e.stopPropagation()}
            >
                {/* Header */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                    <h2 style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>🌐 AI 翻譯</h2>
                    <button
                        onClick={onClose}
                        style={{
                            width: '32px',
                            height: '32px',
                            borderRadius: '50%',
                            background: 'rgba(255,255,255,0.1)',
                            border: 'none',
                            color: '#fff',
                            cursor: 'pointer',
                            fontSize: '18px'
                        }}
                    >
                        ✕
                    </button>
                </div>

                {/* 語言選擇 */}
                <div style={{ marginBottom: '20px' }}>
                    <label style={{ display: 'block', marginBottom: '8px', color: '#cbd5e1', fontSize: '14px' }}>
                        目標語言
                    </label>
                    <select
                        value={targetLang}
                        onChange={(e) => setTargetLang(e.target.value)}
                        style={{
                            width: '100%',
                            padding: '12px',
                            borderRadius: '8px',
                            background: 'rgba(0,0,0,0.3)',
                            border: '1px solid rgba(255,255,255,0.1)',
                            color: '#fff',
                            fontSize: '14px'
                        }}
                    >
                        {languages.map(lang => (
                            <option key={lang.value} value={lang.value}>
                                {lang.label}
                            </option>
                        ))}
                    </select>
                </div>

                {/* AI 提供商選擇 */}
                <div style={{ marginBottom: '20px' }}>
                    <label style={{ display: 'block', marginBottom: '8px', color: '#cbd5e1', fontSize: '14px' }}>
                        AI 提供商
                    </label>
                    <select
                        value={provider}
                        onChange={(e) => setProvider(e.target.value)}
                        style={{
                            width: '100%',
                            padding: '12px',
                            borderRadius: '8px',
                            background: 'rgba(0,0,0,0.3)',
                            border: '1px solid rgba(255,255,255,0.1)',
                            color: '#fff',
                            fontSize: '14px'
                        }}
                    >
                        {providers.map(prov => (
                            <option key={prov.value} value={prov.value}>
                                {prov.icon} {prov.label}
                            </option>
                        ))}
                    </select>

                    {provider !== 'ollama' && (
                        <p style={{ marginTop: '8px', fontSize: '12px', color: '#fbbf24' }}>
                            ⚠️ 需要在設定中配置 API Key
                        </p>
                    )}
                </div>

                {/* 翻譯按鈕 */}
                <button
                    onClick={handleTranslate}
                    disabled={isTranslating}
                    className="action-btn"
                    style={{
                        width: '100%',
                        padding: '14px',
                        marginBottom: '10px',
                        opacity: isTranslating ? 0.6 : 1,
                        cursor: isTranslating ? 'wait' : 'pointer'
                    }}
                >
                    {isTranslating ? '🔄 翻譯中...' : '🚀 開始翻譯'}
                </button>

                {/* Debug Logs */}
                {debugLogs.length > 0 && (
                    <div style={{
                        padding: '10px',
                        marginBottom: '20px',
                        borderRadius: '8px',
                        background: 'rgba(0,0,0,0.4)',
                        border: '1px solid rgba(255,255,255,0.05)',
                        fontSize: '11px',
                        fontFamily: 'monospace',
                        color: '#94a3b8'
                    }}>
                        {debugLogs.map((log, i) => (
                            <div key={i} style={{ marginBottom: '2px', color: log.includes('失敗') || log.includes('異常') ? '#fca5a5' : '#94a3b8' }}>
                                {'>'} {log}
                            </div>
                        ))}
                        {isTranslating && <div className="loading-dots" style={{ marginTop: '5px' }}>處理中...</div>}
                    </div>
                )}

                {/* 錯誤訊息 */}
                {error && (
                    <div style={{
                        padding: '12px',
                        marginBottom: '20px',
                        borderRadius: '8px',
                        background: 'rgba(239, 68, 68, 0.1)',
                        border: '1px solid rgba(239, 68, 68, 0.3)',
                        color: '#fca5a5'
                    }}>
                        ❌ {error}
                    </div>
                )}

                {/* 翻譯結果 */}
                {translatedText && (
                    <div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                            <label style={{ color: '#cbd5e1', fontSize: '14px' }}>翻譯結果</label>
                            <button
                                onClick={handleCopy}
                                style={{
                                    padding: '6px 12px',
                                    borderRadius: '6px',
                                    background: 'rgba(16, 185, 129, 0.2)',
                                    border: '1px solid rgba(16, 185, 129, 0.3)',
                                    color: '#10b981',
                                    cursor: 'pointer',
                                    fontSize: '12px'
                                }}
                            >
                                📋 複製
                            </button>
                        </div>
                        <div style={{
                            padding: '16px',
                            borderRadius: '8px',
                            background: 'rgba(0,0,0,0.3)',
                            border: '1px solid rgba(255,255,255,0.1)',
                            color: '#fff',
                            whiteSpace: 'pre-wrap',
                            lineHeight: '1.6',
                            maxHeight: '300px',
                            overflowY: 'auto'
                        }}>
                            {translatedText}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
