import re

text = input("Input text: ")

output = re.sub(r"(.)\1*", lambda m: f"{len(m.group(0))}{m.group(1)}", text)

print(output)
print("Compression ratio:", len(text) / len(output))
