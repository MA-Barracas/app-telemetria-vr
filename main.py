from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse
from pathlib import Path
import time

app = FastAPI()
HERE = Path(__file__).parent

devices = {}
dashboard_clients = set()


def public_state(device_id: str):
    d = devices.get(device_id, {})
    return {
        "device_id": device_id,
        "connected": d.get("connected", False),
        "last_seen": d.get("last_seen"),
        "message_number": d.get("message_number", 0),
        "head": d.get("head"),
        "controllers": d.get("controllers", {}),
    }


async def broadcast(message: dict):
    dead = []
    for ws in list(dashboard_clients):
        try:
            await ws.send_json(message)
        except Exception:
            dead.append(ws)
    for ws in dead:
        dashboard_clients.discard(ws)


@app.get("/")
async def home():
    return FileResponse(HERE / "index.html")


@app.get("/dashboard")
async def dashboard():
    return FileResponse(HERE / "dashboard.html")


@app.get("/health")
async def health():
    return {"ok": True}


@app.get("/devices")
async def get_devices():
    return JSONResponse({k: public_state(k) for k in sorted(devices)})


@app.websocket("/ws")
async def xr_ws(websocket: WebSocket):
    device_id = websocket.query_params.get("device_id", "").strip()
    if not device_id:
        await websocket.close(code=1008)
        return

    await websocket.accept()
    devices[device_id] = {
        "connected": True,
        "last_seen": time.time(),
        "message_number": 0,
        "head": None,
        "controllers": {},
    }
    print(f"✅ {device_id}: XR conectado", flush=True)
    await broadcast({"type": "device_update", "device": public_state(device_id)})

    counter = 0
    try:
        while True:
            data = await websocket.receive_json()
            counter += 1
            devices[device_id] = {
                "connected": True,
                "last_seen": time.time(),
                "message_number": counter,
                "head": data.get("head"),
                "controllers": data.get("controllers", {}),
            }
            state = public_state(device_id)

            if counter == 1 or counter % 10 == 0:
                head = state.get("head")
                ctrls = state.get("controllers", {})
                print(f"\n--- {device_id} | paquete #{counter} ---", flush=True)
                if head:
                    print(f"HEAD   x={head['x']:.3f} y={head['y']:.3f} z={head['z']:.3f}", flush=True)
                for hand, c in ctrls.items():
                    print(
                        f"{hand.upper():5} x={c['x']:.3f} y={c['y']:.3f} z={c['z']:.3f} "
                        f"trigger={c.get('trigger', 0):.2f} grip={c.get('squeeze', 0):.2f}",
                        flush=True,
                    )

            await broadcast({"type": "device_update", "device": state})
            await websocket.send_json({"ack": counter, "device_id": device_id, "server_time": time.time()})

    except WebSocketDisconnect:
        if device_id in devices:
            devices[device_id]["connected"] = False
            devices[device_id]["last_seen"] = time.time()
        print(f"❌ {device_id}: XR desconectado", flush=True)
        await broadcast({"type": "device_update", "device": public_state(device_id)})


@app.websocket("/dashboard-ws")
async def dashboard_ws(websocket: WebSocket):
    await websocket.accept()
    dashboard_clients.add(websocket)
    await websocket.send_json({
        "type": "snapshot",
        "devices": {k: public_state(k) for k in sorted(devices)},
    })
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        dashboard_clients.discard(websocket)
