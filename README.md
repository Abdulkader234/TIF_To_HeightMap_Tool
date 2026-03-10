# GEO data to HeightMap converter for UE5 – Unreal Engine Plugin Documentation

## 1. Overview
The Heightmap Import Tool plugin allows users to import GeoTIFF heightmap files directly into Unreal Engine as 16-bit PNG texture assets. The plugin is designed for quick heightmap management and landscape setup.

- **Plugin Name:** TIF_To_HeightMap_Tool
- **Current Version:** 1.0.0
- **Supported Unreal Engine Versions:** 5.6+
- **Platforms:** Windows
- **Intended Audience:** Artists, Technical Artists

---

## 2. Features
- Import .tif / .tiff GeoTIFF heightmaps directly into Unreal Engine
- Automatic conversion to 16-bit PNG (required by Unreal Landscape)
- Extracts real world min/max height values for correct Z scale calculation
- Displays recommended XY and Z scale for Landscape Mode
- Handles NoData values (-9999) found in GIS/satellite data
- Validates single-band (grayscale) format before import
- Prevents duplicate imports with file-already-exists detection
- User feedback via in-editor notifications for all error states

---

## 3. Installation

### 3.1 Requirements
- Unreal Engine 5.2 or newer
- Windows 10 or later

### 3.2 Installation Steps
1. Copy the `TIF_To_HeightMap_Tool` folder into: /ProjectFolder/Plugins
2. Launch Unreal Engine.
3. Open **Edit → Plugins**.
4. Enable **Simple OBJ Importer**.
5. Restart Unreal Engine.

---

## 4. Getting Started

### 4.1 Enabling the Plugin
After restarting Unreal Engine, verify the plugin is enabled by checking:
**Edit → Plugins → Importers → TIF_To_HeightMap_Tool**

### 4.2 Basic Workflow
1. Open the plugin via Window → TIF_To_HeightMap_Tool
2. Click Browse to select a .tif heightmap file from disk
3. The plugin automatically converts and imports the file
4. Review the texture metadata and scale values
5. Enter your Landscape Overall Resolution
6. Manually apply the recommended XY and Z scale values in Landscape Mode

---

## 5. User Interface

### Import Section
| UI Element | Description |
|---|---|
| **Browse Button** | Opens a file picker to select a `.TIF` file from disk |
| **Landscape Overall Resolution** | Target resolution for your Unreal Landscape. Recalculates recommended scales |

### Texture Information Section

| Field | Example | Description |
|---|---|---|
| **Texture Resolution** | 2500 x 2500 | Width × Height of the imported texture in pixels |
| **Imported Min Height** | 606.77 | Lowest elevation value in meters |
| **Imported Max Height** | 884.5 | Highest elevation value in meters |
| **HeightRange** | 277.73 | Max - Min height. Used to compute Z scale |
| **Texture Path** | /Game/ImportedHeightmaps/Tif_height | Content browser path of the saved asset |
| **Height Image** | (thumbnail) | Visual preview of the converted texture |

### Landscape Settings Section

| Field | Example | Description |
|---|---|---|
| **Recommended XY Scale** | 98.386 / 98.386 | Horizontal scale per axis for the Landscape Actor |
| **Recommended Z Scale** | 54.244 | Vertical scale so height range maps correctly in Unreal |

---

## 6. Usage Guide

### Importing a Heightmap

1. Click **Browse** and select a valid `.tif` or `.tiff` file
2. Plugin automatically converts the file to 16-bit PNG
3. Asset is saved to `/Game/ImportedHeightmaps/`
4. Review the displayed metadata
5. Enter your target **Landscape Overall Resolution**
6. Apply the recommended scale values to your Landscape Actor

---

## 7. Data Handling & Output

| | |
|---|---|
| **Input Format** | GeoTIFF `.tif` / `.tiff`, single-band grayscale |
| **Output Format** | 16-bit PNG |
| **Naming Convention** | `<OriginalFileName>_height` |
| **Destination (disk)** | `[ProjectContent]/ImportedHeightmaps/` |
| **Destination (Unreal)** | `/Game/ImportedHeightmaps/` |
| **NoData Handling** | Pixels `<= -9999` are set to `0` |

---

## 8. Limitations
- Only single-band (grayscale) GeoTIFF files are supported
- RGB or multi-band TIF files are rejected with an error message
- Very large TIF files (4K+) may use significant RAM during conversion
- Scale values must be applied manually in Landscape Mode
- NoData value is hardcoded to `-9999` (standard GIS convention)
---

## 9. Troubleshooting

| Issue | Cause | Solution |
|---|---|---|
| Texture fields empty after browse | Invalid or multi-band TIF | Use a single-band grayscale `.tif` file |
| Landscape too flat or exaggerated | Wrong Z Scale or resolution mismatch | Match Landscape Resolution and re-apply Z Scale |
| Asset not found in Content Browser | Write permission or unsaved project | Save project and refresh Content Browser |
| "No file was selected" | File dialog closed without selecting | Click Browse and select a `.tif` file |
| "TIF is not single band" | RGB or multi-band file | Re-export as single-band grayscale |
| "File already exists" | Asset already imported | Use existing asset or delete it first |
| "Import failed" | Unknown Unreal error | Check **Window → Output Log** for details |
| XY or Z Scale shows 0 | Resolution = 0 or flat terrain | Set a valid resolution and check height range |

---

## 10. Version History

| Version | Date | Notes |
|-------|------|-------|
| 1.0.0 | 2026-03-09 | Initial release |

---

## 11. Support & Contact

- Contact: abdalkaderalkhayat@gmail.com
