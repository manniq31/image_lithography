from PIL import Image
from simplecrypt import encrypt, decrypt
import random
import sys

keys = []
yes = ["Yes", "Y", "y", "yes", ""]
instructions = ("Help:\n"
        "Usage: ImageLithography MODE  [Arguments depending on mode]\n"
        "     give no mode and arguments to start in interactive mode\n\n\n"
        
        
        "MODES: generate, hide, discover, password, keys\n"
        "     generate:   generate an image with random colored pixels hiding a file or text\n"
        "       arguments: TEXT or PATH TO A FILE you want to hide\n\n"
        
        "     hide:       hide a file or text in an existing image (overwrites existing image)\n"
        "       arguments: TEXT or FILE, [PASSWORD (file or \"generate\")], IMAGE\n\n"
        
        "     discover:   discover data from an image and store it\n"
                "       arguments: IMAGE, [PASSWORD], OUTPUT (file or \"display\")\n"
                "     password:   generate a password to use it in the \"hide\" mode\n"
                "     keys:       generate keys to use them in the \"encode\" mode\n")


def generateKeys():
    keys.clear()
    path = input("store keys as: ")
    for i in range(6):
        color = randomColor()
        if color not in keys:
            keys.append(color)
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
    image = Image.open(input("input image path: ")).getdata()
    for pixel in image:
        if pixel in keys:
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
    path = input("store image as: ")
    pixels = 1  # the pixel-0 at the beginning
    for c in text: pixels += ord(c)
    width = 0
    height = 0
    # generate an approximately 16:9 image
    while width * height < pixels:
        width += 1
        if height / width < 0.53: height += 1
    image = []
    i = 0
    counter = 0
    for pixel in range(0, height * width):
        if i < len(text):
            if counter == ord(text[i]):
                pixel = random.choice(keys)
                counter = 0
                i += 1
            else:
                while True:
                    color = randomColor()
                    if color not in keys:
                        break
                pixel = color
        else:
            while True:
                color = randomColor()
                if color not in keys: break
            pixel = color
        counter += 1
        for i in range(0, 3): image.append(pixel[i])
    Image.frombytes("RGB", (width, height), bytes(image)).save(path)
    print("image was stored successfully")
    print("pixels needed: ", pixels, "\n"
          "pixels used: ", width * height)


def randomColor():
    color = []
    for i in range(0, 3):
        color.append(random.randint(0, 255))
    return tuple(color)


def generatePassword():
    password_location = input("store the password as: ")
    min_char = 16
    max_char = 32
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
        if input("encrypt the string? [Y/n]: ") in yes:
            password = generatePassword()
            secret = encrypt(password, text)
        else:
            secret = bytes(text.encode('utf-8'))
        if validateImage(secret, path): break
    hide(secret, path)


def hideFile():
    while True:
        file_path = input("file you want to hide: ")
        image_path = input("image you want to hide the file in: ")
        file = open(file_path, "rb").read()
        if input("encrypt the file? [Y/n]: ") in yes:
            password = generatePassword()
            secret = encrypt(password, file)
        else:
            secret = file
        if validateImage(secret, image_path): break
    hide(secret, image_path)

def validateImage(secret, path):
    pixels = 0
    for b in secret: pixels += b + 1
    with Image.open(path) as img:
        if pixels < img.width * img.height:
            print("the image is to small to contain the data\nchoose another one with more pixels")
            return False
    return True

def hide(secret, path):
    # use the last bit of every color for every pixel to store if its relevant for the string
    counter = 0
    with Image.open(path) as img:
        data = img.tobytes()
        mode = img.mode
        size = img.size
    new_image = []
    n = 0
    for byte in data:
        if n < len(secret):
            if counter == secret[n]:
                new_byte = byte | 1
                counter = 0
                n += 1
            else:
                new_byte = byte & 254
                counter += 1
        else:
            new_byte = byte & 254
            counter += 1
        new_image.append(new_byte)
    Image.frombytes(mode, size, bytes(new_image)).save(path)
    print("immage saved succesfully")


def discover():
    image_path = input("choose an image to extract data from: ")
    secret = discoverSecret(image_path)
    if input("is the data encrypted? [Y/n]: ") in yes:
        password_location = input("load password from (leave empty for manual input): ")
        if not password_location:
            password = input("password: ")
        else:
            with open(password_location, "rb") as file:
                password = file.read()
        data = decrypt(password, secret)
    else:
        data = secret
    try:
        text = data.decode('utf-8')
        if input("the data is text\n"
                 "do you want to display it? [Y/n]: ") in yes:
            print("text:\n",text)
        file_path = input("store text as: ")
    except UnicodeDecodeError:
        file_path = input("the data can't be shown as text\n"
                          "store discovered file as: ")
    if file_path is not "":
        with open(file_path, "wb") as file:
            file.write(secret)
        print("file stored succesfully")


def discoverSecret(image_path):
    with Image.open(image_path) as img:
        data = img.tobytes()
    counter = 0
    secret = []
    for byte in data:
        if byte & 1:
            secret.append(counter)
            counter = 0
        else:
            counter += 1
    return bytes(secret)

def main():
    while True:
        task = input(
            "1) encode\n"
            "2) decode\n"
            "3) generate Keys\n"
            "4) import Keys\n"
            "5) hide string in existing image\n"
            "6) hide file in image\n"
            "7) discover file/string\n"
            "input: ")
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
            hideFile()
        elif task == "7":
            discover()
        elif task == "exit":
            exit()
        else:
            print("invalid input")
        input("press enter to continue ")


def parseInput(arguments):
    if not arguments:
        main()
    elif arguments[0] == "help":
        print(instructions)

    # hide function
    elif arguments[0] == "hide":
        if len(arguments) == 3:
            hide(open(arguments[1], "rb").read(), arguments[2])
        elif len(arguments) == 4:
            if arguments[2] == "generate":
                password = generatePassword()
            else:
                with open(arguments[2], "rb") as file:
                    password = file.read()
            with open(arguments[1], "rb") as file:
                secret = encrypt(password, file.read())
            path = arguments[3]
            hide(secret, path)
        else:
            print("wrong amount of arguments")

    # discover function
    elif arguments[0] == "discover":
        if len(arguments) == 3:
            secret = discoverSecret(arguments[1])
        elif len(arguments) == 4:
            with open(arguments[2], "rb") as file:
                secret = decrypt(file.read(), discoverSecret(arguments[1]))
        else:
            print("wrong amount of arguments")
            exit()
        if arguments[len(arguments) - 1] == "display":
            try:
                text = secret.decode('utf-8')
                print("text:\n", text)
                exit()
            except UnicodeDecodeError:
                path = input("the data can't be shown as text\nstore it as: ")
        else:
            path = arguments[len(arguments) - 1]
        with open(path, "wb") as file:
            file.write(secret)
        exit()

    else:
        print("invalid arguments\nprint help dialog with \"help\"")

if __name__== "__main__":
    parseInput(sys.argv[1:])
