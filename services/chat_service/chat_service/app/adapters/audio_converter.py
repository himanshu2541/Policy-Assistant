import subprocess
import imageio_ffmpeg
from chat_service.app.interfaces import AudioStreamConverter

class FFmpegAudioConverter(AudioStreamConverter):

    def convert_bytes(self, data: bytes) -> bytes:
        """
        Converts WebM bytes -> WAV bytes using a single FFmpeg process.
        """
        if not data:
            return b""

        ffmpeg_cmd = imageio_ffmpeg.get_ffmpeg_exe()
        
        # FFmpeg command: Input pipe -> Output pipe (WAV format, 16k, Mono)
        process = subprocess.Popen(
            [
                ffmpeg_cmd,
                "-i", "pipe:0",       # Read from stdin
                "-f", "wav",          # Output WAV (Container + PCM)
                "-ac", "1",           # Mono
                "-ar", "16000",       # 16k Hz
                "pipe:1",             # Write to stdout
                "-loglevel", "error"
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        # Write all data at once and capture output
        stdout_data, stderr_data = process.communicate(input=data)

        if process.returncode != 0:
            raise RuntimeError(f"FFmpeg conversion failed: {stderr_data.decode()}")

        return stdout_data