from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse
from pathlib import Path
import time

app = FastAPI()
HERE = Path(__file__).parent

latest_packet = {
    "status": "No se han recibido datos XR todavía."
}


@app.get("/")
async def home():
    return FileResponse(HERE / "index.html")


@app.get("/health")
async def health():
    return {"ok": True}


@app.get("/latest")
async def latest():
    """Permite comprobar desde cualquier navegador el último paquete recibido."""
    return JSONResponse(latest_packet)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    global latest_packet

    await websocket.accept()
    print("✅ WebSocket conectado", flush=True)

    counter = 0

    try:
        while True:
            data = await websocket.receive_json()
            counter += 1

            latest_packet = {
                "received_at_server": time.time(),
                "message_number": counter,
                **data,
            }

            # No inundamos los logs de Render:
            # mostramos aproximadamente 1 de cada 10 paquetes.
            if counter == 1 or counter % 10 == 0:
                head = data.get("head")
                controllers = data.get("controllers", {})

                print(f"\n--- XR paquete #{counter} ---", flush=True)

                if head:
                    print(
                        "HEAD  "
                        f"x={head['x']:.3f} "
                        f"y={head['y']:.3f} "
                        f"z={head['z']:.3f}",
                        flush=True,
                    )

                for hand, c in controllers.items():
                    print(
                        f"{hand.upper():5} "
                        f"x={c['x']:.3f} "
                        f"y={c['y']:.3f} "
                        f"z={c['z']:.3f} "
                        f"trigger={c.get('trigger', 0):.2f} "
                        f"squeeze={c.get('squeeze', 0):.2f}",
                        flush=True,
                    )

            # Confirma al navegador que el servidor ha recibido el paquete.
            await websocket.send_json({
                "ack": counter,
                "server_time": time.time(),
            })

    except WebSocketDisconnect:
        print("❌ WebSocket desconectado", flush=True)
