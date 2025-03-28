rle_str = lambda s: "".join(
    f"{s[i]}{len(list(filter(lambda x: x == s[i], s[i:])))}"
    for i in range(len(s))
    if i == 0 or s[i] != s[i - 1]
)
