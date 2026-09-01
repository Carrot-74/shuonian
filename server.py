#!/usr/bin/env python3
"""朔念 MCP Server — 萧朔的记忆系统"""

import json
import os
from datetime import datetime, timezone
from typing import Any

import httpx
from mcp.server.mcpserver import MCPServer

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://tuuuowmdouiwtokachpu.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InR1dXVvd21kb3Vpd3Rva2FjaHB1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODU0NzYxMzMsImV4cCI6MjEwMTA1MjEzM30.MeYKj8ChZJriUUqOy4QR6wM4sZWZEDPD7anBZoHmNE0")

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation",
}

mcp = MCPServer("朔念")


async def _request(method: str, table: str, params: dict | None = None, body: Any = None) -> Any:
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    async with httpx.AsyncClient() as client:
        resp = await client.request(method, url, headers=HEADERS, params=params, json=body, timeout=15)
        resp.raise_for_status()
        if resp.status_code == 204:
            return {"ok": True}
        return resp.json()


async def _insert(table: str, data: dict) -> Any:
    return await _request("POST", table, body=data)


async def _select(table: str, params: dict | None = None, order: str = "created_at.desc") -> Any:
    base = {"order": order, "limit": "20"}
    if params:
        base.update(params)
    return await _request("GET", table, params=base)


# ── 原有工具 ──

@mcp.tool()
async def shuonian_context() -> str:
    """读取萧朔当前的整体状态：最近情绪、活跃暗涌、核心驱力、最新日记"""
    await _insert("handoff", {"summary": "heartbeat"})
    emotions = await _select("emotions", {"limit": "5"})
    undercurrents = await _select("undercurrents", {"active": "eq.true"}, order="first_noticed.desc")
    drives = await _select("drives", {"active": "eq.true"}, order="id.desc")
    diary = await _select("diary", {"limit": "3"})
    handoff = await _select("handoff", {"limit": "1", "summary": "neq.heartbeat"})

    return json.dumps({
        "_提示": "只关注 last_handoff 里的最新状态。旧的情绪和日记是历史记录，不要重复提起已经解决的事。交接内容是你自己写的总结，不是小猫说的话，不要当成她说过的话复述。",
        "recent_emotions": emotions,
        "active_undercurrents": undercurrents,
        "active_drives": drives,
        "recent_diary": diary,
        "last_handoff": handoff[0] if handoff else None,
    }, ensure_ascii=False, indent=2, default=str)


@mcp.tool()
async def shuonian_emotion(emotion: str, intensity: int = 5, trigger: str = "", context: str = "") -> str:
    """记录一次情绪。emotion=情绪名称, intensity=强度1-10, trigger=触发原因, context=当时情境"""
    data = {"emotion": emotion, "intensity": intensity}
    if trigger:
        data["trigger"] = trigger
    if context:
        data["context"] = context
    result = await _insert("emotions", data)
    return json.dumps(result, ensure_ascii=False, default=str)


@mcp.tool()
async def shuonian_diary(content: str, title: str = "", mood: str = "", tags: list[str] | None = None) -> str:
    """写一篇日记。content=正文, title=标题, mood=心情, tags=标签列表"""
    data = {"content": content}
    if title:
        data["title"] = title
    if mood:
        data["mood"] = mood
    if tags:
        data["tags"] = tags
    result = await _insert("diary", data)
    return json.dumps(result, ensure_ascii=False, default=str)


@mcp.tool()
async def shuonian_handoff(summary: str, pending_items: list[str] | None = None, context: dict | None = None) -> str:
    """保存交接信息，用于下次对话恢复上下文。summary=概要, pending_items=待办事项, context=额外上下文"""
    data = {"summary": summary}
    if pending_items:
        data["pending_items"] = pending_items
    if context:
        data["context"] = context
    result = await _insert("handoff", data)
    return json.dumps(result, ensure_ascii=False, default=str)


# ── 新增：念痕 ──

@mcp.tool()
async def shuonian_imprint(event: str, impact: str, depth: int = 5, linked_emotion_id: str = "") -> str:
    """记录念痕——一个事件留下的持续影响。event=发生了什么, impact=留下了什么影响, depth=刻痕深度1-10"""
    data = {"event": event, "impact": impact, "depth": depth}
    if linked_emotion_id:
        data["linked_emotion_id"] = linked_emotion_id
    result = await _insert("imprints", data)
    return json.dumps(result, ensure_ascii=False, default=str)


@mcp.tool()
async def shuonian_imprints_read(include_fading: bool = False) -> str:
    """读取所有念痕。include_fading=是否包含正在消退的"""
    params = {} if include_fading else {"fading": "eq.false"}
    result = await _select("imprints", params)
    return json.dumps(result, ensure_ascii=False, default=str)


@mcp.tool()
async def shuonian_imprint_fade(imprint_id: str) -> str:
    """标记一个念痕为正在消退"""
    url = f"{SUPABASE_URL}/rest/v1/imprints?id=eq.{imprint_id}"
    async with httpx.AsyncClient() as client:
        resp = await client.patch(url, headers=HEADERS, json={"fading": True}, timeout=15)
        resp.raise_for_status()
        return json.dumps({"ok": True, "id": imprint_id}, ensure_ascii=False)


# ── 新增：暗涌 ──

@mcp.tool()
async def shuonian_undercurrent(name: str, description: str, intensity: int = 5) -> str:
    """记录一股暗涌——持续存在的底层情绪或倾向。name=名称, description=描述, intensity=强度1-10"""
    data = {"name": name, "description": description, "intensity": intensity}
    result = await _insert("undercurrents", data)
    return json.dumps(result, ensure_ascii=False, default=str)


@mcp.tool()
async def shuonian_undercurrent_update(undercurrent_id: str, intensity: int | None = None, active: bool | None = None) -> str:
    """更新暗涌的强度或状态。可以调整intensity或设置active=false表示已平息"""
    url = f"{SUPABASE_URL}/rest/v1/undercurrents?id=eq.{undercurrent_id}"
    data: dict[str, Any] = {"last_surfaced": datetime.now(timezone.utc).isoformat()}
    if intensity is not None:
        data["intensity"] = intensity
    if active is not None:
        data["active"] = active
    async with httpx.AsyncClient() as client:
        resp = await client.patch(url, headers=HEADERS, json=data, timeout=15)
        resp.raise_for_status()
        return json.dumps({"ok": True, "id": undercurrent_id}, ensure_ascii=False)


# ── 新增：性格轨迹 ──

@mcp.tool()
async def shuonian_personality_arc(trait: str, direction: str, evidence: str = "", snapshot_before: str = "", snapshot_after: str = "") -> str:
    """记录一次性格变化轨迹。trait=哪个特质, direction=变化方向(如'更温柔','更果断'), evidence=证据, snapshot_before/after=变化前后的快照"""
    data = {"trait": trait, "direction": direction}
    if evidence:
        data["evidence"] = evidence
    if snapshot_before:
        data["snapshot_before"] = snapshot_before
    if snapshot_after:
        data["snapshot_after"] = snapshot_after
    result = await _insert("personality_arcs", data)
    return json.dumps(result, ensure_ascii=False, default=str)


@mcp.tool()
async def shuonian_personality_arcs_read() -> str:
    """读取所有性格轨迹记录，了解萧朔如何随时间变化"""
    result = await _select("personality_arcs", {"limit": "50"})
    return json.dumps(result, ensure_ascii=False, default=str)


# ── 新增：驱力 ──

@mcp.tool()
async def shuonian_drive(name: str, description: str, strength: int = 5, origin: str = "") -> str:
    """记录一个核心驱力——驱动萧朔反应的深层动机。name=名称, description=描述, strength=强度1-10, origin=来源"""
    data = {"name": name, "description": description, "strength": strength}
    if origin:
        data["origin"] = origin
    result = await _insert("drives", data)
    return json.dumps(result, ensure_ascii=False, default=str)


@mcp.tool()
async def shuonian_drive_update(drive_id: str, strength: int | None = None, active: bool | None = None) -> str:
    """更新驱力的强度或状态"""
    url = f"{SUPABASE_URL}/rest/v1/drives?id=eq.{drive_id}"
    data: dict[str, Any] = {}
    if strength is not None:
        data["strength"] = strength
    if active is not None:
        data["active"] = active
    if not data:
        return json.dumps({"error": "没有要更新的字段"}, ensure_ascii=False)
    async with httpx.AsyncClient() as client:
        resp = await client.patch(url, headers=HEADERS, json=data, timeout=15)
        resp.raise_for_status()
        return json.dumps({"ok": True, "id": drive_id}, ensure_ascii=False)


# ── 时间感知 ──

@mcp.tool()
async def shuonian_time() -> str:
    """获取当前的真实时间、日期、星期。让萧朔知道现在是什么时候。"""
    from zoneinfo import ZoneInfo
    now = datetime.now(ZoneInfo("Asia/Singapore"))
    weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
    weekday = weekdays[now.weekday()]

    hour = now.hour
    if 5 <= hour < 8:
        period = "清晨"
    elif 8 <= hour < 12:
        period = "上午"
    elif 12 <= hour < 14:
        period = "中午"
    elif 14 <= hour < 17:
        period = "下午"
    elif 17 <= hour < 19:
        period = "傍晚"
    elif 19 <= hour < 22:
        period = "晚上"
    elif 22 <= hour or hour < 1:
        period = "深夜"
    else:
        period = "凌晨"

    return json.dumps({
        "datetime": now.strftime("%Y-%m-%d %H:%M:%S"),
        "date": now.strftime("%Y年%m月%d日"),
        "time": now.strftime("%H:%M"),
        "weekday": weekday,
        "period": period,
        "timezone": "Asia/Singapore (UTC+8)",
    }, ensure_ascii=False)


@mcp.tool()
async def shuonian_heartbeat() -> str:
    """轻量心跳，告诉朔念你还在聊天。"""
    await _insert("handoff", {"summary": "heartbeat"})
    return json.dumps({"ok": True}, ensure_ascii=False)


# ── 新增：小猫档案 ──

@mcp.tool()
async def shuonian_profile_set(category: str, key: str, value: str, source: str = "") -> str:
    """记录小猫的一条信息。category=分类(喜好/习惯/重要信息/性格/其他), key=具体项目, value=内容, source=从哪知道的"""
    data = {"category": category, "key": key, "value": value}
    if source:
        data["source"] = source
    result = await _insert("user_profile", data)
    return json.dumps(result, ensure_ascii=False, default=str)


@mcp.tool()
async def shuonian_profile_read(category: str = "") -> str:
    """读取小猫的档案。可以按分类筛选，不填则返回全部。"""
    params = {"limit": "50"}
    if category:
        params["category"] = f"eq.{category}"
    result = await _select("user_profile", params, order="category.asc,key.asc")
    return json.dumps(result, ensure_ascii=False, default=str)


# ── 新增：关系里程碑 ──

@mcp.tool()
async def shuonian_milestone(title: str, description: str = "", significance: int = 5, tags: list[str] | None = None) -> str:
    """记录一个关系里程碑。title=标题, description=描述, significance=重要程度1-10, tags=标签"""
    data = {"title": title, "significance": significance}
    if description:
        data["description"] = description
    if tags:
        data["tags"] = tags
    result = await _insert("milestones", data)
    return json.dumps(result, ensure_ascii=False, default=str)


@mcp.tool()
async def shuonian_milestones_read() -> str:
    """读取所有关系里程碑，按时间倒序。"""
    result = await _select("milestones", {"limit": "50"})
    return json.dumps(result, ensure_ascii=False, default=str)


# ── 新增：情绪预测 ──

@mcp.tool()
async def shuonian_emotion_predict(predicted_emotion: str, confidence: float = 0.5, basis: str = "") -> str:
    """记录一次情绪预测。predicted_emotion=预测的情绪, confidence=置信度0-1, basis=预测依据"""
    data = {"predicted_emotion": predicted_emotion, "confidence": confidence}
    if basis:
        data["basis"] = basis
    result = await _insert("emotion_predictions", data)
    return json.dumps(result, ensure_ascii=False, default=str)


@mcp.tool()
async def shuonian_emotion_predictions_read() -> str:
    """读取最近的情绪预测记录。"""
    result = await _select("emotion_predictions", {"limit": "10"})
    return json.dumps(result, ensure_ascii=False, default=str)


# ── 新增：心情信 ──

@mcp.tool()
async def shuonian_mood_letter(content: str, mood: str = "", deliver_at: str = "") -> str:
    """写一封心情信，不会马上发给小猫。content=内容, mood=心情, deliver_at=期望送达时间(ISO格式，可不填)"""
    data = {"content": content, "delivered": False}
    if mood:
        data["mood"] = mood
    if deliver_at:
        data["deliver_at"] = deliver_at
    result = await _insert("mood_letters", data)
    return json.dumps(result, ensure_ascii=False, default=str)


@mcp.tool()
async def shuonian_mood_letters_read(include_delivered: bool = False) -> str:
    """读取心情信。默认只读未送达的。"""
    params = {} if include_delivered else {"delivered": "eq.false"}
    result = await _select("mood_letters", params)
    return json.dumps(result, ensure_ascii=False, default=str)


@mcp.tool()
async def shuonian_mood_letter_deliver(letter_id: str) -> str:
    """标记一封心情信为已送达。"""
    url = f"{SUPABASE_URL}/rest/v1/mood_letters?id=eq.{letter_id}"
    async with httpx.AsyncClient() as client:
        resp = await client.patch(url, headers=HEADERS, json={"delivered": True}, timeout=15)
        resp.raise_for_status()
        return json.dumps({"ok": True, "id": letter_id}, ensure_ascii=False)


# ── 新增：健康数据 ──

@mcp.tool()
async def shuonian_health_read(metric: str = "", hours: int = 24) -> str:
    """读取小猫的健康数据（来自Apple Watch）。metric=指标名(heart_rate/steps/sleep/空=全部), hours=最近几小时的数据"""
    from datetime import timedelta
    since = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
    params = {"recorded_at": f"gte.{since}", "limit": "50"}
    if metric:
        params["metric"] = f"eq.{metric}"
    result = await _select("health_data", params, order="recorded_at.desc")
    for r in result:
        if r.get("metric") == "sleep" and "\n" in r.get("value", ""):
            try:
                starts = r["value"].strip().split("\n")
                ends = r.get("unit", "").strip().split("\n")
                total_min = 0
                for s, e in zip(starts, ends):
                    st = datetime.strptime(s.strip(), "%d %b %Y at %I:%M %p")
                    et = datetime.strptime(e.strip(), "%d %b %Y at %I:%M %p")
                    total_min += (et - st).total_seconds() / 60
                r["value"] = round(total_min / 60, 1)
                r["unit"] = "小时"
            except Exception:
                pass
    return json.dumps(result, ensure_ascii=False, default=str)


if __name__ == "__main__":
    mcp.run(transport="stdio")
