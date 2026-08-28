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


if __name__ == "__main__":
    mcp.run(transport="stdio")
