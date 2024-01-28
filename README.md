# ZybookAuto
Automatically completes activities on Zybooks, with ability to vary time between answer submission.

Requires `requests` library which can be installed using:
`pip install requests`

*NOTE: This repository is no longer actively maintained. If you encounter any issues feel free to open a merge request and I will review it.*

Instructions: 

Zybooks auto guide:

# WINDOWS:
step one, install python3 https://www.python.org/downloads/windows/ (if you know how to use winget install it with winget instead)

step two, install git https://git-scm.com/download/win (if you know how to use winget install it with winget instead)

step three, open the terminal or command prompt or powershell

step four, `cd C:/folder/to/use` navigate to the folder you will use (optional)

step five, `git.exe clone https://github.com/eglock/ZybookAuto` (getting an error that git.exe is not a valid program? you need to install git!)

step six, `pip.exe install requests` (getting an error that pip.exe is not a valid program? you need to install python3!)

step seven, open the zybookauto folder `cd ZybookAuto`

step eight, using a text editor or IDE, `notepad.exe cfg.py` fill cfg.py with your email and password that you use for zybooks 
`USR = "myemail123@gmail.com" # Username
PWD = "Passw0rd" # Password`

step nine, save by hitting ctrl s or from the menu

step ten, close notepad

step eleven, `python.exe ZybookAuto.py`

step twelve, in the menu (using number keys) select your class and either have it fill out one by one or use the batch option

step thirteen, verify on the zybooks website that it did your zybooks work for you.


# MacOS/Linux/Android/WSL:

remember on unix systems, /foLder/namES/Are/cASe/sensiTive/

step one, install python3 https://www.python.org/downloads/ (maybe use your package manager)

step two, install git https://git-scm.com/download/ (maybe use your package manager)

step three, open the terminal (console)

step four, `cd /folder/to/use` navigate to the folder you will use (optional)

step five, `git clone https://github.com/eglock/ZybookAuto` (getting an error that git is not a valid command? you need to install git!)

step six, `pip install requests` (getting an error that pip is not a valid command? you need to install python3!)

step seven, open the zybookauto folder `cd ZybookAuto`

step eight, using a text editor or IDE, (try using your system notepad and not these terminal programs)`nano cfg.py` fill cfg.py with your email and password that you use for zybooks (optional: if you prefer vi, instead use `vim cfg.py`)
`USR = "myemail123@gmail.com" # Username
PWD = "Passw0rd" # Password`

step nine, save by hitting ctrl x for nano or esc :wq

step ten, make sure you have exited the text editor

step eleven, `python ZybookAuto.py`

step twelve, in the menu (using number keys) select your class and either have it fill out one by one or use the batch option

step thirteen, verify on the zybooks website that it did your zybooks work for you.
