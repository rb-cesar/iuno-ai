from __future__ import annotations

import tempfile
import wave
from typing import Optional, List

from iuno.voice.base import AudioRecorder, VoiceError


class SoundDeviceRecorder(AudioRecorder):
    """Gravador simples via `sounddevice`.

    UX: "push-to-talk" por ENTER.
    - Aperte ENTER para começar a gravar
    - Aperte ENTER novamente para parar

    Salva um WAV PCM 16-bit mono/stereo (dependendo do config).
    """

    def __init__(self, sample_rate: int = 16000, channels: int = 1, device: Optional[int] = None):
        self.sample_rate = int(sample_rate)
        self.channels = int(channels)
        self.device = device

        try:
            import sounddevice as sd
        except Exception as e:  # pragma: no cover
            raise VoiceError(
                "Para usar microfone direto, instale a dependência opcional: pip install sounddevice"
            ) from e

        self._sd = sd

    def record_wav(self) -> str:
        sd = self._sd

        print("[MIC] Pressione ENTER para começar a gravar...")
        input()
        print("[MIC] Gravando... pressione ENTER para parar.")

        frames: List[bytes] = []

        def callback(indata, frames_count, time_info, status):  # pragma: no cover
            if status:
                # status é informativo; não aborta automaticamente
                pass
            frames.append(indata.copy().tobytes())

        try:
            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype="int16",
                callback=callback,
                device=self.device,
            ):
                input()  # bloqueia até ENTER
        except Exception as e:
            raise VoiceError(f"Falha ao gravar do microfone: {e}") from e

        if not frames:
            raise VoiceError("Nenhum áudio capturado.")

        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        tmp_path = tmp.name
        tmp.close()

        try:
            with wave.open(tmp_path, "wb") as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(2)  # int16
                wf.setframerate(self.sample_rate)
                wf.writeframes(b"".join(frames))
        except Exception as e:
            raise VoiceError(f"Falha ao salvar WAV temporário: {e}") from e

        print(f"[MIC] Áudio salvo em: {tmp_path}")
        return tmp_path

