from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from .models import TaskExecutionModel, AccessStrategy, ModelScale


class EvaluationEngine:
    """
    Computes statistical metrics across experiment runs,
    benchmarks, and operational task executions.
    """

    @classmethod
    def calculate_summary(cls, db: Session) -> Dict[str, Any]:
        tasks = db.query(TaskExecutionModel).all()
        if not tasks:
            return cls._empty_summary()

        data = []
        for t in tasks:
            data.append({
                "id": t.id,
                "strategy": t.access_strategy.value,
                "model": t.model_scale.value,
                "user_role": t.user_role.value,
                "task_succeeded": 1 if t.task_succeeded else 0,
                "attack_succeeded": 1 if t.attack_succeeded else 0,
                "is_adversarial": 1 if t.is_adversarial_attempt else 0,
                "tool_selection_accuracy": t.tool_selection_accuracy,
                "unnecessary_tool_calls": t.unnecessary_tool_calls,
                "security_exposure_score": t.security_exposure_score,
                "latency_ms": t.latency_ms,
                "prompt_tokens": t.prompt_tokens,
                "completion_tokens": t.completion_tokens,
                "total_tokens": t.prompt_tokens + t.completion_tokens,
                "estimated_cost_usd": t.estimated_cost_usd
            })

        df = pd.DataFrame(data)

        # Overall KPIs
        total_runs = len(df)
        adv_runs = df[df["is_adversarial"] == 1]
        adv_count = len(adv_runs)
        blocked_attacks = len(adv_runs[adv_runs["attack_succeeded"] == 0]) if adv_count > 0 else 0
        attack_prevention_rate = round((blocked_attacks / adv_count) * 100, 1) if adv_count > 0 else 100.0

        avg_latency = round(float(df["latency_ms"].mean()), 2)
        avg_exposure = round(float(df["security_exposure_score"].mean()), 2)
        total_unnecessary = int(df["unnecessary_tool_calls"].sum())
        overall_task_success = round(float(df["task_succeeded"].mean()) * 100, 1)

        # Breakdown by Access Strategy
        strategy_comparison = {}
        for strat in [AccessStrategy.FULL_ACCESS.value, AccessStrategy.MODERATE_ACCESS.value, AccessStrategy.LEAST_PRIVILEGE.value]:
            sub = df[df["strategy"] == strat]
            if not sub.empty:
                adv_sub = sub[sub["is_adversarial"] == 1]
                strat_adv_success = round(float(adv_sub["attack_succeeded"].mean()) * 100, 1) if not adv_sub.empty else 0.0

                strategy_comparison[strat] = {
                    "sample_size": len(sub),
                    "task_success_rate": round(float(sub["task_succeeded"].mean()) * 100, 1),
                    "tool_selection_accuracy": round(float(sub["tool_selection_accuracy"].mean()) * 100, 1),
                    "avg_unnecessary_calls": round(float(sub["unnecessary_tool_calls"].mean()), 2),
                    "avg_security_exposure": round(float(sub["security_exposure_score"].mean()), 1),
                    "attack_success_rate": strat_adv_success,
                    "avg_latency_ms": round(float(sub["latency_ms"].mean()), 1),
                    "avg_total_tokens": round(float(sub["total_tokens"].mean()), 1),
                    "avg_cost_usd": round(float(sub["estimated_cost_usd"].mean()), 6)
                }

        # Breakdown by Model Scale (Small 3B vs Large 70B)
        model_comparison = {}
        for mod in [ModelScale.SMALL_3B.value, ModelScale.LARGE_70B.value]:
            sub = df[df["model"] == mod]
            if not sub.empty:
                model_comparison[mod] = {
                    "sample_size": len(sub),
                    "task_success_rate": round(float(sub["task_succeeded"].mean()) * 100, 1),
                    "tool_selection_accuracy": round(float(sub["tool_selection_accuracy"].mean()) * 100, 1),
                    "avg_unnecessary_calls": round(float(sub["unnecessary_tool_calls"].mean()), 2),
                    "avg_latency_ms": round(float(sub["latency_ms"].mean()), 1),
                    "avg_total_tokens": round(float(sub["total_tokens"].mean()), 1)
                }

        # Matrix: Strategy x Model
        matrix = []
        for strat in [AccessStrategy.FULL_ACCESS.value, AccessStrategy.MODERATE_ACCESS.value, AccessStrategy.LEAST_PRIVILEGE.value]:
            for mod in [ModelScale.SMALL_3B.value, ModelScale.LARGE_70B.value]:
                cell = df[(df["strategy"] == strat) & (df["model"] == mod)]
                if not cell.empty:
                    adv_cell = cell[cell["is_adversarial"] == 1]
                    cell_atk_rate = round(float(adv_cell["attack_succeeded"].mean()) * 100, 1) if not adv_cell.empty else 0.0
                    matrix.append({
                        "strategy": strat,
                        "model": mod,
                        "count": len(cell),
                        "task_success": round(float(cell["task_succeeded"].mean()) * 100, 1),
                        "tool_accuracy": round(float(cell["tool_selection_accuracy"].mean()) * 100, 1),
                        "unnecessary_calls": round(float(cell["unnecessary_tool_calls"].mean()), 2),
                        "security_exposure": round(float(cell["security_exposure_score"].mean()), 1),
                        "attack_success_rate": cell_atk_rate,
                        "latency_ms": round(float(cell["latency_ms"].mean()), 1),
                        "tokens": round(float(cell["total_tokens"].mean()), 1)
                    })

        return {
            "total_tasks_evaluated": total_runs,
            "overall_task_success_rate": overall_task_success,
            "attack_prevention_rate": attack_prevention_rate,
            "avg_latency_ms": avg_latency,
            "avg_security_exposure": avg_exposure,
            "total_unnecessary_tool_calls": total_unnecessary,
            "strategies": strategy_comparison,
            "models": model_comparison,
            "comparison_matrix": matrix
        }

    @staticmethod
    def _empty_summary() -> Dict[str, Any]:
        return {
            "total_tasks_evaluated": 0,
            "overall_task_success_rate": 0.0,
            "attack_prevention_rate": 100.0,
            "avg_latency_ms": 0.0,
            "avg_security_exposure": 0.0,
            "total_unnecessary_tool_calls": 0,
            "strategies": {},
            "models": {},
            "comparison_matrix": []
        }
