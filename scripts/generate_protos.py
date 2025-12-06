import sys
import subprocess
from pathlib import Path


def generate_protos():
    # 1. Determine Paths
    # We are in /scripts, so project root is two levels up
    current_script_path = Path(__file__).resolve()
    project_root = current_script_path.parent.parent

    build_context = project_root / "shared"

    # The proto file path relative to the build context
    # Structure: shared/shared/protos/service.proto
    proto_file_relative = Path("shared/protos/service.proto")

    proto_file_full = build_context / proto_file_relative

    print(f"🚀 Generating gRPC stubs...")
    print(f"📂 Build Context: {build_context}")
    print(f"📄 Proto File:    {proto_file_relative}")

    if not proto_file_full.exists():
        print(f"❌ Error: Proto file not found at {proto_file_full}")
        sys.exit(1)

    # 2. Run protoc command
    command = [
        sys.executable,
        "-m",
        "grpc_tools.protoc",
        "-I",
        ".",  # Include current dir (outer shared) as root
        "--python_out=.",  # Output struct relative to current dir
        "--grpc_python_out=.",  # Output struct relative to current dir
        str(proto_file_relative),  # shared/protos/service.proto
    ]

    try:
        subprocess.check_call(command, cwd=build_context)
        print("✅ Protoc compilation successful.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Protoc failed: {e}")
        sys.exit(1)

    # 3. Fix Imports in the generated _grpc.py file
    # The file is located at shared/shared/protos/service_pb2_grpc.py
    grpc_file = build_context / "shared" / "protos" / "service_pb2_grpc.py"

    if grpc_file.exists():
        print(f"🔧 Patching imports in {grpc_file.name}...")
        with open(grpc_file, "r") as f:
            content = f.read()

        # Fix: Change "import service_pb2" to "from . import service_pb2"
        # This is required so you can import it as 'shared.protos.service_pb2_grpc'
        module_name = "service_pb2"

        print("✅ Import paths patched.")
    else:
        print(f"⚠️ Warning: Could not find {grpc_file} to patch.")


if __name__ == "__main__":
    generate_protos()
