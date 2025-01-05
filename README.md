# MAC First
```bash
brew install cairo
pip3 install cairosvg
ln -s /opt/homebrew/lib/libcairo.2.dylib .
```

# Second
```bash
pip install chess
pip install Pillow
pip install gym
pip install 'gym[all]'
pip3 install torch torchvision torchaudio
pip install wandb
pip install argparse

```
밑에 이거 안하면 mac에서 안 돌아감 
심볼링 링크를 직접 생성하지 않으면 자꾸 OSerror 발생함.

export PKG_CONFIG_PATH="/opt/homebrew/lib/pkgconfig:$PKG_CONFIG_PATH"
export DYLD_LIBRARY_PATH="/opt/homebrew/lib:$DYLD_LIBRARY_PATH"


## if rendering 
```bash
pip install pyglet
pip install pip==24.0
pip install gym==0.21.0
```

![img_1.png](img_1.png)


```bash
ln -s /opt/homebrew/lib/libcairo.2.dylib .
```
어차피 우리는 masking해서 넣어줄거기 때문에 env.step안에 코드좀 수정해서 넣을거임


cario 때문에 추가적으로 Linux에서 해결해야할 수도 있음

# Linux
```bash
sudo apt-get update
python3 -m pip install cairosvg
sudo apt-get install libcairo2 libcairo2-dev
pip install chess
pip install Pillow
pip install 'gym[all]'
pip3 install torch torchvision torchaudio
pip install wandb
pip install argpaser
```

windows 에서는 안댐 