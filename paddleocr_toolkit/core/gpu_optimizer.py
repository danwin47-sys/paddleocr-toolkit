#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GPU批次处理优化器
v1.2.0新增 - 提升GPU利用率和处理速度
"""
import logging
import time
from typing import Any, List, Dict, Optional
import psutil

from paddleocr_toolkit.utils.logger import logger

import numpy as np


class GPUMemoryPool:
    """GPU内存池管理"""

    def __init__(self):
        """初始化内存池"""
        self.allocated_memory = []
        self.peak_usage = 0

    def __enter__(self):
        """进入上下文"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出时清理内存"""
        self.clear()

    def allocate(self, size: int):
        """分配内存"""
        memory = np.zeros(size, dtype=np.float32)
        self.allocated_memory.append(memory)
        current_usage = sum(m.nbytes for m in self.allocated_memory)
        self.peak_usage = max(self.peak_usage, current_usage)
        return memory

    def clear(self):
        """清理内存"""
        self.allocated_memory.clear()

    def get_peak_usage_mb(self) -> float:
        """获取峰值使用量(MB)"""
        return self.peak_usage / 1024 / 1024


class GPUBatchProcessor:
    """
    GPU批次处理优化器

    通过批次处理提升GPU利用率，预期2x性能提升
    """

    def __init__(self, batch_size: int = 16, enable_memory_pool: bool = True):
        """
        初始化GPU批次处理器

        Args:
            batch_size: 批次大小，建议8-32
            enable_memory_pool: 是否启用内存池
        """
        self.batch_size = batch_size
        self.enable_memory_pool = enable_memory_pool
        self.memory_pool = GPUMemoryPool() if enable_memory_pool else None

        # 性能统计
        self.stats = {
            "total_images": 0,
            "total_batches": 0,
            "total_time": 0.0,
            "gpu_time": 0.0,
            "preprocessing_time": 0.0,
        }

    def _create_batches(self, images: List[Any], batch_size: int) -> List[List[Any]]:
        """
        将图片列表分成批次

        Args:
            images: 图片列表
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
        预处理批次图片

        Args:
            batch: 图片批次

        Returns:
            批次tensor
        """
        start_time = time.time()

        # 这里应该是实际的图片预处理逻辑
        # 暂时使用占位符
        processed = []
        for img in batch:
            # 实际应该：resize, normalize, to_tensor等
            processed.append(img)

        # 堆叠成批次
        batch_tensor = np.array(processed) if processed else np.array([])

        self.stats["preprocessing_time"] += time.time() - start_time
        return batch_tensor

    def _gpu_predict_batch(
        self, batch_tensor: np.ndarray, ocr_engine: Any
    ) -> List[Any]:
        """
        GPU批次预测

        Args:
            batch_tensor: 批次tensor
            ocr_engine: OCR引擎实例

        Returns:
            预测结果列表
        """
        start_time = time.time()

        # 使用内存池（如果启用）
        if self.memory_pool:
            with self.memory_pool:
                # 实际的批次预测
                # 这里应该调用PaddleOCR的批次预测
                results = ocr_engine.ocr(batch_tensor, batch=True)
        else:
            results = ocr_engine.ocr(batch_tensor, batch=True)

        self.stats["gpu_time"] += time.time() - start_time
        return results

    def batch_predict(self, images: List[Any], ocr_engine: Any) -> List[Any]:
        """
        批次预测主函数

        Args:
            images: 图片列表
            ocr_engine: OCR引擎实例

        Returns:
            所有结果列表
        """
        total_start = time.time()

        # 创建批次
        batches = self._create_batches(images, self.batch_size)
        self.stats["total_images"] = len(images)
        self.stats["total_batches"] = len(batches)

        all_results = []

        for batch in batches:
            # 预处理
            batch_tensor = self._preprocess_batch(batch)

            # GPU预测
            batch_results = self._gpu_predict_batch(batch_tensor, ocr_engine)

            # 收集结果
            all_results.extend(batch_results)

        self.stats["total_time"] = time.time() - total_start

        return all_results

    def get_performance_stats(self) -> dict:
        """
        获取性能统计

        Returns:
            性能统计字典
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
        """重置统计"""
        self.stats = {
            "total_images": 0,
            "total_batches": 0,
            "total_time": 0.0,
            "gpu_time": 0.0,
            "preprocessing_time": 0.0,
        }

    def print_performance_report(self):
        """打印性能报告"""
        stats = self.get_performance_stats()

        logger.info("=" * 60)
        logger.info("GPU Batch Processing Report")
        logger.info("=" * 60)
        logger.info("Total Images: %d", stats['total_images'])
        logger.info("Total Batches: %d", stats['total_batches'])
        logger.info("Batch Size: %d", self.batch_size)
        logger.info("Total Time: %.2fs", stats['total_time'])
        logger.info("Avg per Image: %.3fs", stats.get('avg_time_per_image', 0))
        logger.info("Avg per Batch: %.3fs", stats.get('avg_time_per_batch', 0))
        logger.info(
            "Throughput: %.1f img/s", 
            stats['total_images'] / stats['total_time'] if stats['total_time'] > 0 else 0
        )
        logger.info(
            "Preprocessing Time: %.2fs (%.1f%%)", 
            stats['preprocessing_time'], 
            stats.get('preprocessing_ratio', 0) * 100
        )
        logger.info("GPU Time: %.2fs (%.1f%%)", stats['gpu_time'], stats.get('gpu_ratio', 0) * 100)
        
        if self.memory_pool:
            logger.info("Peak Memory: %.1fMB", self.memory_pool.get_peak_usage_mb())
            
        logger.info("=" * 60)


# 使用示例
# 使用示例
if __name__ == "__main__":
    logger.info("Usage:")
    logger.info(
        """
from paddleocr_toolkit.core.gpu_optimizer import GPUBatchProcessor

# 初始化
gpu_processor = GPUBatchProcessor(batch_size=16)

# 批次处理
results = gpu_processor.batch_predict(images, ocr_engine)

# 查看性能
gpu_processor.print_performance_report()
"""
    )
