import whisper

from exAudio import *
from speech2text import *
from utils import download_video

# def audio_to_txt(foldername, model):
#     # load audio and pad/trim it to fit 30 seconds
#     audio = whisper.load_audio(foldername)
#     audio = whisper.pad_or_trim(audio)

#     # make log-Mel spectrogram and move to the same device as the model
#     mel = whisper.log_mel_spectrogram(audio, n_mels=model.dims.n_mels).to(model.device)

#     # detect the spoken language
#     _, probs = model.detect_language(mel)
#     print(f"Detected language: {max(probs, key=probs.get)}")

#     # decode the audio
#     options = whisper.DecodingOptions()
#     result = whisper.decode(model, mel, options)
#     return result

av = input("请输入BV号：")
filename = download_video(av[2:])
foldername = process_audio_split(filename)
breakpoint()
load_whisper("turbo")
run_analysis(foldername, prompt="以下是普通话的句子。")
output_path = f"outputs/{foldername}.txt"
print("转换完成！", output_path)

# model = whisper.load_model("turbo")
# results = audio_to_txt(foldername, model)

# # print the recognized text
# print(result.text)
# #save the result to txt
# txt_out = 'audio/txt_out'
# if os.path.exists(txt_out) == False:
#     os.makedirs(txt_out)
# file_base = os.path.basename(foldername)
# with open(os.path.join(txt_out, f"{file_base}.txt"), "w", encoding="utf-8") as f:
#     f.write(result.text)