# Abi-streaming-server
Streaming Server Stuff and Code

## Setup
To record the stream set the "record" setting in the /etc/ngnix/ngnix.conf in line 40 to true

## OBS Setup
```txt
Allow Numpad Shortcuts:
xmodmap -e "keycode 104 = backslash"

Shortcuts: 
<Num_Enter> Transition
<Num_Sub>   Cut
<Space>     Cut
<Num_0>     Cut
<Num_.>     Fade
<Num_Add>   Fade
<Num_1-9>   select Scene

Virtual Cam:
dnf/apt install v4l2loopback
```

