import requests
import bs4
import time
import os

base_url = "https://pastpapers.papacambridge.com/"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
}
cookie_str = "tk_or=%22%22; tk_r3d=%22%22; tk_lr=%22%22; userboardid=1; _gid=GA1.2.2040563971.1742790169; _ga_Q40X8VVS1Y=GS1.1.1742790168.1.0.1742790171.0.0.0; _ga=GA1.1.202476268.1742788929; __cflb=02DiuFfZyZiBjdK5v3X1q4kGWbDABQnpzB2kpYTfr7hxp; cf_clearance=2LIeyxKmV1yyZ3MVWioFkxiBt97rbcxW4YIdBHpHUD0-1742872197-1.2.1.1-RRN1sxNaO__imvLd4aKmFkignq2xA7tNdT6qT46ePGC_UxduwJH62qipaXEkK.ZK7tjCEurqxssvcY5K3ccG0rd8n0x3RYri7fr2ndtIS2STG3_DHqKr54wRM7P4_C0FNNhmM48Q6Yzo98VsYS9.07TYHDKJEhgqHf6.RvoJmy8KyPd74.kqSgKn4HNLaoi27jUK3wqoLgDJG3shLC3fMG7FWm1dDKecgy6qZuSS8j2qAea6UD9fyVMlxmlHopaBX8vKJTxr.fmW.kNvbd1jUjiKLJ5h2ed8wM6ISt5ImpIKPVONDqO9XkSqOWWPJEitDrK7bmwW3fmjcZdVuJPeEYONiZcRdxldNxnjhh.w6tc; _ga_FKQM30NY3V=GS1.1.1742870554.4.1.1742872957.0.0.0"
cookies = {
    k.strip(): v.strip()
    for k, v in (item.split("=", 1) for item in cookie_str.split(";"))
}


def get_all_paper(additional_url):
    url = base_url + "papers/caie/" + additional_url
    session = requests.Session()
    # Set the session cookies
    session.cookies.update(cookies)
    # Set the session headers
    session.headers.update(headers)
    response = session.get(url, headers=headers)
    soup = bs4.BeautifulSoup(response.text, "html.parser")

    if response.status_code != 200:
        print(f"[{response.status_code}]Failed to retrieve {url}")
        return False
    # get all the <a> with class kt-widget4__title kt-nav__link-text cursor colorgrey stylefont fonthover
    links = soup.find_all(
        "a",
        class_="kt-widget4__title kt-nav__link-text cursor colorgrey stylefont fonthover",
    )
    # get the href attribute of each <a>
    hrefs = [link.get("href") for link in links]
    os.makedirs(f"papers\\{additional_url}", exist_ok=True)
    # access the hrefs
    for href in hrefs:
        url = base_url + href
        print(f"Accessing {url}")
        response = session.get(url, headers=headers)
        if response.status_code != 200:
            print(f"Failed to retrieve {url}")
            continue
        soup = bs4.BeautifulSoup(response.text, "html.parser")
        # get all the <a> with property download
        download_links = soup.find_all("a", download=True)
        # get the href attribute of each <a>
        download_hrefs = [link.get("href") for link in download_links]
        for download_href in download_hrefs:
            if not (download_href.startswith("download_file.php?files=")):
                print(f"Invalid download link: {download_href}")
                continue
            download_url = download_href[len("download_file.php?files=") :]
            print(f"Downloading {download_url}")
            filename = download_url.split("/")[-1]
            if not ("ms" in filename or "qp" in filename):
                continue
            # check if the file already exists
            filepath = os.path.join(f"papers\\{additional_url}", filename)
            if os.path.exists(filepath):
                print(f"{filename} already exists, skipping")
                continue
            # download the file
            response = session.get(
                download_url,
                headers=headers,
            )
            if response.status_code != 200:
                print(f"Failed to download {download_url}")
                continue
            # save the file
            with open(filepath, "wb") as f:
                f.write(response.content)


if __name__ == "__main__":
    input_url = input("Enter the URL")
    if not input_url:
        print("No URL provided")
        exit(1)
    get_all_paper(input_url)
