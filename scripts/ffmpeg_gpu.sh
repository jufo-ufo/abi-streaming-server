ffmpeg -y -vsync 0 -hwaccel cuda -hwaccel_output_format cuda -extra_hw_frames 8 -i $1 -c:v h264_nvenc -b:v 1200k $2

