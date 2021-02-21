import speech_recognition as sr
import time
import wave
import threading
import os
import valib
import response
import glob
import logging






    """
    process() method reads data from pyaudio stream for given duration.
    After read, it creates audio frame and save it to .wav file.
    it generates new WAV file every time it gets called.
    """
    def process(self, RECORD_SECONDS):
        frames = []
        for i in range(0, int(RESPEAKER_RATE / CHUNK * RECORD_SECONDS)):
            data = self.stream.read(CHUNK, exception_on_overflow=False)
            frames.append(data)

        out_filename = WAVE_OUTPUT_FILEPATH + str(time.time()) + ".wav"
        wf = wave.open(out_filename, 'wb')
        wf.setnchannels(RESPEAKER_CHANNELS)
        wf.setsampwidth(self.p.get_sample_size(self.p.get_format_from_width(RESPEAKER_WIDTH)))
        wf.setframerate(RESPEAKER_RATE)
        wf.writeframes(b''.join(frames))
        wf.close()
        return out_filename

    """
    voice_command_processor() method reads data from .wav file and convert into text.
    it is using speech_recognition library and recognize_google option to convert speech
    into text.
    """
    def voice_command_processor(self, filename):
        global recognized_text
        with sr.AudioFile(filename) as source:
            #r.adjust_for_ambient_noise(source=source, duration=0.5)
            wait_time = 3
            while True:
                audio = r.record(source, duration=3)
                if audio:
                    break
                time.sleep(1)
                wait_time = wait_time - 1
                if wait_time == 0:
                    break

            try:
                recognized_text = r.recognize_google(audio)
            except sr.UnknownValueError as e:
                pass
            except sr.RequestError as e:
                logger.error("service is down")
                pass
            os.remove(filename)
            return recognized_text



"""a = voice()    # Initializing the voice class."""

"""
Infinite loop:
    1. Reading microphone for 3 sec and generation .wav file.
    2. Creating thread with voice_command_processor() method for converting speech to text.
    3. IF wake word is detected (in my case Gideon):
        a. Clearing recognized_text global variable.
        b. Turing on the LED.
        c. Audio reply with "how can i help you"
        d. Start reading from pyaudio stream for next 5 sec for question.
        e. Convert the audio to text using voice_command_processor().
        f. Process the text using process_text() method from response.py.
        g. once the processing done, it will remove all the files from the output directory.
        f. turn off the LED.
"""
if __name__ == '__main__':

    logger = logging.getLogger('voice assistant')
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler("/mnt/ramdisk/voice.log")
    fh.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    while True:
        file_name = a.process(3)
        logger.info("wake_word said :: " + recognized_text)
        #print("wake_word said :: " + recognized_text)
        if "Gideon" in recognized_text:
            logger.info("wake word detected...")
            recognized_text = ''
            px.wakeup()
            valib.audio_playback('how can i help you')
            time.sleep(0.5)
            command_file_name = a.process(5)
            a.voice_command_processor(command_file_name)
            logger.info("you said :: " + recognized_text)
            px.think()
            status = response.process_text(recognized_text, a)
            while status != 'done':
                pass

            files = glob.glob(os.path.join(WAVE_OUTPUT_FILEPATH + '*.wav'))
            for file in files:
                os.remove(file)
            recognized_text = ''
            px.off()
        else:
            t1 = threading.Thread(target=a.voice_command_processor, args=(file_name,))
            t1.start()
