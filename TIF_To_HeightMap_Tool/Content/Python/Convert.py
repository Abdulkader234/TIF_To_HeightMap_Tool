import os                     # Hanterar filer och mappar på disk
from PIL import Image         # Läser och skriver bilder (stödjer 16-bit PNG)
import numpy as np            # Snabb array-matematik för höjddata
import unreal                 # Åtkomst till Unreal Editor API
import tkinter as tk          # Enkelt filvalsfönster
from tkinter import filedialog


def select_tif():
    """
    Öppnar ett filvalsfönster så användaren kan välja en GeoTIFF-fil.
    Returnerar den valda filsökvägen som en sträng.
    Returnerar en tom sträng om användaren avbryter.
    """
    root = tk.Tk()
    root.withdraw()  # Döljer huvudfönstret, vi vill bara visa filvalsdialogen

    path = filedialog.askopenfilename(
        title="Välj GeoTIFF",
        filetypes=[("TIF-filer", "*.tif *.tiff")]
    )

    root.destroy()  # Städar upp tkinter efter att dialogen stängts
    return path


def convert_and_import(tif_path):
    """
    Läser en GeoTIFF heightmap,
    konverterar den till 16-bit PNG,
    importerar den till Unreal,
    och returnerar metadata som ett dictionary.
    """

    # Resultat-dictionary
    # Alltid initialiserad med SÄKRA standardvärden
    # Varje nyckel här blir en pin i Execute Python Script-noden i Unreal
    
    result = {
        "conversion_success": False,  # True när PNG har sparats korrekt
        "import_success": False,      # True när asseten finns i Unreal-projektet
        "file_already_exists": False, # True om asseten redan importerats tidigare
        "no_file_selected": False,    # True om användaren stängde filvalsdialogen
        "file_not_found": False,      # True om den valda filsökvägen inte finns på disk
        "not_single_band": False,     # True om TIF har flera kanaler (t.ex. RGB)
        "no_valid_data": False,       # True om alla pixlar är NoData (-9999)
        "flat_heightmap": False,      # True om alla höjdvärden är identiska (range = 0)
        "error_message": "",          # Läsbart felmeddelande som visas i widgeten
        "asset_path": "",             # Unreal asset-sökväg t.ex. /Game/ImportedHeightmaps/fil_height
        "min_height": 0.0,            # Lägsta verkliga höjdvärde i meter
        "max_height": 0.0,            # Högsta verkliga höjdvärde i meter
        "height_range": 0.0,          # Skillnad mellan max och min höjd i meter
        "width": 0,                   # Texturbredd i pixlar
        "height": 0                   # Texturhöjd i pixlar
    }

    # Validering: Ingen fil vald
    # Detta händer när användaren stänger filvalsdialogen utan att välja en fil
    # filedialog.askopenfilename() returnerar en tom sträng i det fallet
    
    if not tif_path:
        result["no_file_selected"] = True
        result["error_message"] = "No file selected"
        return result

    
    # Validering: Filen finns inte på disk
    # Sökvägen kan vara ogiltig eller filen kan ha flyttats/raderats
   
    if not os.path.exists(tif_path):
        result["file_not_found"] = True
        result["error_message"] = "File does not exist"
        return result

    # Ladda TIF-bild
    # PIL öppnar filen och numpy konverterar den till en 2D-array av höjdvärden
    # Insvept i try/except för att fånga korrupta eller ostödda TIF-format
    
    try:
        img = Image.open(tif_path)
        data = np.array(img)
    except Exception as e:
        result["error_message"] = "Failed to open TIF: " + str(e)
        return result

    """
    Validering: Single band (gråskala)
    En heightmap måste ha exakt ETT värde per pixel som representerar höjd
    RGB-bilder har formen (höjd, bredd, 3) — len = 3, inte giltig
    Gråskalebilder har formen (höjd, bredd) — len = 2, korrekt
    
    Exempel:
    RGB-bild:    data.shape = (1024, 1024, 3) → len = 3 → OGILTIG
    Heightmap:   data.shape = (1024, 1024)    → len = 2 → GILTIG
    """
    
    if len(data.shape) != 2:
        result["not_single_band"] = True
        result["error_message"] = "TIF is not single band"
        return result

    # Spara bildupplösning i pixlar
    result["width"] = data.shape[1]   # Antal kolumner = bredd
    result["height"] = data.shape[0]  # Antal rader = höjd

    """
    Hantera NoData-värden
    GeoTIFF-filer från satelliter eller flygmätningar använder -9999 för att
    markera pixlar där ingen mätdata finns, t.ex. över hav eller moln
    
    Varför -9999?
    Verkliga höjder på jorden ligger mellan ca -430m (Döda havet) och
    +8849m (Everest) — därför är -9999 ett omöjligt verkligt höjdvärde
    och används som en "flagga" för saknad data
    
    Om vi INTE filtrerar bort -9999 skulle normaliseringen bli fel:
    Utan filtrering: min_h = -9999  → fel heightmap
    Med filtrering:  min_h = -430   → korrekt heightmap
    """
    
    nodata_mask = data <= -9999   # Skapar en mask för alla ogiltiga pixlar
    valid_data = data[~nodata_mask]  # Behåller bara pixlar med giltig höjddata

    
    # Validering: Ingen giltig data
    # Om ALLA pixlar är NoData finns det ingen höjddata att konvertera

    if valid_data.size == 0:
        result["no_valid_data"] = True
        result["error_message"] = "No valid height data found"
        return result

    
    # Beräkna min, max och range
    # Dessa värden behövs för att:
    # 1. Normalisera heightmappen till 0-1
    # 2. Beräkna rätt Z-skala i Unreal så landskapet får korrekta proportioner
   
    min_h = float(valid_data.min())
    max_h = float(valid_data.max())
    height_range = max_h - min_h

    # Validering: Platt heightmap
    # Om alla höjdvärden är identiska är range = 0
    # Division med 0 vid normalisering skulle krascha skriptet
   
    if height_range == 0:
        result["flat_heightmap"] = True
        result["error_message"] = "Height range is zero"
        return result

    # Spara höjdinformation för Blueprint att använda
    result["min_height"] = min_h
    result["max_height"] = max_h
    result["height_range"] = height_range

    
    # Normalisera höjddata till 0-1
    # Varje pixelvärde omvandlas till ett tal mellan 0.0 och 1.0
    # där 0.0 = lägsta höjden och 1.0 = högsta höjden

    normalized = (data - min_h) / height_range

    # Sätt NoData-pixlar till 0 (lägsta höjd) efter normalisering
    normalized[nodata_mask] = 0

    # Konvertera till 16-bit heltal (0-65535)
    # Unreal kräver 16-bit PNG för heightmaps
    # 16-bit ger 65536 möjliga höjdnivåer vilket ger tillräcklig precision
    # 8-bit skulle bara ge 256 nivåer vilket skapar synliga trappsteg i terrängen

    heightmap_16 = (normalized * 65535).astype(np.uint16)

    # Skapa fysisk mapp i projektets Content-mapp
    # Alla importerade heightmaps sparas i en dedikerad mapp
    # för att hålla projektstrukturen organiserad

    project_content_dir = unreal.Paths.project_content_dir()
    output_folder = os.path.join(project_content_dir, "ImportedHeightmaps")

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)  # Skapar mappen om den inte finns

    # Bygg filnamn baserat på originalfilens namn
    base_name = os.path.splitext(os.path.basename(tif_path))[0]
    output_name = base_name + "_height.png"
    output_path = os.path.join(output_folder, output_name)

    # Spara 16-bit PNG
    # mode="I;16" anger att bilden ska sparas som 16-bit gråskala
    try:
        out_img = Image.fromarray(heightmap_16, mode="I;16")
        out_img.save(output_path)
    except Exception as e:
        result["error_message"] = "Failed to save PNG: " + str(e)
        return result

    result["conversion_success"] = True  # PNG sparad korrekt

    # Säkerställ att Unreal Content-mappen finns
    # /Game/ motsvarar projektets Content-mapp i Unreal
    unreal_folder = "/Game/ImportedHeightmaps"

    if not unreal.EditorAssetLibrary.does_directory_exist(unreal_folder):
        unreal.EditorAssetLibrary.make_directory(unreal_folder)

    asset_name = base_name + "_height"
    unreal_asset_path = unreal_folder + "/" + asset_name

   
    # Kontrollera om asseten redan finns i Unreal
    # Om den finns returnerar vi direkt utan att importera igen
    # Detta förhindrar dubbelimport och ger användaren rätt feedback
    if unreal.EditorAssetLibrary.does_asset_exist(unreal_asset_path):
        result["file_already_exists"] = True
        result["import_success"] = True
        result["asset_path"] = unreal_asset_path
        result["error_message"] = "File already exists: " + unreal_asset_path
        return result


    # Importera PNG till Unreal
    # AssetImportTask definierar hur filen ska importeras
    # automated = True kör importen utan popups eller bekräftelsedialoger
    # replace_existing = False förhindrar att befintliga assets skrivs över
    # save = True sparar asseten direkt efter import
    task = unreal.AssetImportTask()
    task.filename = output_path          # Sökväg till PNG-filen på disk
    task.destination_path = unreal_folder  # Var i Unreal projektet den ska hamna
    task.destination_name = asset_name   # Vad asseten ska heta i Unreal
    task.automated = True
    task.replace_existing = False
    task.save = True

    try:
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    except Exception as e:
        result["error_message"] = "Unreal import exception: " + str(e)
        return result

    
    # Verifiera att importen lyckades
    # Vi kontrollerar att asseten faktiskt finns efter importen
    # Om den saknas misslyckades importen av okänd anledning
    if unreal.EditorAssetLibrary.does_asset_exist(unreal_asset_path):
        result["import_success"] = True
        result["asset_path"] = unreal_asset_path
    else:
        result["error_message"] = "Import failed — check Unreal Output Log"

    return result


def run():
    """
    Huvudfunktion som anropas från Unreal Blueprint.

    1. Öppnar filvalsdialog
    2. Konverterar TIF till 16-bit PNG
    3. Importerar till Unreal
    4. Returnerar dictionary med ALL metadata som Blueprint behöver
    """
    tif_path = select_tif()
    result = convert_and_import(tif_path)
    return result