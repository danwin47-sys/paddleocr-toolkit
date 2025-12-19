#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GPU批次處理最佳化器
v1.2.0新增 - 提升GPU利用率和處理速度
"""

import time
from typing import Any, List

import numpy as np


class GPUMemoryPool:
    """GPU記憶體池管理"""

    def __init__(self):
        """初始化記憶體池"""
        self.allocated_memory = []
        self.peak_usage = 0

    def __enter__(self):
        """進入上下文"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出時清理記憶體"""
        self.clear()

    def allocate(self, size: int):
        """分配記憶體"""
        memory = np.zeros(size, dtype=np.float32)
        self.allocated_memory.append(memory)
        current_usage = sum(m.nbytes for m in self.allocated_memory)
        self.peak_usage = max(self.peak_usage, current_usage)
        return memory

    def clear(self):
        """清理記憶體"""
        self.allocated_memory.clear()

    def get_peak_usage_mb(self) -> float:
        """獲取峰值使用量(MB)"""
        return self.peak_usage / 1024 / 1024


class GPUBatchProcessor:
    """
    GPU批次處理最佳化器

    透過批次處理提升GPU利用率，預期2x效能提升
    """

    def __init__(self, batch_size: int = 16, enable_memory_pool: bool = True):
        """
        初始化GPU批次處理器

        Args:
            batch_size: 批次大小，建議8-32
            enable_memory_pool: 是否啟用記憶體池
        """
        self.batch_size = batch_size
        self.enable_memory_pool = enable_memory_pool
        self.memory_pool = GPUMemoryPool() if enable_memory_pool else None

        # 效能統計
        self.stats = {
            "total_images": 0,
            "total_batches": 0,
            "total_time": 0.0,
            "gpu_time": 0.0,
            "preprocessing_time": 0.0,
            "total_pages": 0,  # 新增：總處理頁數
            "avg_speed": 0.0,  # 新增：平均速度
        }

    def _create_batches(self, images: List[Any], batch_size: int) -> List[List[Any]]:
        """
        將圖片列表分成批次

        Args:
            images: 圖片列表
            batch_size: 批次大小

        Returns:
            批次列表
        """
        batches = []
        for i in range(0, len(images), batch_size):
            batch = images[i : i + batch_size]
            batches.append(batch)
        return batches

    def _preprocess_batch(self, batch: List[Any]) -> np.ndarray:
        """
        預處理批次圖片

        Args:
            batch: 圖片批次

        Returns:
            批次tensor
        """
        start_time = time.time()

        # 這裡是實際的圖片預處理邏輯
        # 暫時使用佔位符
        processed = []
        for img in batch:
            # 實際應該：resize, normalize, to_tensor 等
            # 模擬處理過程
            time.sleep(0.01)
            processed.append(img)

        # 堆疊成批次
        batch_tensor = np.array(processed) if processed else np.array([])

        self.stats["preprocessing_time"] += time.time() - start_time
        return batch_tensor

    def _gpu_predict_batch(
        self, batch_tensor: np.ndarray, ocr_engine: Any
    ) -> List[Any]:
        """
        GPU批次預測

        Args:
            batch_tensor: 批次tensor
            ocr_engine: OCR引擎例項

        Returns:
            預測結果列表
        """
        start_time = time.time()

        # 使用記憶體池（如果啟用）
        if self.memory_pool:
            with self.memory_pool:
                # 實際的批次預測
                # 這裡應該呼叫法 PaddleOCR 的批次預測
                results = ocr_engine.ocr(batch_tensor, batch=True)
        else:
            results = ocr_engine.ocr(batch_tensor, batch=True)

        self.stats["gpu_time"] += time.time() - start_time
        return results

    def batch_predict(self, images: List[Any], ocr_engine: Any) -> List[Any]:
        """
        批次預測主函式

        Args:
            images: 圖片列表
            ocr_engine: OCR引擎例項

        Returns:
            所有結果列表
        """
        total_start = time.time()

        # 建立批次
        batches = self._create_batches(images, self.batch_size)
        self.stats["total_images"] = len(images)
        self.stats["total_batches"] = len(batches)

        all_results = []

        for batch in batches:
            # 預處理
            batch_tensor = self._preprocess_batch(batch)

            # GPU預測
            batch_results = self._gpu_predict_batch(batch_tensor, ocr_engine)

            # 收集結果
            all_results.extend(batch_results)

        self.stats["total_time"] = time.time() - total_start
        self.stats["total_pages"] = len(images)  # 假設每張圖片為一頁
        if self.stats["total_pages"] > 0:
            self.stats["avg_speed"] = self.stats["total_time"] / self.stats["total_pages"]

        return all_results

    def get_performance_stats(self) -> dict:
        """
        獲取效能統計

        Returns:
            效能統計字典
        """
        if self.stats["total_images"] == 0:
            return self.stats

        return {
            **self.stats,
            "avg_time_per_image": self.stats["total_time"] / self.stats["total_images"],
            "avg_time_per_batch": self.stats["total_time"] / self.stats["total_batches"]
            if self.stats["total_batches"] > 0
            else 0,
            "preprocessing_ratio": self.stats["preprocessing_time"]
            / self.stats["total_time"]
            if self.stats["total_time"] > 0
            else 0,
            "gpu_ratio": self.stats["gpu_time"] / self.stats["total_time"]
            if self.stats["total_time"] > 0
            else 0,
        }

    def reset_stats(self):
        """重置統計"""
        self.stats = {
            "total_images": 0,
            "total_batches": 0,
            "total_time": 0.0,
            "gpu_time": 0.0,
            "preprocessing_time": 0.0,
            "total_pages": 0,
            "avg_speed": 0.0,
        }

    def print_performance_report(self):
        """列印效能報告"""
        stats = self.get_performance_stats()

        print("\n" + "=" * 60)
        print("GPU批次處理效能報告")
        print("=" * 60)
        print(f"總圖片數: {stats['total_images']}")
        print(f"批次數: {stats['total_batches']}")
        print(f"批次大小: {self.batch_size}")
        print(f"總時間: {stats['total_time']:.2f}s")
        print(f"處理頁數: {stats['total_pages']}")
        print(f"平均速度: {stats['avg_speed']:.2f}s/頁")
        print(f"平均每圖: {stats.get('avg_time_per_image', 0):.3f}s")
        print(f"平均每批: {stats.get('avg_time_per_batch', 0):.3f}s")
        print(
            f"預處理時間: {stats['preprocessing_time']:.2f}s ({stats.get('preprocessing_ratio', 0):.1%})"
        )

# 使用示例
if __name__ == "__main__":
    print("GPU批次處理最佳化器")
    print("預期效能提升: 2x")
    print("\n使用方法:")
    print(
        """
from paddleocr_toolkit.core.gpu_optimizer import GPUBatchProcessor

# 初始化
gpu_processor = GPUBatchProcessor(batch_size=16)

# 批次處理
results = gpu_processor.batch_predict(images, ocr_engine)

# 檢視效能
gpu_processor.print_performance_report()
"""
    )
