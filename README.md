# Meta Quest WebXR POC

Prueba mínima:

Meta Quest Browser -> WebXR -> WSS -> FastAPI en Render

## Archivos

- `main.py`: FastAPI + WebSocket.
- `index.html`: WebXR mínimo.
- `requirements.txt`: dependencias Python.
- `render.yaml`: configuración opcional para Render.

## Render

Build Command:

```bash
pip install -r requirements.txt
```

Start Command:

```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

Después abre la URL HTTPS de Render desde **Meta Quest Browser**.

## Comprobaciones

- `/health` debe devolver `{"ok":true}`.
- `/latest` muestra el último paquete recibido desde las Quest.
- La página principal debe mostrar:
  - WebSocket: CONECTADO
  - WebXR: IMMERSIVE-VR DISPONIBLE

Pulsa `ENTRAR EN VR`, mueve cabeza y mandos y aprieta el gatillo.
