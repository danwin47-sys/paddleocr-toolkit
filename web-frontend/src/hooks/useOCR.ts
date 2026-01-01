import { useState, useCallback } from 'react';
import { getApiUrl } from '@/utils/api';
import { OCRCache } from '@/utils/ocr-cache';

export interface OCRResult {
    task_id: string;
    status: string;
    progress: number;
    results?: {
        raw_result: string;
        page_results: string[];
        pages: number;
        confidence: number;
    };
    error?: string;
}

export interface UseOCRReturn {
    uploadFile: (file: File, mode: string, geminiKey?: string, claudeKey?: string) => Promise<void>;
    isProcessing: boolean;
    progress: number;
    statusText: string;
    result: OCRResult | null;
    error: string | null;
    reset: () => void;
}

export function useOCR(): UseOCRReturn {
    const [isProcessing, setIsProcessing] = useState(false);
    const [progress, setProgress] = useState(0);
    const [statusText, setStatusText] = useState('準備就緒');
    const [result, setResult] = useState<OCRResult | null>(null);
    const [error, setError] = useState<string | null>(null);

    const reset = useCallback(() => {
        setIsProcessing(false);
        setProgress(0);
        setStatusText('準備就緒');
        setResult(null);
        setError(null);
    }, []);

    const pollTaskStatus = async (taskId: string): Promise<OCRResult> => {
        return new Promise((resolve, reject) => {
            let pollInterval = 1000; // Initial 1 second
            const MAX_INTERVAL = 5000; // Max 5 seconds
            const BACKOFF_MULTIPLIER = 1.2; // Increase by 20% each time

            const poll = async () => {
                try {
                    const apiUrl = getApiUrl();
                    const endpoint = apiUrl ? `${apiUrl}/api/tasks/${taskId}` : `/api/tasks/${taskId}`;

                    const res = await fetch(endpoint, {
                        headers: {
                            'ngrok-skip-browser-warning': 'true'
                        }
                    });
                    if (!res.ok) throw new Error('無法獲取任務狀態');

                    const data: OCRResult = await res.json();

                    // Update progress display
                    if (data.progress) {
                        setProgress(data.progress);
                        if (data.progress < 30) setStatusText('檔案處理中...');
                        else if (data.progress < 80) setStatusText('OCR 辨識運算中...');
                        else setStatusText('AI 校正與後處理...');
                    }

                    if (data.status === 'completed') {
                        resolve(data);
                    } else if (data.status === 'failed') {
                        reject(new Error(data.error || '任務失敗'));
                    } else {
                        // Task still processing, gradually increase polling interval
                        pollInterval = Math.min(pollInterval * BACKOFF_MULTIPLIER, MAX_INTERVAL);
                        console.log(`⏱️ Next poll in: ${Math.round(pollInterval)}ms`);
                        setTimeout(poll, pollInterval);
                    }
                } catch (err) {
                    reject(err);
                }
            };

            // Start first poll
            poll();
        });
    };

    const uploadFile = useCallback(async (file: File, mode: string, geminiKey?: string, claudeKey?: string) => {
        // Generate file fingerprint for caching
        const fileFingerprint = `${file.name}_${file.size}_${file.lastModified}_${mode}`;

        // 1. Check cache first
        const cachedResult = OCRCache.get(fileFingerprint);
        if (cachedResult) {
            console.log('✅ Using cached result');
            setResult(cachedResult.result);
            setProgress(100);
            setStatusText('從快取載入');

            // Briefly show then restore
            setTimeout(() => {
                setStatusText('處理完成（快取）');
            }, 500);
            return;
        }

        setIsProcessing(true);
        setError(null);
        setResult(null);
        setProgress(0);
        setStatusText('正在上傳...');

        try {
            const formData = new FormData();
            formData.append('file', file);

            const params = new URLSearchParams();
            params.append('mode', mode);
            if (geminiKey) params.append('gemini_key', geminiKey);
            if (claudeKey) params.append('claude_key', claudeKey);

            const apiUrl = getApiUrl();
            const endpoint = apiUrl ? `${apiUrl}/api/ocr?${params.toString()}` : `/api/ocr?${params.toString()}`;

            const res = await fetch(endpoint, {
                method: 'POST',
                body: formData,
                headers: {
                    'ngrok-skip-browser-warning': 'true'
                }
            });

            if (!res.ok) {
                throw new Error(`上傳失敗: ${res.statusText}`);
            }

            const data = await res.json();
            const taskId = data.task_id;

            setStatusText('等待處理...');
            const finalResult = await pollTaskStatus(taskId);

            setResult(finalResult);
            setStatusText('處理完成');
            setProgress(100);

            // 2. Save to cache
            OCRCache.set(fileFingerprint, file.name, mode, finalResult);
            console.log('💾 Result cached');

        } catch (err: any) {
            setError(err.message || '發生未知錯誤');
            setStatusText('發生錯誤');
        } finally {
            setIsProcessing(false);
        }
    }, []);

    return {
        uploadFile,
        isProcessing,
        progress,
        statusText,
        result,
        error,
        reset
    };
}
