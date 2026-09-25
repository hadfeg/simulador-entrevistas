from copy import deepcopy
from datetime import date
import math


PRICING_DATE = "2026-09-24"

TEXT_PRICING_USD_PER_MILLION = {
    "gpt-5.6-luna": {
        "input": 0.20,
        "cached_input": 0.02,
        "cache_write": 0.25,
        "output": 1.20,
    },
    "gpt-5.6-terra": {
        "input": 2.00,
        "cached_input": 0.20,
        "cache_write": 2.50,
        "output": 12.00,
    },
    "gpt-5.6-sol": {
        "input": 4.00,
        "cached_input": 0.40,
        "cache_write": 5.00,
        "output": 20.00,
    },
    "gpt-5.6": {
        "input": 4.00,
        "cached_input": 0.40,
        "cache_write": 5.00,
        "output": 20.00,
    },
}

TRANSCRIPTION_USD_PER_MINUTE = {
    "gpt-transcribe": 0.0045,
    "gpt-4o-mini-transcribe": 0.0030,
    "gpt-4o-transcribe": 0.0060,
}

TTS_PRICING = {
    "gpt-4o-mini-tts": {
        "text_input_per_million": 0.60,
        "audio_output_per_million": 12.00,
    }
}

REALTIME_PRICING_USD_PER_MILLION = {
    "gpt-realtime-2.1": {
        "text_input": 4.00,
        "text_cached_input": 0.40,
        "text_output": 24.00,
        "audio_input": 32.00,
        "audio_cached_input": 0.40,
        "audio_output": 64.00,
    },
    "gpt-realtime-2.1-mini": {
        "text_input": 0.60,
        "text_cached_input": 0.06,
        "text_output": 2.40,
        "audio_input": 10.00,
        "audio_cached_input": 0.30,
        "audio_output": 20.00,
    },
}

LIVE_TRANSCRIPTION_USD_PER_MINUTE = {
    "gpt-live-transcribe": 0.017,
}


def new_usage() -> dict:
    return {
        "pricing_date": PRICING_DATE,
        "text": {
            "interviewer": _empty_text_component(),
            "evaluator": _empty_text_component(),
        },
        "realtime": {
            "model": None,
            "responses": 0,
            "input_text_tokens": 0,
            "input_audio_tokens": 0,
            "cached_text_tokens": 0,
            "cached_audio_tokens": 0,
            "output_text_tokens": 0,
            "output_audio_tokens": 0,
            "estimated_cost_usd": 0.0,
        },
        "live_transcription": {
            "model": None,
            "calls": 0,
            "audio_tokens": 0,
            "estimated_seconds": 0.0,
            "estimated_cost_usd": 0.0,
        },
        "audio": {
            "transcription": {
                "model": None,
                "seconds": 0.0,
                "estimated_cost_usd": 0.0,
            },
            "tts": {
                "model": None,
                "calls": 0,
                "estimated_text_input_tokens": 0,
                "estimated_audio_output_tokens": 0,
                "estimated_audio_seconds": 0.0,
                "estimated_cost_usd": 0.0,
            },
        },
        "summary": {},
    }


def _empty_text_component() -> dict:
    return {
        "model": None,
        "calls": 0,
        "input_tokens": 0,
        "cached_input_tokens": 0,
        "cache_write_tokens": 0,
        "output_tokens": 0,
        "total_tokens": 0,
        "estimated_cost_usd": 0.0,
    }


def response_usage(response, model: str) -> dict:
    usage = getattr(response, "usage", None)
    result = _empty_text_component()
    result["model"] = model

    if usage is None:
        return result

    details = getattr(usage, "input_tokens_details", None)

    result["calls"] = 1
    result["input_tokens"] = int(getattr(usage, "input_tokens", 0) or 0)
    result["cached_input_tokens"] = int(
        getattr(details, "cached_tokens", 0) or 0
    )
    result["cache_write_tokens"] = int(
        getattr(details, "cache_write_tokens", 0) or 0
    )
    result["output_tokens"] = int(getattr(usage, "output_tokens", 0) or 0)
    result["total_tokens"] = int(getattr(usage, "total_tokens", 0) or 0)
    result["estimated_cost_usd"] = estimate_text_cost(result)
    return result


def estimate_text_cost(component: dict) -> float:
    model = component.get("model")
    prices = TEXT_PRICING_USD_PER_MILLION.get(model)
    if not prices:
        return 0.0

    input_tokens = component.get("input_tokens", 0)
    cached_tokens = component.get("cached_input_tokens", 0)
    cache_write_tokens = component.get("cache_write_tokens", 0)
    ordinary_tokens = max(
        0,
        input_tokens - cached_tokens - cache_write_tokens,
    )

    cost = (
        ordinary_tokens * prices["input"]
        + cached_tokens * prices["cached_input"]
        + cache_write_tokens * prices["cache_write"]
        + component.get("output_tokens", 0) * prices["output"]
    ) / 1_000_000

    return round(cost, 8)


def add_text_usage(total: dict, component_name: str, call_usage: dict):
    component = total["text"][component_name]
    component["model"] = call_usage.get("model") or component["model"]

    for key in [
        "calls",
        "input_tokens",
        "cached_input_tokens",
        "cache_write_tokens",
        "output_tokens",
        "total_tokens",
    ]:
        component[key] += int(call_usage.get(key, 0) or 0)

    component["estimated_cost_usd"] = estimate_text_cost(component)
    refresh_summary(total)


def add_transcription_usage(total: dict, model: str, seconds: float):
    seconds = max(0.0, float(seconds or 0))
    component = total["audio"]["transcription"]
    component["model"] = model
    component["seconds"] = round(component["seconds"] + seconds, 3)

    price_per_minute = TRANSCRIPTION_USD_PER_MINUTE.get(model, 0.0)
    component["estimated_cost_usd"] = round(
        component["seconds"] / 60 * price_per_minute,
        8,
    )
    refresh_summary(total)


def estimate_tts_usage(text: str, model: str) -> dict:
    words = len(text.split())
    estimated_seconds = max(0.4, words / 2.5) if words else 0.0

    # Aproximaciones: ~4 caracteres por token de texto y
    # ~1 token de audio por 50 ms de salida hablada.
    estimated_text_tokens = math.ceil(len(text) / 4) if text else 0
    estimated_audio_tokens = math.ceil(estimated_seconds / 0.05)

    prices = TTS_PRICING.get(model, {})
    cost = (
        estimated_text_tokens
        * prices.get("text_input_per_million", 0.0)
        + estimated_audio_tokens
        * prices.get("audio_output_per_million", 0.0)
    ) / 1_000_000

    return {
        "model": model,
        "calls": 1,
        "estimated_text_input_tokens": estimated_text_tokens,
        "estimated_audio_output_tokens": estimated_audio_tokens,
        "estimated_audio_seconds": round(estimated_seconds, 3),
        "estimated_cost_usd": round(cost, 8),
    }


def add_tts_usage(total: dict, call_usage: dict):
    component = total["audio"]["tts"]
    component["model"] = call_usage.get("model") or component["model"]
    component["calls"] += int(call_usage.get("calls", 0) or 0)
    component["estimated_text_input_tokens"] += int(
        call_usage.get("estimated_text_input_tokens", 0) or 0
    )
    component["estimated_audio_output_tokens"] += int(
        call_usage.get("estimated_audio_output_tokens", 0) or 0
    )
    component["estimated_audio_seconds"] = round(
        component["estimated_audio_seconds"]
        + float(call_usage.get("estimated_audio_seconds", 0) or 0),
        3,
    )
    component["estimated_cost_usd"] = round(
        component["estimated_cost_usd"]
        + float(call_usage.get("estimated_cost_usd", 0) or 0),
        8,
    )
    refresh_summary(total)


def add_realtime_usage(total: dict, model: str, usage: dict):
    component = total["realtime"]
    component["model"] = model
    component["responses"] += 1

    input_details = usage.get("input_token_details", {}) or {}
    cached_details = input_details.get("cached_tokens_details", {}) or {}
    output_details = usage.get("output_token_details", {}) or {}

    component["input_text_tokens"] += int(
        input_details.get("text_tokens", 0) or 0
    )
    component["input_audio_tokens"] += int(
        input_details.get("audio_tokens", 0) or 0
    )
    component["cached_text_tokens"] += int(
        cached_details.get("text_tokens", 0) or 0
    )
    component["cached_audio_tokens"] += int(
        cached_details.get("audio_tokens", 0) or 0
    )
    component["output_text_tokens"] += int(
        output_details.get("text_tokens", 0) or 0
    )
    component["output_audio_tokens"] += int(
        output_details.get("audio_tokens", 0) or 0
    )

    prices = REALTIME_PRICING_USD_PER_MILLION.get(model)
    if prices:
        ordinary_text = max(
            0,
            component["input_text_tokens"] - component["cached_text_tokens"],
        )
        ordinary_audio = max(
            0,
            component["input_audio_tokens"] - component["cached_audio_tokens"],
        )
        cost = (
            ordinary_text * prices["text_input"]
            + component["cached_text_tokens"] * prices["text_cached_input"]
            + ordinary_audio * prices["audio_input"]
            + component["cached_audio_tokens"] * prices["audio_cached_input"]
            + component["output_text_tokens"] * prices["text_output"]
            + component["output_audio_tokens"] * prices["audio_output"]
        ) / 1_000_000
        component["estimated_cost_usd"] = round(cost, 8)

    refresh_summary(total)


def add_live_transcription_usage(
    total: dict,
    model: str,
    usage: dict | None,
):
    component = total["live_transcription"]
    component["model"] = model
    component["calls"] += 1

    usage = usage or {}
    input_details = usage.get("input_token_details", {}) or {}
    audio_tokens = int(input_details.get("audio_tokens", 0) or 0)
    component["audio_tokens"] += audio_tokens

    # Realtime user audio is approximately one token per 100 ms.
    estimated_seconds = audio_tokens * 0.1
    component["estimated_seconds"] = round(
        component["estimated_seconds"] + estimated_seconds,
        3,
    )

    price = LIVE_TRANSCRIPTION_USD_PER_MINUTE.get(model, 0.0)
    component["estimated_cost_usd"] = round(
        component["estimated_seconds"] / 60 * price,
        8,
    )
    refresh_summary(total)


def refresh_summary(total: dict):
    interviewer = total["text"]["interviewer"]
    evaluator = total["text"]["evaluator"]
    transcription = total["audio"]["transcription"]
    tts = total["audio"]["tts"]
    realtime = total["realtime"]
    live_transcription = total["live_transcription"]

    realtime_text_tokens = (
        realtime["input_text_tokens"]
        + realtime["output_text_tokens"]
    )
    text_tokens = (
        interviewer["total_tokens"]
        + evaluator["total_tokens"]
        + realtime_text_tokens
    )

    total_cost = (
        interviewer["estimated_cost_usd"]
        + evaluator["estimated_cost_usd"]
        + transcription["estimated_cost_usd"]
        + tts["estimated_cost_usd"]
        + realtime["estimated_cost_usd"]
        + live_transcription["estimated_cost_usd"]
    )

    total["summary"] = {
        "text_tokens": text_tokens,
        "text_input_tokens": (
            interviewer["input_tokens"]
            + evaluator["input_tokens"]
            + realtime["input_text_tokens"]
        ),
        "text_output_tokens": (
            interviewer["output_tokens"]
            + evaluator["output_tokens"]
            + realtime["output_text_tokens"]
        ),
        "cached_input_tokens": (
            interviewer["cached_input_tokens"]
            + evaluator["cached_input_tokens"]
            + realtime["cached_text_tokens"]
            + realtime["cached_audio_tokens"]
        ),
        "realtime_audio_input_tokens": realtime["input_audio_tokens"],
        "realtime_audio_output_tokens": realtime["output_audio_tokens"],
        "voice_input_seconds": (
            transcription["seconds"]
            + live_transcription["estimated_seconds"]
        ),
        "estimated_tts_seconds": tts["estimated_audio_seconds"],
        "estimated_cost_usd": round(total_cost, 8),
        "currency": "USD",
        "is_estimate": True,
    }


def finalized_usage(total: dict) -> dict:
    refresh_summary(total)
    return deepcopy(total)
