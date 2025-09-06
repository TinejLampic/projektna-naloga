import csv
import os
import requests
import re


#pridobitev podatkov iz spleta

nepremicnine_frontpage_url = "https://www.bolha.com/hitro-iskanje?categoryIds%5B%5D=" \
"9579%2C9580%2C10920&geo%5Blat%5D=46.044463358034&geo%5Blng%5D=14.485205411911&geo%5BautoComplete%5D=Petrol+-" \
"+Ljubljana+-+Tr%C5%BEa%C5%A1ka+44%2C+Tr%C5%BEa%C5%A1ka+cesta+44%2C+1000+Ljubljana%2C+Slovenija&geo%5Bradius%5D=100" 

nepremicnine_directory = 'podatki'  

frontpage_filename = 'nepremicnine.html'

csv_filename = 'nepremicnine.csv'


def download_url_to_string(url):   #funkcija v obliki niza vrne vsebino spletne strani
    try:
        # del kode, ki morda sproži napako
        headers = {"User-Agent": "Chrome/139.0.7258.139"}     #da spletna stran ne 'misli' da smo bot
        page_content = requests.get(url, headers=headers,).text   
    except requests.exceptions.RequestException:
        # koda, ki se izvede pri napaki
        print("Spletna stran ni dosegljiva.")
    return page_content


def save_string_to_file(text, directory, filename):   #vrednost paprametra 'text' zapiše v novo ustvarjeno datoteko

    os.makedirs(directory, exist_ok=True)
    path = os.path.join(directory, filename)
    with open(path, 'w', encoding='utf-8') as file_out:
        file_out.write(text)
    return None


def save_multiple_pages(base_url, directory, filename_prefix, num_pages=200):   #funkcija, ki shrani strani, vsako v svojo html datoteko
    all_content = ""
    for page_num in range(1, num_pages + 1):
        url = f"{base_url}?page={page_num}"
        print(f"Prenašam: {url}")
        text = download_url_to_string(url)
        save_string_to_file(text, directory, f"{filename_prefix}_{page_num}.html")
        all_content += text
    return all_content


# Po pridobitvi podatkov jih želimo obdelati.

def read_file_to_string(directory, filename):   #odpremo datoteko za branje
    """Funkcija vrne celotno vsebino datoteke "directory"/"filename" kot niz."""
    os.makedirs(directory, exist_ok=True)
    path = os.path.join(directory, filename)
    with open(path, 'r', encoding='utf-8') as file_in:
        text = file_in.read()
    return text
    
def page_to_ads(page_content):   #funkcija sprejme niz in poišče posamezne oglase, ki jih nato vrne v obliki seznama
    return re.findall(r'<article class="entity-body cf">(.*?)</article>', page_content, flags=re.DOTALL)    
    
    

def get_dict_from_ad_block(block):    #funkcija za posamezen oglas izlušči željene podatke in jih vrne v slovarju
    lokacija = re.search(r'Lokacija: </span>(.*)<br />', block)
    povrsina = re.search(r'Bivalna površina:\s*([\d,\.]+)\s*m2', block)
    datum = re.search(r'pubdate="pubdate">(.*)\.</time>', block)
    razdalja = re.search(r'Razdalja:\s*([\d,\.]+\s*(?:m|km))', block)
    cena = re.search(r'<strong class="price price--hrk">(.*)</strong>', block, flags=re.DOTALL)

    if lokacija == None or povrsina == None or datum == None or razdalja == None or cena == None:   #poskrbi, da ne upoštevamo oglasa, pri katerem kakšen podatek majnka
        print("Napaka v bloku:", block)
        return None

    return {
        'lokacija': lokacija.group(1),
        'povrsina': povrsina.group(1) + " m2",
        'cena': re.sub(r'&nbsp;<span class="currency">€</span>', ' €', cena.group(1).strip()),
        'razdalja': re.sub(r'(m|km)$', '', razdalja.group(1)).strip() + ' km',
        'datum': datum.group(1)
    }



def ads_from_files(directory, filename_prefix, num_pages):   #funkcija prebere posamezne strani oglasov (Html datoteke), iz njih izlušči bloke z oglasi, jih pretvori v slovarje s podatki in vse skupaj združi v seznam oglasov
    ads = []
    for page_num in range(1, num_pages + 1):
        filename = f"{filename_prefix}_{page_num}.html"
        page_content = read_file_to_string(directory, filename)
        blocks = page_to_ads(page_content)
        page_ads = [get_dict_from_ad_block(block) for block in blocks]
        ads.extend([ad for ad in page_ads if ad is not None])
    return ads


# Obdelane podatke želimo sedaj shraniti.

def write_csv(fieldnames, rows, directory, filename):
    os.makedirs(directory, exist_ok=True)   #ustvari mapo, če ne obstaja
    path = os.path.join(directory, filename)       #sestavi pot
    with open(path, 'w', encoding='utf-8', newline='') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()       #zapiše imena stolpcev
        for row in rows:
            writer.writerow(row)   #v vrstici bodo podatki o eni nepremičnini
    return




def write_nepremicnine_ads_to_csv(ads, directory, filename):   #funkcija, ki zapiše neprazen seznam slovarjev v csv datoteko
    assert ads and (all(j.keys() == ads[0].keys() for j in ads))    #assert sproži napako, če pogoj ni izpolnjen (če je seznam oglasov definiran in če imajo vsi slovarji v seznamu enake ključe)
    fieldnames = list(ads[0].keys())                                #ključe spremenimo v seznam, to so imena stolpceb
    write_csv(fieldnames, ads, directory, filename)


# Celoten program poženemo v glavni funkciji

def main(redownload=True, reparse=True):    #ta funkcija izvede celoten del pridobivanja podatkov

    if redownload:   # Najprej v lokalno datoteko prenesemo strni
        save_multiple_pages(nepremicnine_frontpage_url, nepremicnine_directory, "nepremicnine", num_pages=200)

    if reparse:    #iz datotek prebere podatke, jih uredi in shrani v csv
        num_pages = 200 
        ads = ads_from_files(nepremicnine_directory, "nepremicnine", num_pages)
        write_nepremicnine_ads_to_csv(ads, nepremicnine_directory, csv_filename)

if __name__ == '__main__':    #če datoteko vključimo drugam, se nam main() ne izvede
    main(True)

