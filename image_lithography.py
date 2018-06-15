from PIL import Image
from simplecrypt import encrypt, decrypt
import random

keys = []


def generateKeys():
    keys.clear()
    path = input("store keys as: ")
    for i in range(0, 6):
        x = randomColor()
        if x not in keys:
            keys.append(x)
    print("keys: ", keys)
    with open(path, "w") as file:
        file.write(str(keys))
        print("keys stored successfully")


def importKeys():
    keys.clear()
    path = input("load keys from: ")
    with open(path, "r") as file:
        for key in (eval(file.readline())):
            if type(key) == int:
                keys.append((key,) * 3)  # generate RGB tuple from 1 channel image
            else:
                keys.append(key)
    print("keys: ", keys)


def decode():
    if not keys:
        print("you have to import keys first")
        input("press enter to continue ")
        importKeys()
    counter = 0
    text = ""
    img = Image.open(input("input image path: "))
    pix = img.load()
    for y in range(0, img.size[1]):
        for x in range(0, img.size[0]):
            if pix[x, y] in keys:
                text += chr(counter)
                counter = 0
            counter += 1
    print("text: ", text)


def encode():
    if not keys:
        while True:
            print("you have to generate(1) or import(2) keys first")
            selection = input("enter your selection (1 or 2): ")
            if selection == "1":
                generateKeys()
                break
            elif selection == "2":
                importKeys()
                break
            else:
                print("invalid input")
    text = input("enter a String to encode: ")
    path = input("store image as: ") + ".png"
    pixels = 1  # the pixel-0 at the beginning
    for c in text: pixels += ord(c)
    width = 0
    height = 0
    # generate an approximately 16:9 image
    while width * height < pixels:
        width += 1
        if height / width < 0.53: height += 1
    img = Image.new('RGB', (width, height))
    pix = img.load()
    i = 0
    counter = 0
    for y in range(0, height):
        for x in range(0, width):
            if i < len(text):
                if counter == ord(text[i]):
                    pix[x, y] = random.choice(keys)
                    counter = 0
                    i += 1
                else:
                    while True:
                        color = randomColor()
                        if color not in keys:
                            break
                    pix[x, y] = color
            else:
                while True:
                    color = randomColor()
                    if color not in keys: break
                pix[x, y] = color
            counter += 1
    img.save(path)
    print("image was stored successfully")
    print("pixels needed: ", pixels, "\npixels used: ", width * height)


def randomColor():
    color = []
    for i in range(0, 3):
        color.append(random.randint(0, 255))
    return tuple(color)


def generatePassword():
    password_location = input("store the password as: ")
    min_char = 80
    max_char = 120
    byte_list = []
    for i in range(random.randint(min_char, max_char)):
        byte_list.append(random.getrandbits(8))
    password = bytes(byte_list)
    with open(password_location, "wb") as file:
        file.write(password)
        print("password stored successfully")
    return password


def hideString():
    while True:
        path = input("choose a png image to hide string in: ")
        text = input("enter the String you want to hide: ")
        img = Image.open(path)
        pixels = 0
        if input("encrypt the string? [Y/n]: ") in ["Yes","yes","Y","y",""]:
            password = generatePassword()
            secret = encrypt(password, text)
        else:
            secret = bytes(text.encode('utf-8'))
        for b in secret:
            pixels += b + 1
        if pixels < img.width * img.height: break
        print("the image is to small to contain that string\nchoose another one with more pixels")
    hide(secret, path)


def hideFile():
    while True:
        file_path = input("file you want to hide: ")
        image_path = input("image you want to hide the file in: ")
        img = Image.open(image_path)
        file = open(file_path, "rb").read()
        if input("encrypt the file? [Y/n]: ") in ["Yes", "Y", "y", "yes",""]:
            password = generatePassword()
            secret = encrypt(password, file)
        else:
            secret = file
        pixels = 0
        for b in secret: pixels += b + 1
        if pixels < img.width * img.height: break
        print("the image is to small to contain that string\nchoose another one with more pixels")
    hide(secret, image_path)


def hide(secret, path):
    # use the last bit of every color for every pixel to store if its relevant for the string
    counter = 0
    img = Image.open(path)
    pix = img
    color = []
    n = 0
    for y in range(0, img.height):
        for x in range(0, img.width):
            for i in range(0, 3):
                color.append(pix[x, y][i])
                if n < len(secret):
                    if counter == secret[n]:
                        color[i] = color[i] | 1
                        counter = 0
                        n += 1
                    else:
                        color[i] = color[i] & 254
                        counter += 1
                else:
                    color[i] = color[i] & 254
                    counter += 1
            pix[x, y] = tuple(color)
            color = []
    img.save(path)


def discoverString():
    image_path = input("choose an image to extract a string from: ")
    secret = discover(image_path)
    if input("is the string encrypted? [Y/n]: ") in ["Yes", "Y", "y", "yes",""]:
        password_location = input("load password from: ")
        with open(password_location, "rb") as file:
            password = file.read()
        text = decrypt(password, secret).decode('utf-8')
    else:
        text = secret.decode('utf-8')
    print("text: ", text)


def discoverFile():
    image_path = input("choose an image to extract a file from: ")
    secret = discover(image_path)
    if input("is the file encrypted? [Y/n]: ") in ["Yes", "Y", "y", "yes",""]:
        password_location = input("load password from (enter for manual input): ")
        if not password_location: password = input("password: ")
        else:
            with open(password_location, "rb") as file:
                password = file.read()
        secret = decrypt(password, secret)
    file_path = input("store discovered file as: ")
    with open(file_path, "wb") as file:
        file.write(secret)


def discover(image_path):
    img = Image.open(image_path)
    counter = 0
    secret = []
    pix = img.load()
    for y in range(0, img.size[1]):
        for x in range(0, img.size[0]):
            for i in range(0, 3):
                if pix[x, y][i] & 1:
                    secret.append(counter)
                    counter = 0
                else:
                    counter += 1
    return bytes(secret)


while True:
    task = input(
        "1) encode\n2) decode\n3) generate Keys\n4) import Keys\n5) hide string in existing image\n"
        "6) discover string\n7) hide file in image\n8) discover file\ninput: ")
    if task == "1":
        encode()
    elif task == "2":
        decode()
    elif task == "3":
        generateKeys()
    elif task == "4":
        importKeys()
    elif task == "5":
        hideString()
    elif task == "6":
        discoverString()
    elif task == "7":
        hideFile()
    elif task == "8":
        discoverFile()
    elif task == "password":
        generatePassword()
    elif task == "exit":
        exit()
    else:
        print("invalid input")
    input("press enter to continue ")
