import re
from fabric.colors import green, red, yellow
from fabric.network import prompt_for_password


def print_green(s):
    print(green(s))


def print_red(s):
    print(red(s))


def print_yellow(s):
    print(yellow(s))


def password_prompt(msg='Set password', min_length=8, max_length=40):
    pwd = None
    while True:
        pwd = prompt_for_password(msg)
        if not min_length <= len(pwd) <= max_length:
            print_red('Password must be from 8 to 40 symbols. Try again.')
            continue
        if not re.findall(r'^[\w\$\^\*\(\)\{\}\[\]\?!@#%&<>:;/+-=]+$', pwd, re.U | re.I):
            print_red('Password has unallowed symbol. Try again.')
            continue
        pwd_confirm = prompt_for_password('Confirm password')
        if pwd != pwd_confirm:
            print_red("Passwords aren't matching. Try again.")
            continue
        break
    return pwd


# # # COMMANDS # # #
