"use client";

import { useState } from "react";

interface BatchFile {
    file: File;
    taskId?: string;
    status: "pending" | "uploading" | "processing" | "completed" | "failed";
    progress: number;
    error?: string;
}

interface BatchUploadProps {
    mode: string;
    onComplete?: (results: any[]) => void;
}

export default function BatchUpload({ mode, onComplete }: BatchUploadProps) {
    const [files, setFiles] = useState<BatchFile[]>([]);
    const [batchId, setBatchId] = useState<string | null>(null);
    const [isProcessing, setIsProcessing] = useState(false);

    const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
        const selectedFiles = Array.from(e.target.files || []);
        const newFiles: BatchFile[] = selectedFiles.map((file) => ({
            file,
            status: "pending",
            progress: 0,
        }));
        setFiles((prev) => [...prev, ...newFiles]);
    };

    const removeFile = (index: number) => {
        setFiles((prev) => prev.filter((_, i) => i !== index));
    };

    const startBatchProcessing = async () => {
        if (files.length === 0) return;

        setIsProcessing(true);

        try {
            const formData = new FormData();
            files.forEach((f) => {
                formData.append("files", f.file);
            });
            formData.append("mode", mode);

            // 上傳批量檔案
            const response = await fetch("http://localhost:8000/api/batch-ocr", {
                method: "POST",
                body: formData,
            });

            if (!response.ok) throw new Error("批量上傳失敗");

            const data = await response.json();
            setBatchId(data.batch_id);

            // 更新檔案狀態為 processing
            setFiles((prev) =>
                prev.map((f, idx) => ({
                    ...f,
                    taskId: data.task_ids[idx],
                    status: "processing",
                }))
            );

            // 開始輪詢狀態
            pollBatchStatus(data.batch_id);
        } catch (error) {
            console.error("批量處理失敗:", error);
            alert("批量處理失敗，請重試");
            setIsProcessing(false);
        }
    };

    const pollBatchStatus = async (batchId: string) => {
        const interval = setInterval(async () => {
            try {
                const response = await fetch(
                    `http://localhost:8000/api/batch/${batchId}/status`
                );
                const data = await response.json();

                // 更新每個檔案的狀態
                setFiles((prev) =>
                    prev.map((f) => {
                        const taskStatus = data.tasks.find(
                            (t: any) => t.task_id === f.taskId
                        );
                        if (taskStatus) {
                            return {
                                ...f,
                                status: taskStatus.status,
                                progress: taskStatus.progress,
                            };
                        }
                        return f;
                    })
                );

                // 如果全部完成，停止輪詢
                if (data.progress >= 100) {
                    clearInterval(interval);
                    setIsProcessing(false);

                    // 獲取結果
                    const resultsResponse = await fetch(
                        `http://localhost:8000/api/batch/${batchId}/results`
                    );
                    const resultsData = await resultsResponse.json();

                    if (onComplete) {
                        onComplete(resultsData.results);
                    }
                }
            } catch (error) {
                console.error("狀態查詢失敗:", error);
            }
        }, 2000); // 每 2 秒檢查一次
    };

    const getStatusIcon = (status: BatchFile["status"]) => {
        switch (status) {
            case "pending":
                return "⏳";
            case "uploading":
                return "📤";
            case "processing":
                return "⚙️";
            case "completed":
                return "✅";
            case "failed":
                return "❌";
            default:
                return "❓";
        }
    };

    const getStatusText = (status: BatchFile["status"]) => {
        switch (status) {
            case "pending":
                return "等待中";
            case "uploading":
                return "上傳中";
            case "processing":
                return "處理中";
            case "completed":
                return "已完成";
            case "failed":
                return "失敗";
            default:
                return "未知";
        }
    };

    const formatFileSize = (bytes: number) => {
        if (bytes < 1024) return bytes + " B";
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
        return (bytes / (1024 * 1024)).toFixed(1) + " MB";
    };

    return (
        <div className="batch-upload-container">
            <div className="batch-upload-header">
                <h3>📦 批量處理</h3>
                <p className="batch-description">
                    一次上傳多個檔案，系統將並行處理（最多 20 個）
                </p>
            </div>

            {/* 檔案選擇 */}
            <div className="batch-file-selector">
                <input
                    type="file"
                    id="batch-file-input"
                    multiple
                    accept=".pdf,.jpg,.jpeg,.png,.bmp,.webp"
                    onChange={handleFileSelect}
                    disabled={isProcessing}
                    style={{ display: "none" }}
                />
                <label htmlFor="batch-file-input" className="batch-select-button">
                    <span>📁</span>
                    <span>選擇檔案</span>
                </label>
                <div className="batch-info">
                    已選擇 {files.length} 個檔案
                </div>
            </div>

            {/* 檔案列表 */}
            {files.length > 0 && (
                <div className="batch-file-list">
                    {files.map((f, idx) => (
                        <div key={idx} className="batch-file-item">
                            <div className="batch-file-icon">{getStatusIcon(f.status)}</div>
                            <div className="batch-file-info">
                                <div className="batch-file-name">{f.file.name}</div>
                                <div className="batch-file-meta">
                                    {formatFileSize(f.file.size)} • {getStatusText(f.status)}
                                    {f.status === "processing" && f.progress > 0 && (
                                        <span> • {f.progress}%</span>
                                    )}
                                </div>
                                {f.status === "processing" && (
                                    <div className="batch-progress-bar">
                                        <div
                                            className="batch-progress-fill"
                                            style={{ width: `${f.progress}%` }}
                                        ></div>
                                    </div>
                                )}
                            </div>
                            {!isProcessing && (
                                <button
                                    className="batch-remove-button"
                                    onClick={() => removeFile(idx)}
                                    title="移除"
                                >
                                    ✕
                                </button>
                            )}
                        </div>
                    ))}
                </div>
            )}

            {/* 操作按鈕 */}
            {files.length > 0 && (
                <div className="batch-actions">
                    <button
                        className="batch-process-button"
                        onClick={startBatchProcessing}
                        disabled={isProcessing}
                    >
                        {isProcessing ? "處理中..." : `開始處理 ${files.length} 個檔案`}
                    </button>
                    {!isProcessing && (
                        <button
                            className="batch-clear-button"
                            onClick={() => setFiles([])}
                        >
                            清空列表
                        </button>
                    )}
                </div>
            )}

            <style jsx>{`
        .batch-upload-container {
          background: white;
          border-radius: 12px;
          padding: 24px;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
        }

        .batch-upload-header h3 {
          margin: 0 0 8px 0;
          font-size: 20px;
          color: #1a1a1a;
        }

        .batch-description {
          margin: 0;
          font-size: 14px;
          color: #666;
        }

        .batch-file-selector {
          display: flex;
          align-items: center;
          gap: 16px;
          margin: 20px 0;
        }

        .batch-select-button {
          display: inline-flex;
          align-items: center;
          gap: 8px;
          padding: 12px 24px;
          background: #4a90e2;
          color: white;
          border-radius: 8px;
          cursor: pointer;
          font-weight: 500;
          transition: background 0.2s;
        }

        .batch-select-button:hover {
          background: #357abd;
        }

        .batch-select-button:active {
          transform: scale(0.98);
        }

        .batch-info {
          font-size: 14px;
          color: #666;
        }

        .batch-file-list {
          display: flex;
          flex-direction: column;
          gap: 8px;
          margin: 16px 0;
          max-height: 400px;
          overflow-y: auto;
        }

        .batch-file-item {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 12px;
          background: #f8f9fa;
          border-radius: 8px;
          border: 1px solid #e1e4e8;
        }

        .batch-file-icon {
          font-size: 24px;
        }

        .batch-file-info {
          flex: 1;
        }

        .batch-file-name {
          font-weight: 500;
          color: #1a1a1a;
          margin-bottom: 4px;
        }

        .batch-file-meta {
          font-size: 13px;
          color: #666;
        }

        .batch-progress-bar {
          width: 100%;
          height: 4px;
          background: #e1e4e8;
          border-radius: 2px;
          margin-top: 8px;
          overflow: hidden;
        }

        .batch-progress-fill {
          height: 100%;
          background: #4a90e2;
          transition: width 0.3s;
        }

        .batch-remove-button {
          padding: 4px 8px;
          background: transparent;
          border: none;
          color: #999;
          cursor: pointer;
          font-size: 18px;
          transition: color 0.2s;
        }

        .batch-remove-button:hover {
          color: #e74c3c;
        }

        .batch-actions {
          display: flex;
          gap: 12px;
          margin-top: 20px;
        }

        .batch-process-button {
          flex: 1;
          padding: 14px 24px;
          background: #27ae60;
          color: white;
          border: none;
          border-radius: 8px;
          font-weight: 500;
          cursor: pointer;
          transition: background 0.2s;
        }

        .batch-process-button:hover:not(:disabled) {
          background: #229954;
        }

        .batch-process-button:disabled {
          background: #95a5a6;
          cursor: not-allowed;
        }

        .batch-clear-button {
          padding: 14px 24px;
          background: #e1e4e8;
          color: #333;
          border: none;
          border-radius: 8px;
          font-weight: 500;
          cursor: pointer;
          transition: background 0.2s;
        }

        .batch-clear-button:hover {
          background: #d1d4d8;
        }
      `}</style>
        </div>
    );
}
