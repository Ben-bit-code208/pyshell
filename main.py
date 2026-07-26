import datetime
import os
import easy_subprocess


print("PyShell Gestartet. Tippe 'help' für Hilfe")

while True:
    command = input("PyShell> ")

    if command == "help":
        print("""'help' - Zeigt diese Hilfe
                 'time' - zeigt Zeit und Datum
                 'clear' - leert den Bildschirm
                 'echo' - gibt Text aus
                 'exit' - Beendet PyShell
                 'calc' rechnet eine Rechnung aus""")

    elif command == "time":
        print(datetime.datetime.now())

    elif command.startswith("echo") == True:
        print(command[5:])

    elif command == "clear":
        if os.name == "posix":
            os.system("clear")
        else:
            try:
                os.system("cls")
            except Exception as e:
                print(e + os.name)

    elif command.startswith("calc") or command == "calc":
        EasyPopen.read_output(dev-calc)

    elif command == "exit":
        break

    else:
        print("Ungültiger Command, bitte probiere es nochmal")
