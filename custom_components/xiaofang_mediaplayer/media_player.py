"""
Support for TTS on a Xiafang Camera

"""
import voluptuous as vol
from homeassistant.components import media_source
from homeassistant.components.media_player import (
    SUPPORT_PLAY_MEDIA,
    # SUPPORT_VOLUME_SET,
    PLATFORM_SCHEMA,
    MediaPlayerEntity,
    MediaType
)
from homeassistant.const import (
    CONF_NAME, STATE_OFF, STATE_PLAYING
)
from homeassistant.components.media_player.browse_media import (
    async_process_play_media_url,
)
import homeassistant.helpers.config_validation as cv

import subprocess
import asyncio

import logging

import os
# import re
# import sys
# import time

DOMAIN = "xiaofang_mediaplayer"

DEFAULT_NAME = 'Xiaofang Camera Speaker'
DEFAULT_VOLUME = 0.5
DEFAULT_CACHE_DIR = "tts"
DEFAULT_SILENCE_DURATION = 0.0
DEFAULT_ADDRESS = ''
DEFAULT_PORT = 11032

# SUPPORT_BLU_SPEAKER = SUPPORT_PLAY_MEDIA | SUPPORT_VOLUME_SET

CONF_ADDRESS = 'ip_address'
CONF_PORT = 'port'
CONF_VOLUME = 'volume'
CONF_CACHE_DIR = 'cache_dir'
CONF_PRE_SILENCE_DURATION = 'pre_silence_duration'
CONF_POST_SILENCE_DURATION = 'post_silence_duration'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Optional(CONF_ADDRESS, default=DEFAULT_ADDRESS): cv.string,
    vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.positive_int,
    vol.Optional(CONF_VOLUME, default=DEFAULT_VOLUME):
        vol.All(vol.Coerce(float), vol.Range(min=0, max=1)),
    vol.Optional(CONF_PRE_SILENCE_DURATION, default=DEFAULT_SILENCE_DURATION):
        vol.All(vol.Coerce(float), vol.Range(min=0, max=60)),
    vol.Optional(CONF_POST_SILENCE_DURATION, default=DEFAULT_SILENCE_DURATION):
        vol.All(vol.Coerce(float), vol.Range(min=0, max=60)),
    vol.Optional(CONF_CACHE_DIR, default=DEFAULT_CACHE_DIR): cv.string,
})

_LOGGER = logging.getLogger(__name__)

def setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup the Bluetooth Speaker platform."""
    name = config.get(CONF_NAME)
    address = config.get(CONF_ADDRESS)
    port = int(config.get(CONF_PORT))
    volume = float(config.get(CONF_VOLUME))
    pre_silence_duration = float(config.get(CONF_PRE_SILENCE_DURATION))
    post_silence_duration = float(config.get(CONF_POST_SILENCE_DURATION))
    cache_dir = get_tts_cache_dir(hass, config.get(CONF_CACHE_DIR))

    add_devices([XiaofangSpeakerDevice(hass, name, address, port, volume, pre_silence_duration, post_silence_duration, cache_dir)])
    return True

def get_tts_cache_dir(hass, cache_dir):
    """Get cache folder."""
    if not os.path.isabs(cache_dir):
        cache_dir = hass.config.path(cache_dir)
    return cache_dir

class XiaofangSpeakerDevice(MediaPlayerEntity):
    """Representation of a Xiaofang Speaker on the network."""

    def __init__(self, hass, name, address, port, volume, pre_silence_duration, post_silence_duration, cache_dir):
        """Initialize the device."""
        self._hass = hass
        self._name = name
        self._is_standby = True
        self._current = None
        self._address = address
        self._port = port
        self._volume = volume
        self._pre_silence_duration = pre_silence_duration
        self._post_silence_duration = post_silence_duration
        self._cache_dir = self.get_tts_cache_dir(cache_dir)

    def get_tts_cache_dir(self, cache_dir):
        """Get cache folder."""
        if not os.path.isabs(cache_dir):
            cache_dir = hass.config.path(cache_dir)
        return cache_dir

    def update(self):
        """Retrieve latest state."""
        if self._is_standby:
            self._current = None
        else:
            self._current = True

    @property
    def name(self):
        """Return the name of the device."""
        return self._name

    # MediaPlayerDevice properties and methods
    @property
    def state(self):
        """Return the state of the device."""
        if self._is_standby:
            return STATE_OFF
        else:
            return STATE_PLAYING

    @property
    def supported_features(self):
        """Flag media player features that are supported."""
        return SUPPORT_PLAY_MEDIA

    @property
    def volume_level(self):
        """Volume level of the media player (0..1)."""
        return self._volume

    def set_volume_level(self, volume):
        """Set volume level, range 0..1."""
        # self._vlc.audio_set_volume(int(volume * 100))
        self._volume = volume

    async def async_play_media(self, media_type, media_id, **kwargs):
        """Send the play command."""
        del kwargs
        self._is_standby = False

        if media_source.is_media_source_id(media_id):
            media_type = MediaType.MUSIC
            play_item = await media_source.async_resolve_media(
                self.hass, media_id, self.entity_id
            )
            media_id = async_process_play_media_url(self.hass, play_item.url)
        _LOGGER.debug('Media Type: %s', media_type)
        if media_type in [MediaType.MUSIC, MediaType.PLAYLIST]:
            command = "sox -t mp3 '{}' -t raw -c 1 -r 32k -e signed-integer -b 16 - vol {} | nc {} {}".format(media_id, self._volume, self._address, self._port)
            _LOGGER.debug('Executing command: %s', command)
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE)
            stdout, stderr = await process.communicate()
            self._is_standby = True
        else:
            _LOGGER.error(
                "Invalid media type %s. Only %s and %s are supported",
                media_type,
                MediaType.MUSIC,
                MediaType.PLAYLIST,
            )