import { useState, useCallback } from 'react';

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
            const timer = setInterval(async () => {
                try {
                    const res = await fetch(`/api/tasks/${taskId}`, {
                        headers: {
                            'ngrok-skip-browser-warning': 'true'
                        }
                    });
                    if (!res.ok) throw new Error('無法獲取任務狀態');

                    const data: OCRResult = await res.json();

                    // 更新進度顯示 (若後端有回傳 progress)
                    if (data.progress) {
                        setProgress(data.progress);
                        if (data.progress < 30) setStatusText('檔案處理中...');
                        else if (data.progress < 80) setStatusText('OCR 辨識運算中...');
                        else setStatusText('AI 校正與後處理...');
                    }

                    if (data.status === 'completed') {
                        clearInterval(timer);
                        resolve(data);
                    } else if (data.status === 'failed') {
                        clearInterval(timer);
                        reject(new Error(data.error || '任務失敗'));
                    }
                } catch (err) {
                    clearInterval(timer);
                    reject(err);
                }
            }, 1000);
        });
    };

    const uploadFile = useCallback(async (file: File, mode: string, geminiKey?: string, claudeKey?: string) => {
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

            const res = await fetch(`/api/ocr?${params.toString()}`, {
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
