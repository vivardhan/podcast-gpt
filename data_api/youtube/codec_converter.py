# Third Party Imports
import ffmpeg

FINAL_CODEC = "flac"

def convert_audio_codec(input_path: str, output_path: str, output_codec = FINAL_CODEC: str) -> None:
	try:
		(
			ffmpeg
				.input(input_path)
				.output(output_path, acodec=output_codec)
				.run(quiet=True)
		)
	except:
		print('Could not convert {} to {}'.format(input_path, output_codec))