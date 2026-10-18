import asyncio
import ctypes
import os
import tempfile
import threading
import wave

from winrt.windows.devices.enumeration import DeviceInformation
from winrt.windows.foundation import Uri
from winrt.windows.media import MediaPlaybackType
from winrt.windows.media.control import (
    GlobalSystemMediaTransportControlsSessionManager as SessionManager,
    GlobalSystemMediaTransportControlsSessionPlaybackStatus as PlaybackStatus,
)
from winrt.windows.media.core import MediaSource
from winrt.windows.media.devices import MediaDevice
from winrt.windows.media.playback import (
    MediaCommandEnablingRule,
    MediaPlaybackItem,
    MediaPlaybackState,
    MediaPlayer,
)

# The speaker ignores audio level: its 15 min idle timer only stops while Windows reports
# a *Playing* media session to it over Bluetooth (AVRCP). Tones at any level/frequency
# were ignored, a playing media session held it on. So we loop a silent clip on the
# speaker through a WinRT MediaPlayer, which Windows lists as a playing media session
# ("Speaker Keep-Alive" in the volume flyout).
#
# To stay out of the way we pause while another app plays media (its own Playing status
# keeps the speaker awake), and pass media keys that Windows routes to our session on to
# the app that played last.

# Only this speaker is kept awake, whatever the Windows default output is. Matched as a
# substring of the device name; change it to keep a different speaker alive.
SPEAKER_NAME = "Sound Pocket"
TITLE = "Speaker Keep-Alive"

# How often to check the speaker connection and other apps' playback
POLL_INTERVAL = 2.0

is_playing = False  # keep-alive enabled (tray Pause/Resume)

_loop = None
_wake = None
_thread = None
_manager = None
_player = None
_stalled = 0
_last_other = None  # session id of the app that last played media, for forwarding keys


def _own_session_id():
    # Windows identifies a desktop app's media session by its process image name
    buf = ctypes.create_unicode_buffer(1024)
    ctypes.windll.kernel32.GetModuleFileNameW(None, buf, len(buf))
    return os.path.basename(buf.value)


_OWN_ID = _own_session_id()


def _is_speaker(name):
    return SPEAKER_NAME.lower() in name.lower()


def _silence_file():
    path = os.path.join(tempfile.gettempdir(), "SpeakerKeepAlive-silence.wav")
    if not os.path.exists(path):
        with wave.open(path, "wb") as f:
            f.setnchannels(1)
            f.setsampwidth(2)
            f.setframerate(44100)
            f.writeframes(bytes(2 * 44100 * 5))
    return path


async def _find_speaker():
    devices = await DeviceInformation.find_all_async_aqs_filter(
        MediaDevice.get_audio_render_selector())
    return next((d for d in devices if _is_speaker(d.name)), None)


def _forwarder(action):
    def handler(sender, args):
        args.handled = True  # keep the keep-alive playing
        _loop.call_soon_threadsafe(lambda: asyncio.ensure_future(_forward(action)))
    return handler


async def _forward(action):
    others = [s for s in _manager.get_sessions() if s.source_app_user_model_id != _OWN_ID]
    target = next((s for s in others if s.source_app_user_model_id == _last_other),
                  others[0] if others else None)
    if target is None:
        return
    if action == "next":
        await target.try_skip_next_async()
    elif action == "previous":
        await target.try_skip_previous_async()
    else:
        await target.try_toggle_play_pause_async()
    _wake.set()  # yield right away if that started their playback


def _open_player(device):
    player = MediaPlayer()
    player.audio_device = device
    player.is_looping_enabled = True
    item = MediaPlaybackItem(MediaSource.create_from_uri(Uri(_silence_file())))
    props = item.get_display_properties()
    props.type = MediaPlaybackType.MUSIC
    props.music_properties.title = TITLE
    props.music_properties.artist = "Keeping your speaker awake"
    item.apply_display_properties(props)
    player.source = item
    commands = player.command_manager
    commands.next_behavior.enabling_rule = MediaCommandEnablingRule.ALWAYS
    commands.previous_behavior.enabling_rule = MediaCommandEnablingRule.ALWAYS
    commands.add_play_received(_forwarder("play_pause"))
    commands.add_pause_received(_forwarder("play_pause"))
    commands.add_next_received(_forwarder("next"))
    commands.add_previous_received(_forwarder("previous"))
    player.play()
    return player


def _close_player():
    global _player
    if _player is None:
        return
    try:
        _player.pause()
        _player.close()
    except OSError:
        pass
    _player = None


async def _tick():
    global _player, _stalled, _last_other
    device = await _find_speaker() if is_playing else None
    if device is None:
        _close_player()
        return
    if _player is None:
        _player = _open_player(device)
        _stalled = 0
        return
    playing = [s for s in _manager.get_sessions()
               if s.source_app_user_model_id != _OWN_ID
               and s.get_playback_info().playback_status == PlaybackStatus.PLAYING]
    state = _player.playback_session.playback_state
    if playing:
        _last_other = playing[0].source_app_user_model_id
        if state == MediaPlaybackState.PLAYING:
            _player.pause()
    elif state == MediaPlaybackState.PLAYING:
        _stalled = 0
    else:
        # Won't resume, e.g. the speaker reconnected between two polls and the player
        # lost its device: start over with a fresh one
        _stalled += 1
        if _stalled > 2:
            _close_player()
        else:
            _player.play()


async def _main():
    global _loop, _wake, _manager
    _loop = asyncio.get_running_loop()
    _wake = asyncio.Event()
    _manager = await SessionManager.request_async()
    while True:
        try:
            await _tick()
        except Exception:
            _close_player()  # retry from scratch next tick; never let this thread die
        try:
            await asyncio.wait_for(_wake.wait(), POLL_INTERVAL)
        except asyncio.TimeoutError:
            pass
        _wake.clear()


def _poke():
    if _loop is not None:
        _loop.call_soon_threadsafe(_wake.set)


def start_audio():
    global is_playing, _thread
    is_playing = True
    if _thread is None:
        _thread = threading.Thread(target=asyncio.run, args=(_main(),), daemon=True)
        _thread.start()
    _poke()


def stop_audio():
    global is_playing
    is_playing = False
    _poke()
