# to find non ascii char

with open('Exercise-1.py') as fp:
        for i, line in enumerate(fp):
            if "\xe2" in line:
                print(i), repr(line)