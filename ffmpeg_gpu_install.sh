apt-get remove -y ffmpeg
mkdir ffmpeg_install
cd ffmpeg_install

apt-get install -y gcc
apt-get install linux-headers-$(uname -r)

wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-ubuntu2204.pin
mv cuda-ubuntu2204.pin /etc/apt/preferences.d/cuda-repository-pin-600
wget https://developer.download.nvidia.com/compute/cuda/11.7.0/local_installers/cuda-repo-ubuntu2204-11-7-local_11.7.0-515.43.04-1_amd64.deb
dpkg -i cuda-repo-ubuntu2204-11-7-local_11.7.0-515.43.04-1_amd64.deb
cp /var/cuda-repo-ubuntu2204-11-7-local/cuda-*-keyring.gpg /usr/share/keyrings/
echo "===================================================================keyring installed====================================================================================================================="
ls -la /usr/share/keyrings
apt-get update
apt-get -y install cuda


git clone https://git.videolan.org/git/ffmpeg/nv-codec-headers.git
cd nv-codec-headers
make -j 8
make install
cd ../

git clone https://git.ffmpeg.org/ffmpeg.git ffmpeg/
apt-get install -y build-essential yasm cmake libtool libc6 libc6-dev unzip wget libnuma1 libnuma-dev
cd ffmpeg/
./configure --enable-nonfree --enable-cuda-nvcc --enable-libnpp --extra-cflags=-I/usr/lib/cuda/include --extra-ldflags=-L/usr/lib/cuda/lib64 --disable-static --enable-shared
make -j 8
make install
cd ../../
rm -R ffmpeg_install
