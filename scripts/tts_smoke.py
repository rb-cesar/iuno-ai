"""Smoke test manual para TTS.

Uso:
  py scripts/tts_smoke.py

Ele tenta falar duas frases em sequência com uma pausa curta.
"""

import sys
from pathlib import Path
import time

# Permite importar o pacote local ao executar como script.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from iuno.voice.tts_pyttsx3 import Pyttsx3TTS


def main():
    tts = Pyttsx3TTS()
    print("Falando 1...")
    tts.speak("Teste um")
    time.sleep(0.5)
    print("Falando 2...")
    tts.speak("Teste dois")
    print("Fim")


if __name__ == "__main__":
    main()
