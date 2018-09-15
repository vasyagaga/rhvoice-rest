#!/usr/bin/env python3

# Copyright (C) 2010-2013  Olga Yakovleva <yakovleva.o.v@gmail.com>
# Copyright (C) 2015  anatoly techtonik <techtonik@gmail.com>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# Base on:
# https://github.com/Olga-Yakovleva/RHVoice/blob/master/src/nvda-synthDriver/__init__.py
# https://github.com/techtonik/RHVoice/blob/master/src/nvda-synthDriver/RHVoice.py

__author__ = "Olga Yakovleva <yakovleva.o.v@gmail.com>"
__version__ = '0.7.2'

import os
import time
import wave

from ctypes import CDLL, CFUNCTYPE, POINTER, Structure, c_char_p, c_double
from ctypes import c_int, c_uint, c_short, c_void_p, byref, sizeof, string_at

LIB = None
RESPONSE_TIME = 0


# --- bindings ---
class RHVoice_tts_engine_struct(Structure):
    pass


RHVoice_tts_engine = POINTER(RHVoice_tts_engine_struct)


class RHVoice_message_struct(Structure):
    pass


RHVoice_message = POINTER(RHVoice_message_struct)


class RHVoice_callback_types:
    set_sample_rate = CFUNCTYPE(c_int, c_int, c_void_p)
    play_speech = CFUNCTYPE(c_int, POINTER(c_short), c_uint, c_void_p)
    process_mark = CFUNCTYPE(c_int, c_char_p, c_void_p)
    word_starts = CFUNCTYPE(c_int, c_uint, c_uint, c_void_p)
    word_ends = CFUNCTYPE(c_int, c_uint, c_uint, c_void_p)
    sentence_starts = CFUNCTYPE(c_int, c_uint, c_uint, c_void_p)
    sentence_ends = CFUNCTYPE(c_int, c_uint, c_uint, c_void_p)
    play_audio = CFUNCTYPE(c_int, c_char_p, c_void_p)


class RHVoice_callbacks(Structure):
    _fields_ = [("set_sample_rate", RHVoice_callback_types.set_sample_rate),
                ("play_speech", RHVoice_callback_types.play_speech),
                ("process_mark", RHVoice_callback_types.process_mark),
                ("word_starts", RHVoice_callback_types.word_starts),
                ("word_ends", RHVoice_callback_types.word_ends),
                ("sentence_starts", RHVoice_callback_types.sentence_starts),
                ("sentence_ends", RHVoice_callback_types.sentence_ends),
                ("play_audio", RHVoice_callback_types.play_audio)]


class RHVoice_init_params(Structure):
    _fields_ = [("data_path", c_char_p),
                ("config_path", c_char_p),
                ("resource_paths", POINTER(c_char_p)),
                ("callbacks", RHVoice_callbacks),
                ("options", c_uint)]


class RHVoice_message_type:
    text = 0
    ssml = 1
    characters = 2


class RHVoice_voice_gender:
    unknown = 0
    male = 1
    female = 2


class RHVoice_voice_info(Structure):
    _fields_ = [("language", c_char_p),
                ("name", c_char_p),
                ("gender", c_int)]


class RHVoice_punctuation_mode:
    default = 0
    none = 1
    all = 2
    some = 3


class RHVoice_capitals_mode:
    default = 0
    off = 1
    word = 2
    pitch = 3
    sound = 4


class RHVoice_synth_params(Structure):
    _fields_ = [("voice_profile", c_char_p),
                ("absolute_rate", c_double),
                ("absolute_pitch", c_double),
                ("absolute_volume", c_double),
                ("relative_rate", c_double),
                ("relative_pitch", c_double),
                ("relative_volume", c_double),
                ("punctuation_mode", c_int),
                ("punctuation_list", c_char_p),
                ("capitals_mode", c_int)]


def load_tts_library(lib_path=None):
    global LIB
    if LIB:
        return LIB
    lib_path = lib_path or 'RHVoice.dll' if os.name == 'nt' else 'libRHVoice.so'
    lib = CDLL(lib_path if os.name == 'nt' else lib_path.encode())
    lib.RHVoice_get_version.restype = c_char_p
    lib.RHVoice_new_tts_engine.argtypes = (POINTER(RHVoice_init_params),)
    lib.RHVoice_new_tts_engine.restype = RHVoice_tts_engine
    lib.RHVoice_delete_tts_engine.argtypes = (RHVoice_tts_engine,)
    lib.RHVoice_delete_tts_engine.restype = None
    lib.RHVoice_get_number_of_voices.argtypes = (RHVoice_tts_engine,)
    lib.RHVoice_get_number_of_voices.restype = c_uint
    lib.RHVoice_get_voices.argtypes = (RHVoice_tts_engine,)
    lib.RHVoice_get_voices.restype = POINTER(RHVoice_voice_info)
    lib.RHVoice_get_number_of_voice_profiles.argtypes = (RHVoice_tts_engine,)
    lib.RHVoice_get_number_of_voice_profiles.restype = c_uint
    lib.RHVoice_get_voice_profiles.argtypes = (RHVoice_tts_engine,)
    lib.RHVoice_get_voice_profiles.restype = POINTER(c_char_p)
    lib.RHVoice_are_languages_compatible.argtypes = (RHVoice_tts_engine, c_char_p, c_char_p)
    lib.RHVoice_are_languages_compatible.restype = c_int
    lib.RHVoice_new_message.argtypes = (
        RHVoice_tts_engine, c_char_p, c_uint, c_int, POINTER(RHVoice_synth_params), c_void_p)
    lib.RHVoice_new_message.restype = RHVoice_message
    lib.RHVoice_delete_message.arg_types = (RHVoice_message,)
    lib.RHVoice_delete_message.restype = None
    lib.RHVoice_speak.argtypes = (RHVoice_message,)
    lib.RHVoice_speak.restype = c_int
    LIB = lib
    return lib


# --- main code ---

class SpeechCallback(object):
    sample_size = sizeof(c_short)

    def __init__(self):
        self._sample_rate = 24000

    def __call__(self, samples, count, user_data):
        """Should return False to stop synthesis"""
        return True

    def set_sample_rate(self, rate, *_):
        self._sample_rate = rate
        return True


class DebugCallback(SpeechCallback):
    def __init__(self):
        super().__init__()
        self.counter = 0
        self.datasize = 0
        self.starttime = time.clock()

    def __call__(self, samples, count, user_data):
        self.counter += 1
        size = count * self.sample_size
        self.datasize += size
        kbps = self.datasize / (time.clock() - self.starttime) / 1024
        self.debug(count, size, kbps)
        return True

    def debug(self, count, size, kbps):
        print("speech callback %s time(s) samples: %s, size: %s, %.2f kBps" % (self.counter, count, size, kbps))


class WaveWriteCallback(SpeechCallback):
    """ Callback that writes sound to wave file. """

    def __init__(self):
        super().__init__()
        self.file = None
        self.filename = 'test.wav'

    def set(self, filename):
        self.filename = filename
        self.close()

    def _open(self):
        if self.file:
            self.file.close()
        self.file = wave.open(self.filename, 'wb')
        self.file.setnchannels(1)
        self.file.setsampwidth(self.sample_size)
        self.file.setframerate(self._sample_rate)

    def close(self):
        if self.file:
            self.file.close()
            self.file = None

    def __call__(self, samples, count, user_data):
        """Should return False to stop synthesis"""
        global RESPONSE_TIME
        if not self.file:
            self._open()
        self.file.writeframes(string_at(samples, count * self.sample_size))
        if not RESPONSE_TIME:
            RESPONSE_TIME = time.time()
        return True


def get_rhvoice_version():
    global LIB
    if not LIB:
        load_tts_library()
    return LIB.RHVoice_get_version().decode('utf-8')


def get_engine(play_speech_cb=DebugCallback(), set_sample_rate_cb=None, resources=None, data_path=None):
    """
    Load DLL and initialize speech engine - load language data
    and set callbacks.
    """

    global LIB, init_params  # need to preserve reference for ctypes
    if not LIB:
        load_tts_library()

    # creating obligatory callback with .play_speech()
    # RHVoice_new_tts_engine fails without callback
    callbacks = RHVoice_callbacks()
    callbacks.play_speech = RHVoice_callback_types.play_speech(play_speech_cb)
    callbacks.set_sample_rate = RHVoice_callback_types.set_sample_rate(
        set_sample_rate_cb or play_speech_cb.set_sample_rate
    )
    # possible callbacks
    resource_paths = [b'/usr/local/etc/RHVoice/dicts/Russian/', ] if not resources else [k.encode() for k in resources]
    init_params = RHVoice_init_params()
    # noinspection PyTypeChecker
    init_params.resource_paths = (c_char_p * (len(resource_paths) + 1))(*(resource_paths + [None]))
    init_params.data_path = data_path.encode() if data_path else b'/usr/local/share/RHVoice'
    init_params.callbacks = callbacks
    # init_params.config_path = '/usr/local/etc/RHVoice/RHVoice.conf'.encode()
    engine = LIB.RHVoice_new_tts_engine(byref(init_params))
    if not engine:
        raise RuntimeError('RHVoice: engine initialization error')
    return engine


def get_synth_params(voice: str):
    voice = voice or 'anna'
    voice = voice.capitalize()
    if voice != 'Anna':
        voice = '{}+Anna'.format(voice)
    return RHVoice_synth_params(
        voice_profile=voice.encode(),
        absolute_rate=0,
        relative_rate=1,
        absolute_pitch=0,
        relative_pitch=1,
        absolute_volume=0,
        relative_volume=1,
        punctuation_mode=RHVoice_punctuation_mode.default,
        punctuation_list=None,
        capitals_mode=RHVoice_capitals_mode.default
    )


def speak_generate(text, synth_params, engine):
    if not LIB:
        raise RuntimeError('RHVoice: Load library before')
    text = text.encode()
    message = LIB.RHVoice_new_message(
        engine,
        text,
        len(text),
        RHVoice_message_type.text,
        byref(synth_params),
        None
    )
    if not message:
        raise RuntimeError('RHVoice: message building error')
    LIB.RHVoice_speak(message)
    LIB.RHVoice_delete_message(message)  # free the memory (check when message is stored)


def get_voices(engine):
    """
    Returns nested dictionary with voice information. First
    level key is voice name in lowercase, second level keys
    are voice properties.
    """
    global LIB
    if not LIB:
        load_tts_library()
    genders = {1: 'male', 2: 'female'}
    voices = dict()
    voices_total = LIB.RHVoice_get_number_of_voices(engine)
    first_voice = LIB.RHVoice_get_voices(engine)
    for voiceno in range(voices_total):
        vi = first_voice[voiceno]
        key = vi.name.lower().decode()
        voices[key] = dict(
            no=voiceno,
            name=vi.name.decode(),
            lang=vi.language.decode(),
            gender=genders[vi.gender]
        )
    return voices


def main():
    global RESPONSE_TIME
    start_time = time.time()

    print('Versions:')
    print(' RHVoice:    {}'.format(get_rhvoice_version()))
    print(' Python API: {}'.format(__version__))
    print()

    wave_ = WaveWriteCallback()
    engine = get_engine(wave_)

    voices = get_voices(engine)
    voice_order = sorted(voices.items(), key=lambda x: x[1]['no'])
    voice_order = [v[0] for v in voice_order]
    print('Voice     Language  Gender')
    for i in range(len(voices)):
        voice = voices[voice_order[i]]
        print('  {name:10}  {lang:2}    {gender:2} '.format(**voice))
    print('Number of voices: {}'.format(len(voices)))
    print()

    texts = ['Я умею сохранять свой голос в mp3', ]

    synth_params = get_synth_params('anna')
    print('Load time: {}'.format(time.time() - start_time))
    for i in range(len(texts)):
        start_time = time.time()
        RESPONSE_TIME = 0
        wave_.set('{}.wav'.format(i))
        speak_generate(texts[i], synth_params, engine)
        response = RESPONSE_TIME - start_time
        start_time = time.time() - start_time
        print('{}. Work: {}, Response: {}'.format(i, start_time, response))


if __name__ == '__main__':
    main()