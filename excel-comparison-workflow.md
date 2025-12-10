# Excel Comparison Workflow - Simphony to MC Name Mapping

## Overview
Compare two Excel files after mapping names from Simphony format to MC format.

- **Excel 1:** Column D = name, Column C = price
- **Excel 2:** Column A = name, Column B = price

---

## Workflow Steps

### Step 1: Set Variable - Name Mapping Dictionary
**Node:** `Set Variable`
- Variable Name: `name_mapping`
- Value:
```python
{
    "GJ ADANA SEYHAN": "GJ ADANA SEYHAN FRANCHISE",
    "GJ ADIYAMAN": "ADIYAMAN PARK FRANCHİSE",
    "GJ AFYON DINAR": "AFYON DINAR FRANCHISE",
    "GJ AFYON WATERMALL": "AFYON WATERMALL FRANCHİSE",
    "GJ AIRPORT AVM": "AIRPORT OUTLET FRANCHİSE",
    "GJ AKSARAY": "AKSARAY FRANCHISE",
    "GJ AKYAKA PARK AVM": "AKYAKAPARK FRANCHISE",
    "GJ AKYAZI GUNEY": "KMO AKYAZI GÜNEY FRANCHİSE",
    "GJ AKYAZI KUZEY": "KMO AKYAZI KUZEY FRANCHİSE",
    "GJ ALANYA GAZIPASA": "ALANYA GAZİPAŞA FRANCHİSE",
    "GJ ALANYA YEKTA MALL": "ALANYA YEKTA MALL FRANCHİSE",
    "GJ ANKARA CEPA": "ANKARA CEPA FRANCHİSE",
    "GJ ANKARA INCEK": "ANKARA İNCEK FRANCHİSE",
    "GJ ANKARA KASMIR": "ANKARA KAŞMİR AVM FRANCHİSE",
    "GJ ANKARA METROMALL AVM": "ANKARA METROMALL FRANCHISE",
    "GJ ANKARA NEXT LEVEL": "ANKARA NEXT LEVEL FRANCHISE",
    "GJ ANTALYA AGORA": "GJ ANTALYA AGORA AVM FRANCHİSE",
    "GJ ANTALYA ALANYA": "ALANYA FRANCHISE",
    "GJ ANTALYA ALANYA CADDE": "ALANYA CADDE FRANCHISE",
    "GJ ANTALYA KAS": "ANTALYA KAŞ FRANCHİSE",
    "GJ ANTALYA KUNDU": "ANTALYA KUNDU FRANCHİSE",
    "GJ ANTALYA LAND OF LEGENDS": "ANTALYA LAND OF LEGENDS FRANCHİSE",
    "GJ ANTALYA LARA": "ANTALYA LARA FRANCHİSE",
    "GJ ARDICLI": "ESENYURT MEYDAN ARDICLI FRANCHISE",
    "GJ ARNAVUTKOY LEVANDER": "ARNAVUTKÖY LEVANDER",
    "GJ ATAKENT MOSTAR": "ATAKENT MOSTAR FRANCHİSE",
    "GJ ATASEHIR GOLF KULUBU": "ATASEHIR GOLF CLUB FRANCHISE",
    "GJ ATLASPARK": "ATLASPARK FRANCHİSE",
    "GJ ATLAS UNI": "ATLAS UNIVERSITESI FRANCHISE",
    "GJ AVCILAR": "AVCILAR FRANCHISE",
    "GJ AYDIN DIDIM": "DIDIM AYDIN FRANCHISE",
    "GJ AYDIN UNIVERSITESI": "AYDIN UNİVERSTESİ FRANCHISE",
    "GJ AYVALIK": "AYVALIK FRANCHİSE",
    "GJ BAGCILAR": "NANDA YAPI BAĞCILAR FRANCHİSE",
    "GJ BAGCILAR MERKEZ": "BAĞCILAR FRANCHİSE",
    "GJ BAKIRKOY (INCIRLI ALTNBS UNI)": "BAKIRKOY ZUHURATBABA FRANCHISE",
    "GJ BALIKESIR": "BALIKESIR FRANCHISE",
    "GJ BANDIRMA": "BANDIRMA BANPET OPET FRANCHİSE",
    "GJ BASAKSEHIR METROKENT": "BAŞAKŞEHİR METROKENT FRANCHİSE",
    "GJ BATMAN": "BATMAN PETROL CİTY FRANCHİSE",
    "GJ BAYRAMPASA FORUM": "FORUM PLAZA FRANCHİSE",
    "GJ BEYKENT": "BEYLIKDUZU BEYKENT FRANCHISE",
    "GJ BEYLIKDUZU COUNTRY": "BEYLİKDÜZÜ DEMİR COUNTRY FRANCHİSE",
    "GJ BEYLIKDUZU ECRIN PARK": "BEYLİKDÜZÜ ECRİNPARK FRANCHİSE",
    "GJ BEYLIKDUZU MIGROS": "BEYLIKDUZU MIGROS-FRANCHISE",
    "GJ BEYLUKDUZU VADI LOCA": "BEYLİKDÜZÜ VADİ LOCA FRANCHİSE",
    "GJ BILECIK": "BILECIK FRANCHISE",
    "GJ BINGOL PARK AVM": "BİNGÖL MİLİAMALL FRANCHİSE",
    "GJ BOLU": "GJ BOLU FRANCHİSE",
    "GJ BOLU ABANT": "BOLU ABANT FRANCHİSE",
    "GJ BOLU HIGHWAY": "BOLU HIGHWAY OUTLET FRANCHİSE",
    "GJ BOLU KILICARSLAN": "BOLU KILICARSLAN FRANCHISE",
    "GJ BURDUR": "BURDUR FRANCHISE",
    "GJ BURSA ASOUTLET": "BURSA AS OUTLET FRANCHISE",
    "GJ BURSA EKER": "BURSA EKER FRANCHISE",
    "GJ BURSA OKSIJEN AVM 14 A": "OKSİJEN 14A FRANCHİSE",
    "GJ BURSA OKSIJEN AVM 14 B": "OKSİJEN 14B FRANCHİSE",
    "GJ BURSA OKSIJEN AVM B37A": "OKSİJEN 37A FRANCHİSE",
    "GJ BURSA OKSIJEN AVM B37B": "OKSİJEN 37B FRANCHİSE",
    "GJ BURSA SURYAPI MARKA AVM": "BURSA MARKA AVM FRANCHİSE",
    "GJ CANKIRI": "ÇANKIRI FRANCHİSE",
    "GJ CATALCA": "CATALCA FRANCHISE",
    "GJ CEKMEKOY METRO": "CEKMEKOY METRO FRANCHISE",
    "GJ CEKMEKOY ORMANKOY": "ÇEKMEKÖY ORMANKÖY FRANCHİSE",
    "GJ CENNET-2": "CENNET 2 FRANCHISE",
    "GJ CENNET -3": "CENNET 3 FRANCHİSE",
    "GJ CERKEZKOY": "CERKEZKÖY FRANCHİSE",
    "GJ CEVIZLIBAG": "CEVİZLİBAĞ FRANCHİSE",
    "GJ CORLU": "CORLU TREND ARENA FRANCHISE",
    "GJ CORUM": "ÇORUM FRANCHISE",
    "GJ CUKUROVA AIRPORT": "CUKUROVA HAVALIMANI FRANCHISE",
    "GJ DALAMAN DUTY FREE": "DALAMAN AIRPORT DUTYFREE FRANCHİSE",
    "GJ DALAMAN MERKEZ": "MUGLA DALAMAN MERKEZ FRANCHISE",
    "GJ DARICA KOCAELI": "DARICA FRANCHİSE",
    "GJ DARULACEZE": "DARÜLACEZE FRANCHİSE",
    "GJ DENIZLI HORIZON": "GJ DENIZLI HORIZON AVM FRANCHISE",
    "GJ DEPOSITE IKITELLI": "DEPOSITE OUTLET FRANCHİSE",
    "GJ DIYARBAKIR": "DIYARBAKIR 75 CADDE FRANCHİSE",
    "GJ DUZCE": "DÜZCE FRANCHİSE",
    "GJ ELAZIG": "ELAZIG ELYSIUM PARK FRANCHISE",
    "GJ ERDEK MOBIL TRACK": "BALIKESIR ERDEK COFFEE TRUCK",
    "GJ ESEN HOTEL": "SIRKECI ESEN HOTEL FRANCHISE",
    "GJ ESENKENT": "BAHCESEHIR ESENKENT FRANCHISE",
    "GJ ESENLER": "ESENLER ATISALANI FRANCHISE",
    "GJ ESENYURT VETROCITY": "VETROCITY FRANCHISE",
    "GJ EYUPPARK": "EYUP PARKAVM FRANCHISE",
    "GJ FETHIYE CALIS": "FETHİYE ÇALİS FRANCHİSE",
    "GJ FETHIYE ORKA OTEL": "FETHİYE ORKA FRANCHİSE",
    "GJ FIKIRTEPE OPTIMIST": "FİKİRTEPE OPTİMİST FRANCHİSE",
    "GJ FIRUZE KONAKLARI": "FİRUZE KONAKLARI FRANCHİSE",
    "GJ GEBZE": "GEBZE FRANCHİSE",
    "GJ GIRESUN": "GIRESUN FRANCHİSE",
    "GJ GOKTURK": "GOKTURK FRANCHISE",
    "GJ GOKTURK YENI": "GOKTURK 2 FRANCHISE",
    "GJ GORUKLE BURSA": "BURSA GÖRÜKLE FRANCHISE",
    "GJ GOZTEPE CLASS PETROL": "GÖZTEPE CLASS PETROL FRANCHİSE",
    "GJ GUNESLI": "GÜNEŞLİ FRANCHİSE",
    "GJ HALIC UNIVERSITESI": "HALİÇ ÜNİVERSİTESİ FRANCHISE",
    "GJ HALKALI ASNUR AVM": "HALKALI ASNUR AVM FRANCHİSE",
    "GJ HALKALI ATAKENT": "ATAKENT AVRUPA KONUTLARI FRANCHİSE",
    "GJ HALKALI BIZIM MAH": "HALKALI BİZİM MAHALLE FRANCHİSE",
    "GJ HATAY DORTYOL": "HATAY DÖRTYOL FRANCHİSE",
    "GJ IDEALIST PARK": "IDEALIST PARK FRANCHISE",
    "GJ IGDIR": "IGDIR FRANCHISE",
    "GJ ISPARTA IYASPARK": "ISPARTA IYAŞPARK FRANCHISE",
    "GJ ISPARTA IYASPARK OUTLET": "ISPARTA BULVAR FRANCHISE",
    "GJ ISPARTA IYASPARK SHOPPING": "ISPARTA IYASPARK SHOPPING CENTER FRANCHıSE",
    "GJ ISPARTA MEYDAN": "ISPARTA MEYDAN FRANCHİSE",
    "GJ ISPARTA SULEYMAN DEMIREL UNI": "ISPARTA S.DEMIREL UNI FRANCHISE",
    "GJ ISTANBUL AKZIRVE": "AKZİRVE FRANCHİSE",
    "GJ ISTANBUL ANADOLU HISARI": "ANADOLU HİSARI FRANCHİSE",
    "GJ ISTANBUL AQUA FLORYA": "AQUA FLORYA FRANCHISE",
    "GJ ISTANBUL ARENAPARK": "ARENA PARK AVM FRANCHİSE",
    "GJ ISTANBUL BESYOL": "BESYOL 2 FRANCHİSE",
    "GJ ISTANBUL BIZ CEVAHIR": "ALİBEYKÖY BİZ CEVAHİR FRANCHİSE",
    "GJ ISTANBUL BUYUKCEKMECE SAHIL": "BÜYÜKÇEKMECE SAHİL FRANCHİSE",
    "GJ ISTANBUL CAPACITY": "CAPACITY FRANCHISE",
    "GJ ISTANBUL HAVALIMANI": "ISTANBUL HAVALIMANI IC HATLAR FRANCHISE",
    "GJ ISTANBUL KAYASEHIR KUZEYYAKA": "KAYAŞEHİR FRANCHİSE",
    "GJ ISTANBUL NATO": "GJ ÇENGELKÖY NATO YOLU FRANHCİSE",
    "GJ ISTANBUL YAKUPLU": "YAKUPLU İNMARİ FRANCHİSE",
    "GJ ISTANBUL YESILKOY": "YEŞİLKÖY FRANHCİSE",
    "GJ ISTMARINA": "IST MARİNA FRANCHİSE",
    "GJ IZMIR AGORA": "GJ IZMIR AGORA FRANCHİSE",
    "GJ IZMIR BAYRAKLI": "IZMIR LIDER CENTRIO FRANCHISE",
    "GJ IZMIR MAVIBAHCE": "IZMIR MAVIBAHCE FRANCHISE",
    "GJ IZMIR OPTIMUM": "IZMIR OPTIMUM FRANCHISE",
    "GJ IZMIR WESTPARK": "IZMIR WESTPARK FRANCHISE",
    "GJ IZMIT MARS AVM": "KOCAELI MARS AVM FRANCHISE",
    "GJ KADIKOY": "KADIKÖY ÇARŞI FRANCHİSE",
    "GJ KADIR HAS CENTER": "KADIRHASCENTER FRANCHISE",
    "GJ KAPADOKYA": "NEVSEHIR UCHISAR FRANCHISE",
    "GJ KARTAL MANZARA ADALAR": "KARTAL MANZARA ADALAR FRANCHİSE",
    "GJ KAVACIK YENI": "KAVACIK FSM FRANCHISE",
    "GJ KAYSERI MELIKGAZI": "KAYSERİ MELİKGAZİ FRANCHİSE",
    "GJ KAYSERI TALAS": "KAYSERI TALAS FRANCHISE",
    "GJ KENT UNIVERSITESI": "İSTANBUL KENT UNİVERSİTESİ FRANCHİSE",
    "GJ KILIS": "KİLİS FRANCHİSE",
    "GJ KIRKLARELI": "KIRKLARELİ MİNİMALL FRANCHİSE",
    "GJ KUTAHYA": "KUTAHYA FRANCHISE",
    "GJ LENS ISTANBUL": "LENS İSTANBUL FRANCHISE",
    "GJ LULEBURGAZ MINIMALL AVM": "LÜLEBURGAZ FRANCHİSE",
    "GJ MAHMUTBEY METRO": "MAHMUTBEY METRO FRANCHISE",
    "GJ MALATYA": "MALATYA DOĞAPARK FRANCHISE",
    "GJ MALATYA YESILYURT": "MALATYA YESILYURT FRANCHISE",
    "GJ MALL OF ISTANBUL": "MALL OF ISTANBUL FRANCHISE",
    "GJ MALTEPE ALTAY ÇEŞME": "MALTEPE ALTAY ÇEŞME FRANCHİSE",
    "GJ MANISA": "MANİSA FRANCHISE",
    "GJ MARMARA FORUM": "MARMARA FORUM FRANCHİSE",
    "GJ MARMARA FORUM KIOSK": "MARMARA FORUM KİOKS FRANCHİSE",
    "GJ MARMARAPARK": "MARMARAPARK FRANCHİSE",
    "GJ  MARMARA UNIVERSITESI": "MARMARA UNIVERSITESI FRANCHISE",
    "GJ MARMARIS MARINA": "MARMARIS MARINA FRANCHISE",
    "GJ MARMARIS ORKA": "MARMARIS ORKA FRANCHISE",
    "GJ MAVERA COMFORT": "BASAKSEHIR MAVERA FRANCHISE",
    "GJ MERSIN ERDEMLI": "MERSIN ERDEMLI FRANCHISE",
    "GJ MERSIN SAYAPARK AVM": "MERSIN FRANCHISE",
    "GJ MOBIL TRACK": "GJ MAYA MOBIL ARAC",
    "GJ NIDAPARK BASAKSEHIR": "BASAKSEHIR NIDAPARK FRANCHISE",
    "GJ NIGDE": "NİĞDE FRANCHİSE",
    "GJ NISANTASI UNI KAGITHANE": "NISANTASI UNI KAGITHANE FRANCHISE",
    "GJ NISANTASI UNIVERSITESI": "GJ İSTANBUL NISANTASI UNI FRANCHISE",
    "GJ OMUR PLAZA": "BAHÇELİEVLER ÖMÜR PLAZA FRANCHISE",
    "GJ ORDU FATSA": "ORDU FATSA FRANCHİSE",
    "GJ ORDU HILTON": "ORDU HILTON FRANCHISE",
    "GJ ORDU UNYE": "UNYE FRANCHISE",
    "GJ ORHANGAZI": "BURSA ORHANGAZI FRANCHISE",
    "GJ OSMANIYE": "OSMANİYE FRANCHİSE",
    "GJ PELICAN AVM": "PELICAN FRANCHISE",
    "GJ  PIAZZA AVM": "GJ MALTEPE PIAZZA AVM FRANCHISE",
    "GJ RIZE": "RİZE FRANCHISE",
    "GJ RIZE ARDESEN": "RİZE ARDEŞEN FRANCHİSE",
    "GJ RIZE TOKI": "RİZE TOKİ FRANCHİSE",
    "GJ RUMELI HISARI": "RUMELİ HİSARI FRANCHİSE",
    "GJ SAHRAYICEDIT": "GJ SAHRAYICEDIT FRANCHISE",
    "GJ SAKARYA AGORA": "GJ SAKARYA AGORA FRANCHİSE",
    "GJ SAKARYA CADDE 54": "SAKARYA CADDE54 FRANCHİSE",
    "GJ SAKARYA KARASU": "SAKARYA KARASU FRANCHİSE",
    "GJ SANCAKTEPE LAVENDER": "SANCAKTEPE LEVANDER",
    "GJ SANLIURFA KARA KOPRU": "ŞANLIURFA KARAKÖPRÜ FRANCHİSE",
    "GJ SAPANCA KIRKPINAR": "SAPANCA KIRKPINAR FRANCHİSE",
    "GJ SARIYER": "SARIYER MERKEZ FRANCHISE",
    "GJ SEFAKOY": "SEFAKOY FRANCHISE",
    "GJ SEFERIHISAR": "IZMIR SEFERIHISAR FRANCHISE",
    "GJ SILE": "ŞİLE FRANCHİSE",
    "GJ SIRKECI": "SIRKECI FRANCHISE",
    "GJ SISLI OPET": "ŞİŞLİ YÜKSEL OPET FRANCHİSE",
    "GJ SULTANGAZI EVA": "SULTANGAZİ FRANCHISE",
    "GJ TORIUM AVM": "TORİUM FRANCHİSE",
    "GJ TRABZON FORUM": "TRABZON FORUM FRANCHISE",
    "GJ TRABZON MEYDAN": "TRABZON MEYDAN FRANCHİSE",
    "GJ TRABZON OF": "TRABZON OF FRANCHİSE",
    "GJ TRABZON RUBENIS AVM": "TRABZON RUBENİS FRANCHİSE",
    "GJ TUZLAPORT": "TUZLAPORT FRANCHİSE",
    "GJ ÜMRANİYE ÇARŞI": "UMRANIYE CARSI FRANCHİSE",
    "GJ USKUDAR": "USKUDAR CARSI FRANCHISE",
    "GJ USKUDAR TASBAHCE": "USKUDAR TASBAHCE FRANCHISE",
    "GJ VAN": "VAN AVM FRANCHISE",
    "GJ VATAN CADDESI": "VATAN CADDESİ FRANCHİSE",
    "GJ VEGA RAMS": "BAHCELIEVLER VEGA RAMS FRANCHISE",
    "GJ VIALAND - YENI": "ISFANBUL FRANCHISE",
    "GJ WATER GARDEN": "WATER GARDEN FRANCHİSE",
    "GJ YALOVA": "YALOVA MERKEZ FRANCHISE",
    "GJ ZEKERIYAKOY": "ZEKERİYAKÖY FRANCHİSE",
}
```

---

### Step 2: Read Excel 1 (Simphony)
**Node:** `Read Excel`
| Parameter | Value |
|-----------|-------|
| File Path | `{{excel1_path}}` |
| Sheet | `Sheet1` |
| Output Variable | `excel1_data` |

---

### Step 3: Read Excel 2 (MC)
**Node:** `Read Excel`
| Parameter | Value |
|-----------|-------|
| File Path | `{{excel2_path}}` |
| Sheet | `Sheet1` |
| Output Variable | `excel2_data` |

---

### Step 4: Initialize Mismatch List
**Node:** `Set Variable`
| Parameter | Value |
|-----------|-------|
| Variable Name | `mismatches` |
| Value | `[]` |

---

### Step 5: Initialize Unmatched List
**Node:** `Set Variable`
| Parameter | Value |
|-----------|-------|
| Variable Name | `unmatched_names` |
| Value | `[]` |

---

### Step 6: Loop Through Excel 1 Rows
**Node:** `For Each`
| Parameter | Value |
|-----------|-------|
| Collection | `{{excel1_data}}` |
| Item Variable | `row1` |
| Index Variable | `row1_index` |

---

### Step 7: (Inside Loop) Get Name and Price from Excel 1
**Node:** `Set Variable`
| Parameter | Value |
|-----------|-------|
| Variable Name | `simphony_name` |
| Value | `{{row1.D}}` *(Column D = name)* |

**Node:** `Set Variable`
| Parameter | Value |
|-----------|-------|
| Variable Name | `simphony_price` |
| Value | `{{row1.C}}` *(Column C = price)* |

---

### Step 8: (Inside Loop) Map Name
**Node:** `Get Dict Value`
| Parameter | Value |
|-----------|-------|
| Dictionary | `{{name_mapping}}` |
| Key | `{{simphony_name}}` |
| Default | `None` |
| Output Variable | `mapped_name` |

---

### Step 9: (Inside Loop) Check if Mapping Exists
**Node:** `If Condition`
| Parameter | Value |
|-----------|-------|
| Condition | `{{mapped_name}} == None` |

**True Branch:**

**Node:** `Append to List`
| Parameter | Value |
|-----------|-------|
| List | `{{unmatched_names}}` |
| Value | `{"row": {{row1_index + 2}}, "name": "{{simphony_name}}", "issue": "No mapping found"}` |

Then: `Continue` (skip to next iteration)

---

### Step 10: (Inside Loop) Find in Excel 2
**Node:** `Filter List`
| Parameter | Value |
|-----------|-------|
| List | `{{excel2_data}}` |
| Condition | `item.A == "{{mapped_name}}"` |
| Output Variable | `matching_rows` |

---

### Step 11: (Inside Loop) Check if Found in Excel 2
**Node:** `If Condition`
| Parameter | Value |
|-----------|-------|
| Condition | `len({{matching_rows}}) == 0` |

**True Branch:**

**Node:** `Append to List`
| Parameter | Value |
|-----------|-------|
| List | `{{unmatched_names}}` |
| Value | `{"row": {{row1_index + 2}}, "name": "{{simphony_name}}", "mapped": "{{mapped_name}}", "issue": "Not found in Excel 2"}` |

Then: `Continue`

---

### Step 12: (Inside Loop) Compare Prices
**Node:** `Get List Item`
| Parameter | Value |
|-----------|-------|
| List | `{{matching_rows}}` |
| Index | `0` |
| Output Variable | `match_row` |

**Node:** `Set Variable`
| Parameter | Value |
|-----------|-------|
| Variable Name | `mc_price` |
| Value | `{{match_row.B}}` *(Column B = price)* |

**Node:** `If Condition`
| Parameter | Value |
|-----------|-------|
| Condition | `{{simphony_price}} != {{mc_price}}` |

**True Branch:**

**Node:** `Append to List`
| Parameter | Value |
|-----------|-------|
| List | `{{mismatches}}` |
| Value | See below |

```json
{
  "excel1_row": {{row1_index + 2}},
  "excel1_col": "C",
  "name_excel1": "{{simphony_name}}",
  "name_excel2": "{{mapped_name}}",
  "price_excel1": {{simphony_price}},
  "price_excel2": {{mc_price}},
  "difference": {{simphony_price - mc_price}}
}
```

---

### Step 13: End Loop
**Node:** `End For Each`

---

### Step 14: Output Results
**Node:** `Set Variable`
| Parameter | Value |
|-----------|-------|
| Variable Name | `result` |
| Value | See below |

```json
{
  "total_mismatches": {{len(mismatches)}},
  "total_unmatched": {{len(unmatched_names)}},
  "mismatches": {{mismatches}},
  "unmatched_names": {{unmatched_names}}
}
```

---

### Step 15: (Optional) Write Results to Excel
**Node:** `Write Excel`
| Parameter | Value |
|-----------|-------|
| File Path | `{{output_path}}` |
| Sheet | `Mismatches` |
| Data | `{{mismatches}}` |

---

## Visual Flow Diagram

```
┌─────────────────────┐
│ Set Variable        │
│ (name_mapping)      │
└──────────┬──────────┘
           │
     ┌─────┴─────┐
     │           │
┌────▼────┐ ┌────▼────┐
│Read     │ │Read     │
│Excel 1  │ │Excel 2  │
└────┬────┘ └────┬────┘
     │           │
     └─────┬─────┘
           │
┌──────────▼──────────┐
│ Set Variable        │
│ (mismatches = [])   │
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│ For Each (excel1)   │◄────────────────┐
└──────────┬──────────┘                 │
           │                            │
┌──────────▼──────────┐                 │
│ Get Dict Value      │                 │
│ (map name)          │                 │
└──────────┬──────────┘                 │
           │                            │
┌──────────▼──────────┐                 │
│ If (mapping exists?)│                 │
└───┬─────────────┬───┘                 │
   No            Yes                    │
    │             │                     │
┌───▼───┐   ┌─────▼─────┐               │
│Append │   │Filter List│               │
│unmatch│   │(find in 2)│               │
└───┬───┘   └─────┬─────┘               │
    │             │                     │
    │       ┌─────▼─────┐               │
    │       │If (found?)│               │
    │       └──┬─────┬──┘               │
    │         No    Yes                 │
    │          │     │                  │
    │     ┌────▼──┐ ┌▼────────┐         │
    │     │Append │ │If prices│         │
    │     │unmatch│ │ match?  │         │
    │     └───┬───┘ └─┬─────┬─┘         │
    │         │      No    Yes          │
    │         │       │     │           │
    │         │  ┌────▼───┐ │           │
    │         │  │Append  │ │           │
    │         │  │mismatch│ │           │
    │         │  └────┬───┘ │           │
    │         │       │     │           │
    └─────────┴───────┴─────┴───────────┘
                      │
           ┌──────────▼──────────┐
           │ Write Excel         │
           │ (results)           │
           └─────────────────────┘
```

---

## Expected Output Example

```
Total rows compared: 180
Price mismatches: 5
Unmatched names: 2

--- PRICE MISMATCHES ---
Row 15 (GJ ANKARA CEPA): Excel1=150.00, Excel2=145.00, Diff=5.00
Row 42 (GJ BURSA EKER): Excel1=200.00, Excel2=195.50, Diff=4.50

--- UNMATCHED NAMES ---
Row 88: GJ NEW STORE - No mapping found
```

---

## Notes

- Column indices are 0-based in code but displayed as letters (A, B, C, D) for clarity
- Row numbers include +2 offset (1 for header, 1 for 0-index conversion)
- The `Filter List` node searches Excel 2 for each mapped name
- Results can be written to a new Excel file or displayed in a message box
