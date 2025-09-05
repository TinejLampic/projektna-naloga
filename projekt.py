import csv
import os
import requests
import re


#pridobitev podatkov iz spleta

# definirajte URL glavne strani bolhe za oglase z mačkami
cats_frontpage_url = "https://www.nepremicnine.net/nepremicnine.html?last=31"   #bolje da imena konstant pišemo z velikimi črkami
# mapa, v katero bomo shranili podatke
cat_directory = 'podatki'
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
        headers = {"User-agent": "Chrome/136.0.7103.114"}     #da spletna stran ne misli da smo bot:  Chrome/verzija chroma
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


def save_frontpage(page, directory, filename):
    """Funkcija shrani vsebino spletne strani na naslovu "page" v datoteko
    "directory"/"filename"."""
    text = download_url_to_string(page)  #to da iz spleta, spodnjo iz mape
    #text = read_file_to_string(directory, 'stran.html')
    save_string_to_file(text, directory, filename)
    return text



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
    return re.findall(r'<div class="property-box mt-4 mt-md-0" itemprop="item" itemscope="" itemtype="http://schema.org/Offer">(.*?)</div></div></div>', page_content, flags=re.DOTALL)    
    # *? - da se ustavi res samo pri koncu prvega oglasa / flags... da pika(.) res pomeni vse (drugace ne zavzame naslednje vrstice)
    


# Definirajte funkcijo, ki sprejme niz, ki predstavlja oglas, in izlušči
# podatke o imenu, lokaciji, datumu objave in ceni v oglasu.

def get_dict_from_ad_block(block):
    """Funkcija iz niza za posamezen oglasni blok izlušči podatke o imenu, ceni
    in opisu ter vrne slovar, ki vsebuje ustrezne podatke."""
    namen = re.search(r'(Prodaja|Oddaja|Najem|Nakup):', block)
    objekt = re.search(r'(?:Prodaja|Oddaja|Najem|Nakup):\s*([^,]+)', block)
    lokacija = re.search(r'<h2>(.*)</h2>', block)
    povrsina = re.search(r'<li><img .*?>([\d,\.]+\s*m)<sup>2</sup></li>', block)
    leto = re.search(r'<li><img .*?>(\d{4})</li>', block)
    cena = re.search(r'<h6 class="">(.*)</h6>', block, flags=re.DOTALL)

    if namen == None or objekt == None or lokacija == None or povrsina == None or leto == None or cena == None:
        print("Napaka v bloku:", block)
        return None



    return {
        'objekt': objekt.group(1),
        'namen': namen.group(1),
        'lokacija': lokacija.group(1),
        'povrsina': povrsina.group(1),
        'cena': re.sub(r'&nbsp;<span class="currency">€</span>', ' €', cena.group(1).strip()),
        'leto': leto.group(1)
    }


# Definirajte funkcijo, ki sprejme ime in lokacijo datoteke, ki vsebuje
# besedilo spletne strani, in vrne seznam slovarjev, ki vsebujejo podatke o
# vseh oglasih strani.


def ads_from_file(filename, directory):
    """Funkcija prebere podatke v datoteki "directory"/"filename" in jih
    pretvori (razčleni) v pripadajoč seznam slovarjev za vsak oglas posebej."""
    page_content = read_file_to_string(directory, filename)
    blocks = page_to_ads(page_content)
    ads = [get_dict_from_ad_block(block) for block in blocks]
    return [ad for ad in ads if ad != None]

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


def write_cat_ads_to_csv(ads, directory, filename):
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
        save_frontpage(cats_frontpage_url, cat_directory, frontpage_filename)

    # Iz lokalne (html) datoteke preberemo podatke
    # Podatke preberemo v lepšo obliko (seznam slovarjev)
    # Podatke shranimo v csv datoteko
    if reparse:
        ads = ads_from_file(frontpage_filename, cat_directory)
        write_cat_ads_to_csv(ads, cat_directory, csv_filename)

if __name__ == '__main__':    #če datoteko vključimo drugam, se nam main() ne izvede
    main(redownload=True)

