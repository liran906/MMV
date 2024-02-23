import pygame, requests, os, playsound

file_dir = r'.\vocabulary\save\mp3'

def play_mp3(word):
    init()
    global file_path
    file_path = os.path.join(file_dir, word+'.mp3')
    check_exist(word)
    # playsound.playsound(file_path)
    playwith_pygame()

def check_exist(word):
    file_path = os.path.join(file_dir, word+'.mp3')
    if not os.path.exists(file_path):
        url = 'https://dict.youdao.com/dictvoice?type=0&audio='+word
        soundpack = requests.get(url)
        if soundpack.status_code == 200:
            with open(file_path, 'wb') as f:
                f.write(soundpack.content)
        else:
            print(f"Failed to retrieve audio for '{word}'")

def init():
    if not os.path.exists(file_dir):
        os.mkdir(file_dir)

def playwith_pygame():
    pygame.mixer.init()
    pygame.mixer.music.load(file_path)
    pygame.mixer.music.play()

if __name__ == '__main__':
    play_mp3('example')