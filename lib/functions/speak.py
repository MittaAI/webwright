from lib.function_wrapper import function_info_decorator
from lib.llm import llm_wrapper
from datetime import datetime
import json
from pathlib import Path
from openai import OpenAI
import os
from playsound import playsound

@function_info_decorator
async def llm_text_to_speech(text: str, voice: str = "alloy", play_audio: bool = True, olog=None, llm=None) -> dict:
    """
    Converts text to speech using OpenAI's TTS-1 model and optionally plays the audio.

    :param text: The text to be converted to speech.
    :type text: str
    :param voice: The voice to use for the speech. Options are "alloy", "echo", "fable", "onyx", "nova", and "shimmer". Default is "alloy".
    :type voice: str
    :param play_audio: Whether to play the audio after generation. Default is True.
    :type play_audio: bool
    :return: A dictionary containing the success status and the path to the generated audio file.
    :rtype: dict
    """
    # Add text to prompt:
    olog.add_entry({
        "content": f"Convert to speech: {text}",
        "type": "user_query",
        "timestamp": datetime.now().isoformat()
    })

    try:
        # Get OpenAI token
        openai_token = llm.config.get_openai_api_key()
        if not openai_token:
            raise ValueError("OpenAI token not found")

        client = OpenAI(api_key=openai_token)
        
        # Create output directory
        output_dir = Path("generated_audio")
        output_dir.mkdir(exist_ok=True)
        
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        speech_file_path = output_dir / f"speech_{timestamp}.mp3"

        # Generate speech
        response = client.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=text
        )

        # Save to file
        response.stream_to_file(speech_file_path)

        if play_audio:
            try:
                playsound(str(speech_file_path))
                print("Audio played successfully.")
            except Exception as play_error:
                print(f"Error playing audio: {str(play_error)}")

        return {
            "success": True,
            "audio_file_path": str(speech_file_path)
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }