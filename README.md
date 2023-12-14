# TTS Xoafang camera speaker for Home Assistant

This project provides a media player (custom component) for Home Assistant that plays TTS (text-to-speech) via a Xoafang camera speaker.


The flow is something like this:

- TTS service gets called to play something on the Xoafang camera speaker
- TTS Xoafang camera speaker component disables Bluetooth tracker component
- Bluetooth tracker component terminates any running Bluetooth scans
- TTS Xoafang camera speaker component plays the TTS MP3 file
- TTS Xoafang camera speaker component enables Bluetooth tracker component
- Bluetooth tracker component continues scanning for devices (presence detection)

## Getting Started

### 1) Install SoX (with MP3 support)

```
sudo apt-get install sox libsox-fmt-mp3

or,

apk add sox
```

### 2) Add the TTS Xoafang camera speaker to HA

Copy the TTS Xoafang camera speaker component (from this GitHub repo) and save it to your Home Assistant config directory.

```
custom_components/xiaofang_mediaplayer/media_player.py
```

### 3) Start using it in HA

By this stage (after a reboot), you should be able to start using the TTS Xoafang camera speaker in HA.

Below is an example of how the component is configured. You need to specify the Bluetooth address of your speaker, and optionally set the `volume` level (must be between 0 and 1). If you find your speaker is not playing the first part of the audio (i.e. first second is missing when played back), then you can optionally add some silence before and/or after the original TTS audio hsing the `pre_silence_duration` and `post_silence_duration` options (must be between 0 and 60 seconds). If you've change your TTS cache directory (in your TTS config), then you should set the `cache_dir` here to match.

```
media_player:
  - platform: xiaofang_mediaplayer
    ip_address: [IP_ADDRESS]   # Required - for example, 192.168.0.x
    port: 11032
    volume: 0.45
    start_audio_api: "cgi-bin/scripts?cmd=start&script=30-audio-server"
    stop_audio_api: "cgi-bin/scripts?cmd=stop&script=30-audio-server"
```
To test that it's all working, you can use **Developer Tools > Services** in the HA frontend to play a TTS message through your Xoafang camera speaker:

![image](https://user-images.githubusercontent.com/8870047/57437834-b773ef00-7296-11e9-891e-9a181ebb6520.png)

`{ "entity_id": "media_player.xiaofang_mediaplayer", "message": "Hello" }`

Another way to test it is to add an automation that plays a TTS message whenever HA is started:

```
automation: 
  - alias: Home Assistant Start
    trigger:
      platform: homeassistant
      event: start
    action:
      - delay: '00:00:10'
      - service: tts.google_translate_say
        data:
          entity_id: media_player.xiaofang_mediaplayer
          message: 'Home Assistant has started'
```
