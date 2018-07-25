from PIL import Image
from simplecrypt import encrypt, decrypt
import random
import sys
from time import time

keys = []
yes = ["Yes", "Y", "y", "yes", ""]
instructions = ("Help:\n"
                "Usage: ImageSteganography MODE  [Arguments depending on mode]\n"
                "     give no mode and arguments to start in interactive mode\n\n\n"


                "MODES: generate, hide, discover, password, keys\n"
                "     generate:   generate an image with random colored pixels hiding a file or text\n"
                "       arguments \"text: ...\" or PATH TO A FILE you want to hide\n\n"

                "     hide:       hide a file or text in an existing image (overwrites existing image)\n"
                "       arguments: TEXT or FILE, [PASSWORD (file or \"generate\")], IMAGE\n\n"

                "     discover:   discover data from an image and store it\n"
                "       arguments: IMAGE, [PASSWORD], OUTPUT (file or \"display\")\n"
                "     password:   generate a password to use it in the \"hide\" mode\n"
                "     keys:       generate keys to use them in the \"encode\" mode\n")
invalidArguments = "wrong (amount of) arguments\nprint help with  \"ImageSteganography help\""


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
    for c in text:
        pixels += ord(c)
    width = 0
    height = 0
    # generate an approximately 16:9 image
    while width * height < pixels:
        width += 1
        if height / width < 0.53:
            height += 1
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
                if color not in keys:
                    break
            pixel = color
        counter += 1
        for i in range(0, 3):
            image.append(pixel[i])
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
        path = input("choose a png image to hide string in : ")
        text = input("enter the String you want to hide: ")
        if input("encrypt the string? [Y/n]: ") in yes:
            password = generatePassword()
            secret = encrypt(password, text)
        else:
            secret = bytes(text.encode('utf-8'))
        if validateImage(secret, path):
            break
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
        if validateImage(secret, image_path):
            break
    hide(secret, image_path)


def validateImage(secret, path):
    with Image.open(path) as img:
        storage = len(img.tobytes()) - 32
        if len(secret) * 8 > storage :  # space for data, end_byte and indicator
            print("the image is to small to contain the data\nchoose another one with more pixels\nthis image can store ", storage / 8, " Bytes")
            return False
        else:
            return True


def hide(secret, path):
    start = time()
    with Image.open(path) as img:
        image = list(img.tobytes())
        mode = img.mode
        size = img.size

    #store how long the secret is in order to not have to scan or change the hole picture later
    secret_length_binary = "0" * (32-len(bin(len(secret))[2:])) + bin(len(secret))[2:]
    start_bytes = []
    for i in range(0,32,8):
        start_bytes.append(int(secret_length_binary[i:i+8],2))
    secret = start_bytes + list(secret)
    index = 0
    for byte in secret:
        for i in range(8):
            if ((byte << i) & 128) // 128:
                image[index] = image[index] | 1
            else:
                image[index] = image[index] & 254
            index += 1
    print("hidden ", len(secret)-8 ,"Bytes using ", 100 * (index / len(image)), "% of the image")
    Image.frombytes(mode, size, bytes(image)).save(path)
    end = time()
    print("image saved successfully\noperation took {:.2} seconds".format(end-start))


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
            print("text:\n", text)
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
        image = img.tobytes()
    bits = []
    secret = []
    secret_length_binary = ""
    for byte in image[:32]:
        secret_length_binary += str(byte & 1)
    secret_end = int(secret_length_binary,2)*8+32
    for pixel in image[32:secret_end]:
        bits.append(pixel & 1)
    for index, byte in enumerate([bits[i:i + 8] for i in range(0, len(bits), 8)]):
        new_byte = 0
        for bit in byte:
            new_byte = (new_byte << 1) | bit
        secret.append(new_byte)
    print("discovered ", len(secret), "Bytes using ", 100 * (len(bits) / len(image)), "% of the image")
    print("data discovered")
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
            if "text:" in arguments[1]:
                secret = bytes(arguments[1][5:], 'utf-8')
            else:
                with open(arguments[1], "rb") as file:
                    secret = file.read()
            if not secret:
                print("there is no data to hide")
                exit()
            path = arguments[2]
            if validateImage(secret, path):
                hide(secret, path)
        elif len(arguments) == 4:
            if arguments[2] == "generate":
                password = generatePassword()
            else:
                with open(arguments[2], "rb") as file:
                    password = file.read()
            if "text:" in arguments[1]:
                secret = encrypt(password, bytes(arguments[1][5:], 'utf-8'))
                print("encryption successful")
            else:
                with open(arguments[1], "rb") as file:
                    secret = encrypt(password, file.read())
                    print("encryption successful")
            path = arguments[3]
            if validateImage(secret, path):
                hide(secret, path)
        else:
            print(invalidArguments)

    # discover function
    elif arguments[0] == "discover":
        if len(arguments) == 3:
            secret = discoverSecret(arguments[1])
        elif len(arguments) == 4:
            with open(arguments[2], "rb") as file:
                secret = decrypt(file.read(), discoverSecret(arguments[1]))
                print("data decrypted")
        else:
            print(invalidArguments)
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
        if path:
            with open(path, "wb") as file:
                file.write(secret)

    else:
        print(invalidArguments)


if __name__ == "__main__":
    parseInput(sys.argv[1:])
