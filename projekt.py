import csv
import os
import requests
import re


#pridobitev podatkov iz spleta

# definirajte URL glavne strani bolhe za oglase z mačkami
realestate_frontpage_url = "https://www.bolha.com/hitro-iskanje?categoryIds%5B%5D=9579%2C9580%2C10920&geo%5Blat%5D=46.044463358034&geo%5Blng%5D=14.485205411911&geo%5BautoComplete%5D=Petrol+-+Ljubljana+-+Tr%C5%BEa%C5%A1ka+44%2C+Tr%C5%BEa%C5%A1ka+cesta+44%2C+1000+Ljubljana%2C+Slovenija&geo%5Bradius%5D=100"   #bolje da imena konstant pišemo z velikimi črkami
# mapa, v katero bomo shranili podatke
realestate_directory = 'podatki'
# ime datoteke v katero bomo shranili glavno stran
frontpage_filename = 'nepremicnine.html'
# ime CSV datoteke v katero bomo shranili podatke
csv_filename = 'nepremicnine.csv'


def download_url_to_string(url):
    """Funkcija kot argument sprejme niz in poskusi vrniti vsebino te spletne
    strani kot niz. V primeru, da med izvajanje pride do napake vrne None.
    """
    try:
        # del kode, ki morda sproži napako
        headers = {"User-Agent": "Chrome/139.0.7258.139"}     #da spletna stran ne misli da smo bot:  Chrome/verzija chroma
        page_content = requests.get(url, headers=headers,).text   #v terminal napišemo: python -m pip install requests
    except requests.exceptions.RequestException:
        # koda, ki se izvede pri napaki
        # dovolj je če izpišemo opozorilo in prekinemo izvajanje funkcije
        print("Spletna stran ni dosegljiva.")
    # nadaljujemo s kodo če ni prišlo do napake
    return page_content


def save_string_to_file(text, directory, filename):
    """Funkcija zapiše vrednost parametra "text" v novo ustvarjeno datoteko
    locirano v "directory"/"filename", ali povozi obstoječo. V primeru, da je
    niz "directory" prazen datoteko ustvari v trenutni mapi.
    """
    os.makedirs(directory, exist_ok=True)
    path = os.path.join(directory, filename)
    with open(path, 'w', encoding='utf-8') as file_out:
        file_out.write(text)
    return None


# Definirajte funkcijo, ki prenese glavno stran in jo shrani v datoteko.


def save_multiple_pages(base_url, directory, filename_prefix, num_pages=200):
    """Shrani več zaporednih strani (npr. 10 strani oglasov) v mape."""
    all_content = ""
    for page_num in range(1, num_pages + 1):
        url = f"{base_url}?page={page_num}"
        print(f"Prenašam: {url}")
        text = download_url_to_string(url)
        save_string_to_file(text, directory, f"{filename_prefix}_{page_num}.html")
        all_content += text
    return all_content



###############################################################################
# Po pridobitvi podatkov jih želimo obdelati.
###############################################################################


def read_file_to_string(directory, filename):   #odpremo datoteko za branje
    """Funkcija vrne celotno vsebino datoteke "directory"/"filename" kot niz."""
    os.makedirs(directory, exist_ok=True)
    path = os.path.join(directory, filename)
    with open(path, 'r', encoding='utf-8') as file_in:
        text = file_in.read()
    return text
    


# Definirajte funkcijo, ki sprejme niz, ki predstavlja vsebino spletne strani,
# in ga razdeli na dele, kjer vsak del predstavlja en oglas. To storite s
# pomočjo regularnih izrazov, ki označujejo začetek in konec posameznega
# oglasa. Funkcija naj vrne seznam nizov.


def page_to_ads(page_content):
    """Funkcija poišče posamezne oglase, ki se nahajajo v spletni strani in
    vrne seznam oglasov."""
    return re.findall(r'<article class="entity-body cf">(.*?)</article>', page_content, flags=re.DOTALL)    
    # *? - da se ustavi res samo pri koncu prvega oglasa / flags... da pika(.) res pomeni vse (drugace ne zavzame naslednje vrstice)
    


# Definirajte funkcijo, ki sprejme niz, ki predstavlja oglas, in izlušči
# podatke o imenu, lokaciji, datumu objave in ceni v oglasu.

def get_dict_from_ad_block(block):
    """Funkcija iz niza za posamezen oglasni blok izlušči podatke o imenu, ceni
    in opisu ter vrne slovar, ki vsebuje ustrezne podatke."""
    lokacija = re.search(r'Lokacija: </span>(.*)<br />', block)
    povrsina = re.search(r'Bivalna površina:\s*([\d,\.]+)\s*m2', block)
    datum = re.search(r'pubdate="pubdate">(.*)\.</time>', block)
    razdalja = re.search(r'Razdalja:\s*([\d,\.]+\s*(?:m|km))', block)
    cena = re.search(r'<strong class="price price--hrk">(.*)</strong>', block, flags=re.DOTALL)

    if lokacija == None or povrsina == None or datum == None or razdalja == None or cena == None:
        print("Napaka v bloku:", block)
        return None



    return {
        'lokacija': lokacija.group(1),
        'povrsina': povrsina.group(1) + " m2",
        'cena': re.sub(r'&nbsp;<span class="currency">€</span>', ' €', cena.group(1).strip()),
        'razdalja': re.sub(r'(m|km)$', '', razdalja.group(1)).strip() + ' km',
        'datum': datum.group(1)
    }


# Definirajte funkcijo, ki sprejme ime in lokacijo datoteke, ki vsebuje
# besedilo spletne strani, in vrne seznam slovarjev, ki vsebujejo podatke o
# vseh oglasih strani.


def ads_from_files(directory, filename_prefix, num_pages):
    ads = []
    for page_num in range(1, num_pages + 1):
        filename = f"{filename_prefix}_{page_num}.html"
        page_content = read_file_to_string(directory, filename)
        blocks = page_to_ads(page_content)
        page_ads = [get_dict_from_ad_block(block) for block in blocks]
        ads.extend([ad for ad in page_ads if ad is not None])
    return ads

###############################################################################
# Obdelane podatke želimo sedaj shraniti.
###############################################################################


def write_csv(fieldnames, rows, directory, filename):
    """
    Funkcija v csv datoteko podano s parametroma "directory"/"filename" zapiše
    vrednosti v parametru "rows" pripadajoče ključem podanim v "fieldnames"
    """
    os.makedirs(directory, exist_ok=True)
    path = os.path.join(directory, filename)
    with open(path, 'w', encoding='utf-8', newline='') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)   #v vrstici bodo podatki o eni nepremičnini
    return


# Definirajte funkcijo, ki sprejme neprazen seznam slovarjev, ki predstavljajo
# podatke iz oglasa mačke, in zapiše vse podatke v csv datoteko. Imena za
# stolpce [fieldnames] pridobite iz slovarjev.


def write_realestate_ads_to_csv(ads, directory, filename):
    """Funkcija vse podatke iz parametra "ads" zapiše v csv datoteko podano s
    parametroma "directory"/"filename". Funkcija predpostavi, da so ključi vseh
    slovarjev parametra ads enaki in je seznam ads neprazen."""
    # Stavek assert preveri da zahteva velja
    # Če drži se program normalno izvaja, drugače pa sproži napako
    # Prednost je v tem, da ga lahko pod določenimi pogoji izklopimo v
    # produkcijskem okolju
    assert ads and (all(j.keys() == ads[0].keys() for j in ads))    #assert sproži napako, če pogoj ni izpolnjen (če je seznam oglasov definiran in če imajo vsi slovarji v seznamu enake ključe)
    fieldnames = list(ads[0].keys())                                #ključe spremenimo v seznam
    write_csv(fieldnames, ads, directory, filename)


# Celoten program poženemo v glavni funkciji

def main(redownload=True, reparse=True):
    """Funkcija izvede celoten del pridobivanja podatkov:
    1. Oglase prenese iz bolhe
    2. Lokalno html datoteko pretvori v lepšo predstavitev podatkov
    3. Podatke shrani v csv datoteko
    """
    # Najprej v lokalno datoteko shranimo glavno stran
    if redownload:
        save_multiple_pages(realestate_frontpage_url, realestate_directory, "nepremicnine", num_pages=200)

    # Iz lokalne (html) datoteke preberemo podatke
    # Podatke preberemo v lepšo obliko (seznam slovarjev)
    # Podatke shranimo v csv datoteko
    if reparse:
        num_pages = 200  # prilagodi, koliko strani želiš
        ads = ads_from_files(realestate_directory, "nepremicnine", num_pages)
        write_realestate_ads_to_csv(ads, realestate_directory, csv_filename)

if __name__ == '__main__':    #če datoteko vključimo drugam, se nam main() ne izvede
    main(True)

