"""
Test script to exercise Query (HTTP + WS), Ingestion (HTTP), and STT (gRPC unary + streaming).

Run from repo root. Ensure services are up:
 - Query HTTP/WS:  http://localhost:8001  (ws://localhost:8001/ws/chat)
 - Ingest HTTP:    http://localhost:8002
 - STT gRPC:       localhost:50051

If you generated stt_pb2 / stt_pb2_grpc into services/.../protos,
either run this script from repo root or add that directory to PYTHONPATH.
"""

import asyncio
import base64
import json
import os
import sys
from io import BytesIO

import httpx
import websockets

# Try to import gRPC stubs; if missing, unary/streaming GRPC tests will skip.
HAS_GRPC = True
try:
    import grpc
    from stt_service.app.protos import stt_pb2, stt_pb2_grpc
except Exception as e:
    HAS_GRPC = False
    grpc = None
    stt_pb2 = None
    stt_pb2_grpc = None
    print(
        "gRPC stubs not available. Skipping gRPC tests. (Exception: {})".format(e),
        file=sys.stderr,
    )


# Endpoints (adjust if your services run on other hosts/ports)
QUERY_HTTP = "http://localhost:8001"
INGEST_HTTP = "http://localhost:8002"
STT_HOST = "localhost"
STT_PORT = 50051
WS_URL = "ws://localhost:8001/ws/chat"


async def test_query_chat():
    print("\n=== HTTP /chat (Query service) ===")
    # root
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(f"{QUERY_HTTP}/")
            print("/ ->", r.status_code, r.text)
    except Exception as e:
        print("/ error:", repr(e))
        
    # health
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(f"{QUERY_HTTP}/health")
            print("/health ->", r.status_code, r.text)
    except Exception as e:
        print("/health error:", repr(e))
        
    # chat
    try:
        payload = {"query": "Hello test: What is retrieval-augmented generation (RAG)?"}
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.post(f"{QUERY_HTTP}/chat", json=payload)
            print("status:", r.status_code)
            try:
                print("response:", json.dumps(r.json(), indent=2))
            except Exception:
                print("raw body:", r.text)
    except Exception as e:
        print("HTTP /chat error:", repr(e))


async def test_ingestion_admin():
    print("\n=== Ingestion admin endpoints ===")
    async with httpx.AsyncClient(timeout=20.0) as client:
        # 1) upload file (multipart)
        try:
            dummy_bytes = b"dummy test file content"
            files = {"file": ("dummy.txt", BytesIO(dummy_bytes), "text/plain")}
            r = await client.post(f"{INGEST_HTTP}/admin/upload", files=files)
            print("/admin/upload ->", r.status_code, r.text)
        except Exception as e:
            print("/admin/upload error:", repr(e))

        # 2) sync (schedule ingestion)
        try:
            r = await client.post(
                f"{INGEST_HTTP}/admin/sync",
                json={"filename": "dummy.txt", "document_id": "doc_test"},
            )
            print("/admin/sync ->", r.status_code, r.text)
        except Exception as e:
            print("/admin/sync error:", repr(e))

        # 3) delete vectors
        try:
            r = await client.request(
                "DELETE",
                f"{INGEST_HTTP}/admin/vectors",
                json={"document_id": "doc_test"},
            )
            print("/admin/vectors ->", r.status_code, r.text)
        except Exception as e:
            print("/admin/vectors error:", repr(e))


def test_grpc_unary():
    print("\n=== gRPC unary Transcribe (STT) ===")
    if not HAS_GRPC:
        print("Skipping gRPC unary test (stubs not available).")
        return
    target = f"{STT_HOST}:{STT_PORT}"
    try:
        channel = grpc.insecure_channel(target)
        stub = stt_pb2_grpc.STTStub(channel)
        req = stt_pb2.AudioRequest(
            audio_content=b"\x00\x01\x02dummy", filename="test.wav"
        )
        resp = stub.Transcribe(req, timeout=10.0)
        print("gRPC unary response:", resp)
    except Exception as e:
        print("gRPC unary error:", repr(e))


async def test_grpc_streaming():
    print("\n=== gRPC streaming TranscribeStream (STT) ===")
    if not HAS_GRPC:
        print("Skipping gRPC streaming test (stubs not available).")
        return

    target = f"{STT_HOST}:{STT_PORT}"
    # Use the async gRPC API
    try:
        # create async channel
        async with grpc.aio.insecure_channel(target) as channel:
            stub = stt_pb2_grpc.STTStub(channel)

            async def request_gen():
                # first send config
                cfg = stt_pb2.StreamConfig(
                    filename="stream_test.wav",
                    language_code="en",
                    sample_rate=16000,
                    return_partials=True,
                )
                yield stt_pb2.StreamRequest(config=cfg)

                # send a few fake chunks
                for i in range(3):
                    chunk = b"\x00" * 4000  # fake raw audio bytes
                    audio = stt_pb2.AudioChunk(data=chunk, is_last=False)
                    yield stt_pb2.StreamRequest(audio=audio)
                    await asyncio.sleep(0.05)

                # final chunk
                final_audio = stt_pb2.AudioChunk(data=b"", is_last=True)
                yield stt_pb2.StreamRequest(audio=final_audio)

            # call streaming RPC and iterate responses
            async for response in stub.TranscribeStream(request_gen()):
                # response is a StreamResponse; check which field is set
                if response.HasField("partial"):
                    p = response.partial
                    print(
                        "Partial:",
                        p.text if hasattr(p, "text") else p,
                        "stability:",
                        getattr(p, "stability", None),
                    )
                elif response.HasField("final"):
                    f = response.final
                    print(
                        "Final:", f.text, "success:", f.success, "message:", f.message
                    )
                else:
                    print("Unknown response:", response)
    except Exception as e:
        print("gRPC streaming error:", repr(e))


async def test_ws_audio_flow():
    print("\n=== WebSocket audio -> Query (ws) ===")
    try:
        # connect
        async with websockets.connect(WS_URL, max_size=None) as ws:
            print("WS connected. Sending two binary chunks and an end marker...")

            # send binary chunks
            await ws.send(b"\x00\x01chunkA")
            await asyncio.sleep(0.02)
            await ws.send(b"\x00\x02chunkB")
            await asyncio.sleep(0.02)

            # send end marker (server should treat this as "end of audio" signal)
            await ws.send("__END_AUDIO__")

            # read responses until server closes or final message arrives
            # we'll wait up to 10s for a reply
            try:
                resp = await asyncio.wait_for(ws.recv(), timeout=10.0)
                # print raw or json
                try:
                    print("WS recv JSON:", json.dumps(json.loads(resp), indent=2))
                except Exception:
                    print("WS recv (raw):", resp)
            except asyncio.TimeoutError:
                print("No response from WS within timeout.")
    except Exception as e:
        print("WebSocket error:", repr(e))


async def main():
    # run HTTP and ingestion quickly (async)
    await test_query_chat()
    await test_ingestion_admin()

    # run gRPC unary (blocking) and streaming (async)
    test_grpc_unary()
    await test_grpc_streaming()

    # websocket test
    await test_ws_audio_flow()

    print("\n=== All tests attempted ===")


if __name__ == "__main__":
    asyncio.run(main())
